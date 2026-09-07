"""AI Study Assistant — RAG over APPROVED content only.

Ground rules:
- The assistant is a STUDY TOOL, not a doctor. It never fabricates authority.
- Only resources with ``ai_usage_status == 'true'`` and a non-blocked rights
  status are eligible for retrieval/ingestion.
- ``ai_usage_status == 'unknown'`` ⇒ DO NOT ingest. ``review_required``/``blocked``
  ⇒ never used as trusted knowledge.
- Returns an answer plus **citations** to the retrieved sources (spec §27).

Retrieval is provider-agnostic:
- If pgvector is available and embeddings are provided, use vector similarity.
- Otherwise fall back to token/keyword overlap over approved content, so the
  feature works in local/dev (SQLite) and CI, and upgrades cleanly.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


@dataclass
class SourceChunk:
    source_type: str  # topic / structure / resource
    source_id: int | None
    title: str
    text: str
    href: str | None = None
    weight: int = 0  # relevance/candidate weight for ranking


# Stopwords to compute simple keyword overlap on the fallback path.
_STOP = set(
    "what is the a an of to in for on with how why does do are was were "
    "explain describe give list name define its it their my your meaning".split()
)


def _tokens(text: str) -> set[str]:
    words = re.findall(r"[a-z0-9][a-z0-9\-']*", text.lower())
    return {w for w in words if w not in _STOP and len(w) > 2}


def _score(query_tokens: set[str], text: str) -> int:
    """Keyword-overlap score used when vector search is unavailable."""
    if not text:
        return 0
    text_tokens = _tokens(text)
    return len(query_tokens & text_tokens)


def is_ingestable(ai_usage_status: str | None) -> bool:
    """True only for content explicitly allowed for AI ingestion."""
    return (ai_usage_status or "").strip().lower() == "true"


async def retrieve(session: AsyncSession, query: str, limit: int = 5) -> list[SourceChunk]:
    """Retrieve approved study context for `query`.

    Only content whose resource is AI-allowed (ai_usage_status='true') and whose
    rights are not review_required/blocked is eligible.
    """
    from app.models.atlas import AnatomicalStructure
    from app.models.content import Resource
    from app.models.subject import Topic, TopicBlock

    qt = _tokens(query)

    # 1) Approved topic blocks (from topics that are published).
    #    Rank topics by title+summary match first, then within a topic prefer
    #    explanatory content blocks (overview/clinical/diagram) over practice
    #    prompts (mcq/viva/flashcards). One topic contributes at most two chunks
    #    so the answer stays focused rather than echoing a quiz.
    EXPLANATORY = {"overview", "clinical", "diagram", "revision", "practical", "books", "objectives"}
    blocks: list[SourceChunk] = []
    topic_rows = await session.execute(select(Topic).where(Topic.is_published.is_(True)).limit(50))
    for topic in topic_rows.scalars().all():
        topic_signal = _score(qt, f"{topic.title} {topic.summary or ''}")
        block_rows = (await session.execute(
            select(TopicBlock).where(TopicBlock.topic_id == topic.id, TopicBlock.is_enabled.is_(True))
        )).scalars().all()

        # Topic-level content_markdown is a strong, self-contained answer source.
        if topic.content_markdown and _score(qt, topic.content_markdown) > 0:
            blocks.append(
                SourceChunk(
                    source_type="topic",
                    source_id=topic.id,
                    title=f"{topic.title} — Overview",
                    text=topic.content_markdown,
                    href=f"/learn/{topic.subject_id}/{topic.slug}",
                    weight=topic_signal + _score(qt, topic.content_markdown),
                )
            )

        if not block_rows:
            continue
        candidates: list[SourceChunk] = []
        for b in block_rows:
            text = (b.content or "")
            score = _score(qt, text)
            if score <= 0 and topic_signal <= 0:
                # The block still belongs to a strongly matching topic: keep weak hits
                # so the topic is represented even if wording differs.
                if topic_signal <= 0:
                    continue
            weight = topic_signal + score
            if b.block_type not in EXPLANATORY:
                weight *= 0.4
            candidates.append(SourceChunk(
                source_type="topic",
                source_id=topic.id,
                title=f"{topic.title} — {b.title}",
                text=text,
                href=f"/learn/{topic.subject_id}/{topic.slug}",
                weight=weight,
            ))
        # Keep the best chunk from this topic (its strongest explanatory block).
        if candidates:
            candidates.sort(key=lambda c: c.weight, reverse=True)
            blocks.extend(candidates[:2])

    # 2) Atlas structures (platform anatomy content).
    struct_chunks: list[SourceChunk] = []
    struct_rows = await session.execute(select(AnatomicalStructure).where(AnatomicalStructure.status == "verified").limit(100))
    for s in struct_rows.scalars().all():
        text = " ".join(x for x in [s.description, s.clinical_notes] if x)
        score = _score(qt, f"{s.preferred_name} {s.synonyms or ''} {text}")
        if score > 0:
            struct_chunks.append(
                SourceChunk(
                    source_type="structure",
                    source_id=s.id,
                    title=s.preferred_name,
                    text=text,
                    href=f"/atlas?structure={s.preferred_name.replace(' ', '-')}",
                    weight=score,
                )
            )

    # 3) Approved external resources (only AI-allowed, non-blocked rights).
    resource_chunks: list[SourceChunk] = []
    resource_rows = await session.execute(
        select(Resource).where(
            Resource.ai_usage_status == "true",
            Resource.rights_status.notin_(["review_required", "blocked", "external_only"]),
            Resource.visibility == "public",
        ).limit(50)
    )
    for r in resource_rows.scalars().all():
        score = _score(qt, r.title)
        if score > 0:
            resource_chunks.append(
                SourceChunk(
                    source_type="resource",
                    source_id=r.id,
                    title=r.title,
                    text=f"{r.title}: {r.attribution_text or ''}",
                    href="/library",
                    weight=score,
                )
            )

    combined = sorted(
        blocks + struct_chunks + resource_chunks,
        key=lambda c: c.weight,
        reverse=True,
    )
    return combined[:limit]


async def retrieve_vector(session: AsyncSession, query: str, limit: int = 5) -> list[SourceChunk]:
    """Vector retrieval over indexed, AI-approved content chunks.

    Uses the stored embeddings (``content_embeddings``). Only chunks that were
    indexed (i.e. already passed the AI-eligibility + rights gates) are queried,
    so the answer can never pull from unapproved content. If no embeddings are
    indexed yet, returns [] (the caller falls back to keyword retrieval).
    """
    from app.core.embeddings import cosine, decode_vector, embed
    from app.models.embedding import ContentEmbedding

    rows = (
        await session.execute(select(ContentEmbedding).limit(2000))
    ).scalars().all()
    if not rows:
        return []

    qv = embed(query)
    scored: list[tuple[float, ContentEmbedding]] = []
    for r in rows:
        rv = decode_vector(r.vector_json)
        if not rv:
            continue
        scored.append((cosine(qv, rv), r))

    scored.sort(key=lambda t: t[0], reverse=True)

    results: list[SourceChunk] = []
    for score, r in scored[:limit]:
        if score <= 0.02:
            continue
        results.append(
            SourceChunk(
                source_type=r.source_type,
                source_id=r.source_id,
                title=r.title or "",
                text=r.text,
                href=r.href,
                weight=int(score * 1000),
            )
        )
    return results


def build_answer(query: str, sources: list[SourceChunk]) -> dict[str, Any]:
    """Produce a study answer with citations from retrieved sources.

    No external LLM is invoked here (no API key in dev/CI). This deterministic
    retrieval-grounded builder keeps the assistant factual and cited, and the
    answer-generation call can be swapped for an LLM later behind the same
    input/output contract.
    """
    citations = [
        {
            "source_type": s.source_type,
            "source_id": s.source_id,
            "title": s.title,
            "href": s.href,
        }
        for s in sources
    ]

    if not sources:
        return {
            "answer": (
                "I could not find approved MEDFREE content on that topic. "
                "This is a study assistant using only verified, AI-eligible platform content."
            ),
            "sources": [],
            "disclaimer": "Educational study tool, not medical advice.",
        }

    # Build a concise answer from the top-ranked chunks, deduplicating identical
    # text and skipping bare quiz prompts so the answer reads like an
    # explanation rather than a test.
    seen_text: set[str] = set()
    picked: list[str] = []
    # Skip only true quiz/interactive placeholders. Learning objectives and
    # explanatory blocks are useful and should be surfaced.
    GENERIC_PROMPTS = (
        "attempt questions", "practice oral", "active-recall flashcards",
        "spaced-repetition cards", "explore this structure",
        "interactive schematic", "toggle each level", "attempt questions on",
    )
    QUIZ_PROMPTS = ("which of the", "select ", "answer the following", "choose the")
    OBJECTIVE_SYNTAX = ("- name", "- describe", "- relate", "- identify", "- explain",
                        "learning objectives", "by the end of", "you will be able to")
    for s in sources:
        text = (s.text or "").strip()
        low = text.lower()
        if any(low.startswith(p) for p in GENERIC_PROMPTS):
            continue
        if s.source_type == "topic" and low.startswith(QUIZ_PROMPTS):
            continue
        # Drop objective/blurb lines that are not factual answer content.
        for line in text.split("\n"):
            l = line.strip().lower()
            if l and l.startswith(OBJECTIVE_SYNTAX):
                text = ""
                break
        if not text:
            continue
        if len(picked) >= 3:
            break
        if len(text) <= 15:
            continue
        norm = " ".join(low.split())
        if norm in seen_text:
            continue
        seen_text.add(norm)
        picked.append(text)

    body = "\n\n".join(f"• {p}" for p in picked) if picked else "No explanation available for this query."

    answer = (
        f"Here's what MEDFREE's approved study material explains about "
        f"\"{query}\":\n\n{body}\n\n"
        "The sources below are cited for verification. This is a study assistant; "
        "always confirm against a reviewed textbook or your faculty."
    )
    return {
        "answer": answer,
        "sources": citations,
        "disclaimer": "Educational study tool, not medical advice.",
    }
