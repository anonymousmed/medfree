"""Curriculum subjects + topics (public). Curriculum is not hard-coded."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import get_session
from app.models.subject import Subject, Topic, TopicBlock
from app.schemas.learning import TopicBlockRead, TopicDetailForBlocks, TopicBlockUpsert
from pydantic import BaseModel

router = APIRouter(prefix="/subjects", tags=["subjects"])


class SubjectRead(BaseModel):
    id: int
    slug: str
    title: str
    description: str | None = None
    icon: str | None = None
    color: str | None = None


class TopicRead(BaseModel):
    id: int
    slug: str
    title: str
    summary: str | None = None
    difficulty: str = "medium"
    est_minutes: int = 0


class TopicRef(BaseModel):
    slug: str
    title: str
    difficulty: str = "medium"
    subject_slug: str | None = None


class TopicDetail(TopicRead):
    content_markdown: str | None = None
    learning_objectives: str | None = None
    blocks: list[TopicBlockRead] = []
    # Curriculum knowledge graph (Phase 11).
    prerequisites: list[TopicRef] = []
    related: list[TopicRef] = []
    next_topics: list[TopicRef] = []


@router.get("", response_model=list[SubjectRead])
async def list_subjects(session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(Subject)
        .where(Subject.is_active.is_(True))
        .order_by(Subject.sort_order)
    )
    return result.scalars().all()


@router.get("/{slug}", response_model=SubjectRead)
async def get_subject(slug: str, session: AsyncSession = Depends(get_session)):
    row = (await session.execute(select(Subject).where(Subject.slug == slug))).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Subject not found")
    return row


@router.get("/{slug}/topics", response_model=list[TopicRead])
async def list_topics(slug: str, session: AsyncSession = Depends(get_session)):
    subject = (await session.execute(select(Subject).where(Subject.slug == slug))).scalar_one_or_none()
    if subject is None:
        raise HTTPException(status_code=404, detail="Subject not found")
    result = await session.execute(
        select(Topic)
        .where(Topic.subject_id == subject.id, Topic.is_published.is_(True))
        .order_by(Topic.sort_order)
    )
    return result.scalars().all()


@router.get("/{subject_slug}/topics/{topic_slug}", response_model=TopicDetail)
async def get_topic(subject_slug: str, topic_slug: str, session: AsyncSession = Depends(get_session)):
    subject = (await session.execute(select(Subject).where(Subject.slug == subject_slug))).scalar_one_or_none()
    if subject is None:
        raise HTTPException(status_code=404, detail="Subject not found")
    row = (
        await session.execute(
            select(Topic)
            .options(selectinload(Topic.blocks))
            .where(
                Topic.subject_id == subject.id,
                Topic.slug == topic_slug,
                Topic.is_published.is_(True),
            )
        )
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Topic not found")
    # Order blocks by position for a stable learning flow.
    row.blocks.sort(key=lambda b: b.position)
    # Load curriculum knowledge-graph edges (prerequisite / related / next).
    return await _topic_detail(row, session)


async def _topic_detail(row, session: AsyncSession) -> dict:
    from app.models.subject import LINK_NEXT, LINK_PREREQUISITE, LINK_RELATED, TopicLink

    # Map id -> (slug, title, difficulty, subject_slug) for every referenced topic.
    links = (
        await session.execute(
            select(TopicLink).where(
                (TopicLink.from_topic_id == row.id) | (TopicLink.to_topic_id == row.id)
            )
        )
    ).scalars().all()
    ids = {l.from_topic_id for l in links} | {l.to_topic_id for l in links} - {row.id}
    ref_map: dict[int, tuple] = {}
    if ids:
        for t in (
            await session.execute(
                select(Topic).options(selectinload(Topic.subject)).where(Topic.id.in_(ids))
            )
        ).scalars().all():
            ref_map[t.id] = (t.slug, t.title, t.difficulty, t.subject.slug if t.subject else None)

    def other_for(l, direction):
        # direction: "in" -> the edge points AT row (row is the target), so the
        # other end is from_topic_id; "out" -> row is the source (other is
        # to_topic_id); "any" -> the end that is not row.
        if direction == "in":
            return l.from_topic_id if l.to_topic_id == row.id else None
        if direction == "out":
            return l.to_topic_id if l.from_topic_id == row.id else None
        return l.to_topic_id if l.from_topic_id == row.id else l.from_topic_id

    def make(out_type, direction):
        seen = set()
        out = []
        for l in links:
            if l.link_type != out_type:
                continue
            other_id = other_for(l, direction)
            ref = ref_map.get(other_id)
            if not ref:
                continue
            if ref[0] in seen:
                continue
            seen.add(ref[0])
            out.append(
                {"slug": ref[0], "title": ref[1], "difficulty": ref[2], "subject_slug": ref[3]}
            )
        return out

    return {
        "id": row.id, "slug": row.slug, "title": row.title, "summary": row.summary,
        "difficulty": row.difficulty, "est_minutes": row.est_minutes,
        "content_markdown": row.content_markdown, "learning_objectives": row.learning_objectives,
        "blocks": row.blocks,
        "prerequisites": make(LINK_PREREQUISITE, "in"),
        "related": make(LINK_RELATED, "any"),
        "next_topics": make(LINK_NEXT, "out"),
    }
