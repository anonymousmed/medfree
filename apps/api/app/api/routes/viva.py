"""Viva engine."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_user
from app.db.session import get_session
from app.models.practice import VivaQuestion
from app.models.progress import VivaAttempt
from app.models.user import User
from app.schemas.practice import VivaAttemptRequest, VivaAttemptResult, VivaQuestionRead

router = APIRouter(prefix="/viva", tags=["viva"])


@router.get("", response_model=list[VivaQuestionRead])
async def list_viva(
    subject: str | None = Query(None),
    topic: str | None = Query(None),
    limit: int = Query(20, le=100),
    session: AsyncSession = Depends(get_session),
):
    stmt = select(VivaQuestion).where(VivaQuestion.is_published.is_(True))
    if subject:
        stmt = stmt.where(VivaQuestion.subject_slug == subject)
    if topic:
        stmt = stmt.where(VivaQuestion.topic_slug == topic)
    result = await session.execute(stmt.limit(limit))
    return result.scalars().all()


@router.get("/count", response_model=dict)
async def viva_count(session: AsyncSession = Depends(get_session)):
    total = (await session.execute(select(func.count()).select_from(VivaQuestion).where(VivaQuestion.is_published.is_(True)))).scalar() or 0
    return {"total_viva": total}


@router.post("/{viva_id}/attempt", response_model=VivaAttemptResult)
async def attempt_viva(
    viva_id: int,
    payload: VivaAttemptRequest,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_db_user),
):
    q = (
        await session.execute(select(VivaQuestion).where(VivaQuestion.id == viva_id))
    ).scalar_one_or_none()
    if q is None:
        raise HTTPException(status_code=404, detail="Viva question not found")

    session.add(
        VivaAttempt(
            user_id=user.id,
            viva_question_id=q.id,
            student_answer=payload.student_answer,
            self_rating=payload.self_rating,
            completed_at=datetime.now(timezone.utc),
        )
    )
    await session.commit()

    return VivaAttemptResult(
        viva_question_id=q.id,
        model_answer=q.model_answer,
        key_points=q.key_points,
    )
