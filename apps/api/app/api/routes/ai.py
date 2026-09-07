"""AI Study Assistant — RAG over approved content, with citations."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin
from app.core.ai import build_answer, is_ingestable, retrieve, retrieve_vector
from app.core.security import record_audit
from app.db.session import get_session

router = APIRouter(prefix="/ai", tags=["ai"])


class AskRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=500)


class Citation(BaseModel):
    source_type: str
    source_id: int | None = None
    title: str
    href: str | None = None


class AskResponse(BaseModel):
    answer: str
    sources: list[Citation]
    disclaimer: str


@router.get("/ingestion-policy")
async def ingestion_policy():
    """Explain which content is AI-eligible (transparency)."""
    return {
        "rule": "Only resources with ai_usage_status='true' and non-blocked rights are ingested.",
        "unknown_is_excluded": True,
        "review_required_is_excluded": True,
        "purpose": "Study assistant only; never a diagnostic tool.",
    }


@router.post("/ask", response_model=AskResponse)
async def ask(payload: AskRequest, session: AsyncSession = Depends(get_session)):
    # Merge keyword retrieval (well-tuned, topic-title ranked) with vector recall
    # (covers paraphrase). Both paths only ever touch AI-eligible, non-blocked
    # content (never unknown / review_required). Keyword results lead; vector
    # results supplement without duplicating.
    kw = await retrieve(session, payload.question)
    vec = await retrieve_vector(session, payload.question)
    seen = {(s.source_type, s.source_id, " ".join(s.text.lower().split())) for s in kw}
    merged = list(kw)
    for s in vec:
        key = (s.source_type, s.source_id, " ".join(s.text.lower().split()))
        if key not in seen:
            merged.append(s)
            seen.add(key)
    if not merged:
        merged = kw or vec
    result = build_answer(payload.question, merged[:6])
    return AskResponse(
        answer=result["answer"],
        sources=[Citation(**c) for c in result["sources"]],
        disclaimer=result["disclaimer"],
    )


class IndexRequest(BaseModel):
    source_type: str = Field(..., pattern=r"^(topic|structure|resource)$")


@router.post("/index", dependencies=[Depends(require_admin)])
async def index_content(
    payload: IndexRequest,
    session: AsyncSession = Depends(get_session),
):
    """(Re)build embeddings for AI-eligible content of a source type.

    Only content that passes ``is_ingestable`` / rights gates is indexed —
    never ``unknown`` or ``review_required``. Idempotent by source key.
    """
    from app.core.embeddings import encode_vector, embed
    from app.models.atlas import AnatomicalStructure
    from app.models.content import Resource
    from app.models.embedding import ContentEmbedding
    from app.models.subject import Topic, TopicBlock

    indexed = 0
    skipped = []

    if payload.source_type in ("topic",):
        topic_rows = await session.execute(select(Topic).where(Topic.is_published.is_(True)))
        for topic in topic_rows.scalars().all():
            block_rows = await session.execute(
                select(TopicBlock).where(TopicBlock.topic_id == topic.id, TopicBlock.is_enabled.is_(True))
            )
            for b in block_rows.scalars().all():
                text = (b.content or b.title or "")
                key = f"topic:{topic.id}:block:{b.id}"
                existing = (
                    await session.execute(select(ContentEmbedding).where(ContentEmbedding.source_key == key))
                ).scalar_one_or_none()
                if existing:
                    continue
                session.add(ContentEmbedding(
                    source_type="topic", source_id=topic.id, source_key=key,
                    title=b.title, text=text,
                    href=f"/learn/{topic.subject_id}/{topic.slug}",
                    vector_json=encode_vector(embed(text)),
                ))
                indexed += 1

    if payload.source_type == "structure":
        rows = await session.execute(select(AnatomicalStructure).where(AnatomicalStructure.status == "verified"))
        for s in rows.scalars().all():
            text = " ".join(x for x in [s.preferred_name, s.description, s.clinical_notes, s.synonyms] if x)
            key = f"structure:{s.id}"
            existing = (
                await session.execute(select(ContentEmbedding).where(ContentEmbedding.source_key == key))
            ).scalar_one_or_none()
            if existing:
                continue
            session.add(ContentEmbedding(
                source_type="structure", source_id=s.id, source_key=key,
                title=s.preferred_name, text=text,
                href=f"/atlas?structure={s.preferred_name.replace(' ', '-')}",
                vector_json=encode_vector(embed(text)),
            ))
            indexed += 1

    if payload.source_type == "resource":
        # Inspect ALL published public resources so we can transparently report
        # the ones we deliberately skip (unknown / non-ingestable) rather than
        # silently ignoring them. Only ingestable ones get embeddings.
        rows = await session.execute(
            select(Resource).where(
                Resource.visibility == "public",
                Resource.review_status == "published",
            )
        )
        for r in rows.scalars().all():
            if not is_ingestable(r.ai_usage_status):
                skipped.append(r.title)
                continue
            text = f"{r.title}: {r.attribution_text or r.source_url or ''}"
            key = f"resource:{r.id}"
            existing = (
                await session.execute(select(ContentEmbedding).where(ContentEmbedding.source_key == key))
            ).scalar_one_or_none()
            if existing:
                continue
            session.add(ContentEmbedding(
                source_type="resource", source_id=r.id, source_key=key,
                title=r.title, text=text, href="/library",
                vector_json=encode_vector(embed(text)),
            ))
            indexed += 1

    await record_audit(session, action="ai.index", target_type="content_type", target_id=None,
                       detail=f"source_type={payload.source_type} indexed={indexed}")
    await session.commit()
    return {"ok": True, "indexed": indexed, "skipped": skipped}
