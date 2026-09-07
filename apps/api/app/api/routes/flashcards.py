"""Flashcard engine with a well-tested spaced-repetition schedule.

MVP uses an SM-2-inspired interval (ease factor + quality), transparent and
easy to verify. An FSRS implementation can be dropped in later without changing
the API contract.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_user
from app.db.session import get_session
from app.models.practice import Flashcard
from app.models.progress import FlashcardReview
from app.models.user import User
from app.schemas.flashcards import (
    FlashcardRead,
    FlashcardReviewRequest,
    FlashcardReviewResult,
    FlashcardStats,
)

router = APIRouter(prefix="/flashcards", tags=["flashcards"])

DEFAULT_EASE = 2.5
MIN_INTERVAL = 1


@router.get("", response_model=list[FlashcardRead])
async def list_cards(
    subject: str | None = Query(None),
    topic: str | None = Query(None),
    limit: int = Query(100, le=200),
    session: AsyncSession = Depends(get_session),
):
    stmt = select(Flashcard)
    if subject:
        stmt = stmt.where(Flashcard.subject_slug == subject)
    if topic:
        stmt = stmt.where(Flashcard.topic_slug == topic)
    result = await session.execute(stmt.limit(limit))
    return list(result.scalars().all())


@router.get("/stats", response_model=FlashcardStats)
async def stats(
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_db_user),
):
    total = (await session.execute(select(func.count()).select_from(Flashcard))).scalar() or 0
    now = datetime.now(timezone.utc)

    due = (
        await session.execute(
            select(func.count())
            .select_from(FlashcardReview)
            .where(FlashcardReview.user_id == user.id, FlashcardReview.due_at <= now)
        )
    ).scalar() or 0

    # Count never-reviewed cards (they are due immediately).
    reviewed_ids = select(FlashcardReview.card_id).where(FlashcardReview.user_id == user.id)
    never_reviewed = (
        await session.execute(
            select(func.count()).select_from(Flashcard).where(Flashcard.id.not_in(reviewed_ids))
        )
    ).scalar() or 0

    reviewed = (
        await session.execute(
            select(func.count()).select_from(FlashcardReview).where(FlashcardReview.user_id == user.id)
        )
    ).scalar() or 0

    avg_interval = (
        await session.execute(
            select(func.avg(FlashcardReview.interval_days)).where(FlashcardReview.user_id == user.id)
        )
    ).scalar() or 0

    return FlashcardStats(
        total_cards=total,
        due_now=due + never_reviewed,
        reviewed=reviewed,
        average_interval_days=round(float(avg_interval), 1),
    )


@router.get("/due", response_model=list[FlashcardRead])
async def due_cards(
    subject: str | None = Query(None),
    limit: int = Query(30, le=100),
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_db_user),
):
    """Cards due for this user (never reviewed, or past due_at)."""
    now = datetime.now(timezone.utc)
    stmt = (
        select(Flashcard)
        .outerjoin(
            FlashcardReview,
            (FlashcardReview.card_id == Flashcard.id) & (FlashcardReview.user_id == user.id),
        )
        .where((FlashcardReview.id.is_(None)) | (FlashcardReview.due_at <= now))
    )
    if subject:
        stmt = stmt.where(Flashcard.subject_slug == subject)
    result = await session.execute(stmt.limit(limit))
    return list(result.scalars().all())


@router.post("/{card_id}/review", response_model=FlashcardReviewResult)
async def review_card(
    card_id: int,
    payload: FlashcardReviewRequest,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_db_user),
):
    card = (await session.execute(select(Flashcard).where(Flashcard.id == card_id))).scalar_one_or_none()
    if card is None:
        raise HTTPException(status_code=404, detail="Flashcard not found")

    review = (
        await session.execute(
            select(FlashcardReview).where(
                FlashcardReview.user_id == user.id, FlashcardReview.card_id == card_id
            )
        )
    ).scalar_one_or_none()

    quality = payload.quality
    if review is None:
        review = FlashcardReview(
            user_id=user.id,
            card_id=card_id,
            ease_factor=DEFAULT_EASE,
            interval_days=MIN_INTERVAL,
            quality=quality,
            review_count=0,
            due_at=datetime.now(timezone.utc),
            last_reviewed_at=datetime.now(timezone.utc),
        )
        session.add(review)

    # SM-2 style update.
    review.review_count += 1
    review.ease_factor = max(
        1.3, review.ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    )
    if quality < 3:
        review.interval_days = MIN_INTERVAL
    elif review.review_count == 1:
        review.interval_days = 1
    elif review.review_count == 2:
        review.interval_days = 6
    else:
        review.interval_days = round(review.interval_days * review.ease_factor)

    now = datetime.now(timezone.utc)
    review.last_reviewed_at = now
    review.due_at = now + timedelta(days=review.interval_days)
    review.quality = quality

    await session.commit()

    return FlashcardReviewResult(
        id=card_id,
        quality=quality,
        interval_days=review.interval_days,
        due_at=review.due_at.isoformat(),
    )
