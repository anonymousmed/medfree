"""Gamification (non-childish): XP, streaks, badges, mastery.

Tracked per user; derived from real study activity (progress, quiz attempts,
viva attempts, flashcards reviewed). Never manipulative notifications.
"""
from __future__ import annotations

from datetime import datetime, date
from typing import Optional

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, UnicodeText
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin

BADGE_FIRST_TOPIC = "first_topic"
BADGE_ANATOMY_EXPLORER = "anatomy_explorer"
BADGE_ATLAS_MASTER = "atlas_master"
BADGE_VIVA_STARTER = "viva_starter"
BADGE_MCQ_100 = "mcq_100"
BADGE_MCQ_500 = "mcq_500"
BADGE_STREAK_7 = "streak_7"
BADGE_STREAK_30 = "streak_30"
BADGE_PRACTICAL_READY = "practical_ready"
BADGE_FIRST_REVISION = "first_revision"
BADGE_SUBJECT_MASTER = "subject_master"

ALL_BADGES = [
    BADGE_FIRST_TOPIC,
    BADGE_ANATOMY_EXPLORER,
    BADGE_ATLAS_MASTER,
    BADGE_VIVA_STARTER,
    BADGE_MCQ_100,
    BADGE_MCQ_500,
    BADGE_STREAK_7,
    BADGE_STREAK_30,
    BADGE_PRACTICAL_READY,
    BADGE_FIRST_REVISION,
    BADGE_SUBJECT_MASTER,
]


class UserBadge(Base):
    __tablename__ = "user_badges"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    badge_key: Mapped[str] = mapped_column(String(50), index=True)
    title: Mapped[Optional[str]] = mapped_column(String(100))
    description: Mapped[Optional[str]] = mapped_column(UnicodeText)
    earned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class UserStreak(Base):
    __tablename__ = "user_streaks"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    current_streak: Mapped[int] = mapped_column(Integer, default=0)
    longest_streak: Mapped[int] = mapped_column(Integer, default=0)
    last_active_on: Mapped[Optional[date]] = mapped_column(Date)
    total_xp: Mapped[int] = mapped_column(Integer, default=0)
    xp_this_month: Mapped[int] = mapped_column(Integer, default=0)
    total_attempts: Mapped[int] = mapped_column(Integer, default=0)


class XPTransaction(Base):
    """Awarded XP with a reason (auditable)."""

    __tablename__ = "xp_transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    amount: Mapped[int] = mapped_column(Integer, default=0)
    reason: Mapped[str] = mapped_column(String(80))  # quiz_correct / viva / flashcard_review / topic_complete / streak
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class GamificationEvent(Base):
    __tablename__ = "gamification_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    event_type: Mapped[str] = mapped_column(String(60))
    metadata_json: Mapped[Optional[str]] = mapped_column(UnicodeText)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
