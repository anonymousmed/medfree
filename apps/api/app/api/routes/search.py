"""Global search across structures, topics, books, resources, questions, viva.

Answers the spec's core question: "Where can I learn this?" — returning a
typed list with deep links (structure → Atlas, topic → Learn, book → Library, ...).
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import rate_limit
from app.db.session import get_session
from app.models.atlas import AnatomicalStructure
from app.models.content import Book, Resource
from app.models.practice import Question, VivaQuestion
from app.models.subject import Subject, Topic
from app.schemas.library import SearchResult

router = APIRouter(prefix="/search", tags=["search"])


@router.get(
    "",
    response_model=list[SearchResult],
    dependencies=[Depends(rate_limit("search", settings.rate_limit_search, settings.rate_limit_window))],
)
async def global_search(
    q: str = Query(..., min_length=2, max_length=120),
    session: AsyncSession = Depends(get_session),
):
    if not q:
        return []
    needle = f"%{q.strip().lower()}%"
    results: list[SearchResult] = []
    # Postgres is strict about boolean == integer; bind a real boolean so the
    # query works on both Postgres and SQLite (which coerces 1<->true).
    published = True

    # 1. Atlas structures (centerpiece comes first)
    structs = (
        await session.execute(
            text(
                "SELECT id, preferred_name, latin_name FROM anatomical_structures "
                "WHERE lower(preferred_name) LIKE :n OR lower(COALESCE(synonyms,'')) LIKE :n "
                "ORDER BY preferred_name LIMIT 8"
            ),
            {"n": needle},
        )
    ).all()
    for s in structs:
        results.append(
            SearchResult(
                type="structure",
                id=s.id,
                title=s.preferred_name,
                subtitle="Atlas · 3D anatomy",
                href=f"/atlas?structure={s.preferred_name.replace(' ', '-')}",
            )
        )

    # 2. Topics
    topics = (
        await session.execute(
            text(
                "SELECT t.id, t.slug, t.title, s.slug AS subject_slug FROM topics t "
                "JOIN subjects s ON s.id = t.subject_id "
                "WHERE lower(t.title) LIKE :n AND t.is_published = :pub ORDER BY t.title LIMIT 6"
            ),
            {"n": needle, "pub": published},
        )
    ).all()
    for t in topics:
        results.append(
            SearchResult(
                type="topic",
                id=t.id,
                title=t.title,
                subtitle="Learn · topic",
                href=f"/learn/{t.subject_slug}/{t.slug}",
            )
        )

    # 3. Books (knowledge/reference layer)
    books = (
        await session.execute(
            text("SELECT id, title FROM books WHERE lower(title) LIKE :n ORDER BY title LIMIT 5"),
            {"n": needle},
        )
    ).all()
    for b in books:
        results.append(
            SearchResult(
                type="book", id=b.id, title=b.title, subtitle="Library · book", href=f"/library/{b.id}"
            )
        )

    # 4. Published public resources
    resources = (
        await session.execute(
            text(
                "SELECT id, title, resource_type FROM resources "
                "WHERE lower(title) LIKE :n AND review_status='published' AND visibility='public' "
                "ORDER BY title LIMIT 5"
            ),
            {"n": needle},
        )
    ).all()
    for r in resources:
        results.append(
            SearchResult(type="resource", id=r.id, title=r.title, subtitle=f"Resource · {r.resource_type}", href="/library")
        )

    # 5. Questions
    questions = (
        await session.execute(
            text("SELECT id, stem FROM questions WHERE lower(stem) LIKE :n AND is_published = :pub ORDER BY stem LIMIT 5"),
            {"n": needle, "pub": published},
        )
    ).all()
    for qq in questions:
        results.append(SearchResult(type="question", id=qq.id, title=qq.stem[:90], subtitle="Practice · MCQ", href="/practice"))

    # 6. Viva
    viva = (
        await session.execute(
            text("SELECT id, prompt FROM viva_questions WHERE lower(prompt) LIKE :n AND is_published = :pub ORDER BY prompt LIMIT 4"),
            {"n": needle, "pub": published},
        )
    ).all()
    for vv in viva:
        results.append(SearchResult(type="viva", id=vv.id, title=vv.prompt[:90], subtitle="Practice · Viva", href="/practice"))

    return results
