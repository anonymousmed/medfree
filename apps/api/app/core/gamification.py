"""Gamification engine.

Non-childish, derived from real study activity (not fabricated). Recomputes
streak, XP and badges from actual progress/attempt/feedback data on each call,
so it is idempotent and auditable.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.gamification import UserBadge, UserStreak, XPTransaction
from app.models.progress import FlashcardReview, QuizAttempt, UserProgress, VivaAttempt
from app.models.user import User

XP_QUIZ_CORRECT = 10
XP_VIVA = 5
XP_FLASHCARD = 3
XP_TOPIC_COMPLETE = 20

DEFAULT_BADGE_META = {
    "first_topic": ("First Topic", "Complete your first topic."),
    "viva_starter": ("Viva Starter", "Attempt your first viva."),
    "first_revision": ("First Revision", "Do your first spaced-repetition review."),
    "mcq_100": ("100 MCQs", "Attempt 100 MCQs."),
    "mcq_500": ("500 MCQs", "Attempt 500 MCQs."),
    "streak_7": ("7-Day Streak", "Study 7 days in a row."),
    "streak_30": ("30-Day Streak", "Study 30 days in a row."),
    "subject_master": ("Subject Master", "Complete a full subject."),
}


async def get_or_update(session: AsyncSession, user: User) -> dict[str, Any]:
    """Compute (and persist, if new) the user's streak, XP and badges."""
    now = datetime.now(timezone.utc)
    today = now.date()

    topics_completed = (
        await session.execute(
            select(func.count()).select_from(UserProgress)
            .where(UserProgress.user_id == user.id, UserProgress.state == "completed")
        )
    ).scalar() or 0
    quiz_total = (
        await session.execute(select(func.count()).select_from(QuizAttempt).where(QuizAttempt.user_id == user.id))
    ).scalar() or 0
    quiz_correct = (
        await session.execute(
            select(func.count()).select_from(QuizAttempt)
            .where(QuizAttempt.user_id == user.id, QuizAttempt.is_correct.is_(True))
        )
    ).scalar() or 0
    viva_total = (
        await session.execute(select(func.count()).select_from(VivaAttempt).where(VivaAttempt.user_id == user.id))
    ).scalar() or 0
    flashcard_total = (
        await session.execute(select(func.count()).select_from(FlashcardReview).where(FlashcardReview.user_id == user.id))
    ).scalar() or 0

    # Streak
    streak = (
        await session.execute(select(UserStreak).where(UserStreak.user_id == user.id))
    ).scalar_one_or_none()
    if streak is None:
        streak = UserStreak(user_id=user.id)
        session.add(streak)
        await session.flush()

    active_recently = bool(quiz_total or viva_total or flashcard_total or topics_completed)
    if active_recently and streak.last_active_on != today:
        if streak.last_active_on:
            diff = (today - streak.last_active_on).days
            streak.current_streak = streak.current_streak + 1 if diff == 1 else 1
        else:
            streak.current_streak = 1
        streak.last_active_on = today
        streak.longest_streak = max(streak.longest_streak, streak.current_streak)

    # XP: deterministic from activity; record the delta as auditable transactions.
    target_xp = quiz_correct * XP_QUIZ_CORRECT + viva_total * XP_VIVA + flashcard_total * XP_FLASHCARD + topics_completed * XP_TOPIC_COMPLETE
    current_xp = (
        await session.execute(select(func.coalesce(func.sum(XPTransaction.amount), 0)).where(XPTransaction.user_id == user.id))
    ).scalar() or 0
    if target_xp > current_xp:
        session.add(XPTransaction(user_id=user.id, amount=target_xp - int(current_xp), reason="activity_sync", created_at=now))
    streak.total_xp = int(target_xp)
    streak.total_attempts = quiz_total

    # Badges
    await _award_badges(session, user.id, quiz_total, viva_total, flashcard_total, streak.current_streak, topics_completed)

    await session.commit()

    earned = (
        await session.execute(select(UserBadge).where(UserBadge.user_id == user.id))
    ).scalars().all()

    return {
        "streak": {"current": streak.current_streak, "longest": streak.longest_streak},
        "xp": streak.total_xp,
        "level": xp_level(streak.total_xp),
        "quiz_attempts": quiz_total,
        "quiz_accuracy": round((quiz_correct / quiz_total) * 100, 1) if quiz_total else 0.0,
        "topics_completed": topics_completed,
        "badges": [
            {"key": b.badge_key, "title": b.title, "description": b.description, "earned_at": b.earned_at.isoformat()}
            for b in earned
        ],
    }


def xp_level(xp: int) -> int:
    return (xp // 100) + 1


async def _award_badges(session, user_id, quiz_total, viva_total, flashcard_total, streak, topics_completed) -> None:
    meta = DEFAULT_BADGE_META
    earned = {
        "first_topic": topics_completed >= 1,
        "viva_starter": viva_total >= 1,
        "first_revision": flashcard_total >= 1,
        "mcq_100": quiz_total >= 100,
        "mcq_500": quiz_total >= 500,
        "streak_7": streak >= 7,
        "streak_30": streak >= 30,
    }
    existing = {
        b.badge_key
        for b in (await session.execute(select(UserBadge).where(UserBadge.user_id == user_id))).scalars().all()
    }
    now = datetime.now(timezone.utc)
    for key, cond in earned.items():
        if cond and key not in existing:
            title, desc = meta.get(key, (key, ""))
            session.add(UserBadge(user_id=user_id, badge_key=key, title=title, description=desc, earned_at=now))
