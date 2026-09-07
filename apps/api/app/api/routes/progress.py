"""User progress endpoints (scoped to the authenticated user)."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_user
from app.db.session import get_session
from app.models.progress import FlashcardReview, QuizAttempt, UserProgress, VivaAttempt
from app.models.user import User

router = APIRouter(prefix="/progress", tags=["progress"])


class ProgressRow(BaseModel):
    subject_slug: str
    topic_slug: str | None = None
    state: str
    mastery: float


class RecordProgressRequest(BaseModel):
    subject_slug: str
    topic_slug: str | None = None
    state: str = "in_progress"
    mastery: float = 0.0


class ProgressSummary(BaseModel):
    total_quiz_attempts: int
    correct_quiz_attempts: int
    accuracy: float
    viva_attempts: int
    flashcards_due: int
    topics_started: int
    topics_completed: int


@router.get("/summary", response_model=ProgressSummary)
async def summary(
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_db_user),
):
    attempts = (
        await session.execute(
            select(func.count()).select_from(QuizAttempt).where(QuizAttempt.user_id == user.id)
        )
    ).scalar() or 0
    correct = (
        await session.execute(
            select(func.count())
            .select_from(QuizAttempt)
            .where(QuizAttempt.user_id == user.id, QuizAttempt.is_correct.is_(True))
        )
    ).scalar() or 0
    viva = (
        await session.execute(
            select(func.count()).select_from(VivaAttempt).where(VivaAttempt.user_id == user.id)
        )
    ).scalar() or 0
    started = (
        await session.execute(
            select(func.count())
            .select_from(UserProgress)
            .where(UserProgress.user_id == user.id)
        )
    ).scalar() or 0
    completed = (
        await session.execute(
            select(func.count())
            .select_from(UserProgress)
            .where(UserProgress.user_id == user.id, UserProgress.state == "completed")
        )
    ).scalar() or 0

    now = datetime.now(timezone.utc)
    due = (
        await session.execute(
            select(func.count())
            .select_from(FlashcardReview)
            .where(FlashcardReview.user_id == user.id, FlashcardReview.due_at <= now)
        )
    ).scalar() or 0

    return ProgressSummary(
        total_quiz_attempts=attempts,
        correct_quiz_attempts=correct,
        accuracy=round((correct / attempts) * 100, 1) if attempts else 0.0,
        viva_attempts=viva,
        flashcards_due=due,
        topics_started=started,
        topics_completed=completed,
    )


@router.get("/topics", response_model=list[ProgressRow])
async def topic_progress(
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_db_user),
):
    result = await session.execute(
        select(UserProgress).where(UserProgress.user_id == user.id)
    )
    return list(result.scalars().all())


@router.post("/topics", response_model=ProgressRow)
async def record_topic(
    payload: RecordProgressRequest,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_db_user),
):
    row = (
        await session.execute(
            select(UserProgress).where(
                UserProgress.user_id == user.id,
                UserProgress.subject_slug == payload.subject_slug,
                UserProgress.topic_slug == payload.topic_slug,
            )
        )
    ).scalar_one_or_none()
    if row is None:
        row = UserProgress(
            user_id=user.id,
            subject_slug=payload.subject_slug,
            topic_slug=payload.topic_slug,
            state=payload.state,
            mastery=payload.mastery,
        )
        session.add(row)
    else:
        row.state = payload.state
        row.mastery = payload.mastery
    await session.commit()
    await session.refresh(row)
    return row
