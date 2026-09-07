"""Progress & attempt tracking (per user)."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class Bookmark(TimestampMixin, Base):
    __tablename__ = "bookmarks"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    target_type: Mapped[str] = mapped_column(String(40))  # topic/resource/atlas/question
    target_id: Mapped[Optional[int]] = mapped_column(Integer, index=True)
    target_slug: Mapped[Optional[str]] = mapped_column(String(200))
    title: Mapped[Optional[str]] = mapped_column(String(300))
    note: Mapped[Optional[str]] = mapped_column(Text)


class Note(TimestampMixin, Base):
    __tablename__ = "notes"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    target_type: Mapped[str] = mapped_column(String(40))  # topic/resource/atlas
    target_id: Mapped[Optional[int]] = mapped_column(Integer, index=True)
    target_slug: Mapped[Optional[str]] = mapped_column(String(200))
    body: Mapped[str] = mapped_column(Text)
    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False)


class UserProgress(TimestampMixin, Base):
    __tablename__ = "user_progress"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    subject_slug: Mapped[str] = mapped_column(String(100), index=True)
    topic_slug: Mapped[Optional[str]] = mapped_column(String(150), index=True)
    state: Mapped[str] = mapped_column(String(30), default="not_started")  # not_started/in_progress/completed
    mastery: Mapped[float] = mapped_column(Float, default=0.0)
    time_spent_seconds: Mapped[int] = mapped_column(Integer, default=0)


class QuizAttempt(Base):
    __tablename__ = "question_attempts"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id", ondelete="CASCADE"))
    selected_option_id: Mapped[Optional[int]] = mapped_column(Integer)
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False)
    score: Mapped[Optional[float]] = mapped_column(Float)
    answered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class VivaAttempt(Base):
    __tablename__ = "viva_attempts"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    viva_question_id: Mapped[int] = mapped_column(ForeignKey("viva_questions.id", ondelete="CASCADE"))
    student_answer: Mapped[Optional[str]] = mapped_column(Text)
    self_rating: Mapped[Optional[int]] = mapped_column(Integer)  # 1-5
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class FlashcardReview(Base):
    __tablename__ = "flashcard_reviews"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    card_id: Mapped[int] = mapped_column(ForeignKey("flashcards.id", ondelete="CASCADE"))
    quality: Mapped[int] = mapped_column(Integer, default=0)  # 0-5 -> EF/interval
    ease_factor: Mapped[float] = mapped_column(Float, default=2.5)
    interval_days: Mapped[int] = mapped_column(Integer, default=0)
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    review_count: Mapped[int] = mapped_column(Integer, default=0)
    last_reviewed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class StudySession(Base):
    __tablename__ = "study_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    duration_seconds: Mapped[int] = mapped_column(Integer, default=0)
    subject_slug: Mapped[Optional[str]] = mapped_column(String(100))
