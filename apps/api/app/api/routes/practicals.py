"""Practicals: step-by-step procedure resources with full teaching metadata."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import get_session
from app.models.practice import Practical
from app.schemas.practicals import PracticalDetail, PracticalRead

router = APIRouter(prefix="/practicals", tags=["practicals"])


@router.get("", response_model=list[PracticalRead])
async def list_practicals(
    subject: str | None = Query(None),
    topic: str | None = Query(None),
    limit: int = Query(50, le=100),
    session: AsyncSession = Depends(get_session),
):
    stmt = select(Practical).where(Practical.is_published.is_(True))
    if subject:
        stmt = stmt.where(Practical.subject_slug == subject)
    if topic:
        stmt = stmt.where(Practical.topic_slug == topic)
    result = await session.execute(stmt.limit(limit))
    return result.scalars().all()


@router.get("/{practical_id}", response_model=PracticalDetail)
async def get_practical(practical_id: int, session: AsyncSession = Depends(get_session)):
    row = (
        await session.execute(
            select(Practical)
            .options(selectinload(Practical.steps))
            .where(Practical.id == practical_id, Practical.is_published.is_(True))
        )
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Practical not found")
    row.steps.sort(key=lambda s: s.position)
    return row
