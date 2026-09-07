"""Practice: MCQs, viva, flashcards, practicals."""
from __future__ import annotations

from typing import Optional

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

class Question(Base):
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(primary_key=True)
    subject_slug: Mapped[str] = mapped_column(String(100), index=True)
    topic_slug: Mapped[Optional[str]] = mapped_column(String(150), index=True)
    stem: Mapped[str] = mapped_column(Text)
    qtype: Mapped[str] = mapped_column(String(30), default="single_best_answer")
    explanation: Mapped[Optional[str]] = mapped_column(Text)
    reference: Mapped[Optional[str]] = mapped_column(String(300))
    difficulty: Mapped[str] = mapped_column(String(20), default="medium")
    learning_objective: Mapped[Optional[str]] = mapped_column(Text)
    reviewer: Mapped[Optional[str]] = mapped_column(String(150))
    image_url: Mapped[Optional[str]] = mapped_column(String(500))
    is_published: Mapped[bool] = mapped_column(Boolean, default=False)

    options: Mapped[list["QuestionOption"]] = relationship(
        back_populates="question", cascade="all, delete-orphan"
    )


class QuestionOption(Base):
    __tablename__ = "question_options"

    id: Mapped[int] = mapped_column(primary_key=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id", ondelete="CASCADE"))
    option_text: Mapped[str] = mapped_column(Text)
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    question: Mapped[Question] = relationship(back_populates="options")


class VivaQuestion(Base):
    __tablename__ = "viva_questions"

    id: Mapped[int] = mapped_column(primary_key=True)
    subject_slug: Mapped[str] = mapped_column(String(100), index=True)
    topic_slug: Mapped[Optional[str]] = mapped_column(String(150), index=True)
    prompt: Mapped[str] = mapped_column(Text)
    model_answer: Mapped[str] = mapped_column(Text)
    key_points: Mapped[Optional[str]] = mapped_column(Text)
    difficulty: Mapped[str] = mapped_column(String(20), default="medium")
    is_published: Mapped[bool] = mapped_column(Boolean, default=False)


class Flashcard(Base):
    __tablename__ = "flashcards"

    id: Mapped[int] = mapped_column(primary_key=True)
    subject_slug: Mapped[str] = mapped_column(String(100), index=True)
    topic_slug: Mapped[Optional[str]] = mapped_column(String(150), index=True)
    front: Mapped[str] = mapped_column(Text)
    back: Mapped[str] = mapped_column(Text)
    card_type: Mapped[str] = mapped_column(String(30), default="basic")


class Practical(Base):
    __tablename__ = "practicals"

    id: Mapped[int] = mapped_column(primary_key=True)
    subject_slug: Mapped[str] = mapped_column(String(100), index=True)
    topic_slug: Mapped[Optional[str]] = mapped_column(String(150), index=True)
    title: Mapped[str] = mapped_column(String(250))
    objective: Mapped[Optional[str]] = mapped_column(Text)
    requirements: Mapped[Optional[str]] = mapped_column(Text)
    principle: Mapped[Optional[str]] = mapped_column(Text)
    preparation: Mapped[Optional[str]] = mapped_column(Text)
    observation: Mapped[Optional[str]] = mapped_column(Text)
    interpretation: Mapped[Optional[str]] = mapped_column(Text)
    common_mistakes: Mapped[Optional[str]] = mapped_column(Text)
    safety_notes: Mapped[Optional[str]] = mapped_column(Text)
    clinical_significance: Mapped[Optional[str]] = mapped_column(Text)
    reference_text: Mapped[Optional[str]] = mapped_column(Text)
    video_url: Mapped[Optional[str]] = mapped_column(String(500))
    is_published: Mapped[bool] = mapped_column(Boolean, default=False)

    steps: Mapped[list["PracticalStep"]] = relationship(
        back_populates="practical", cascade="all, delete-orphan"
    )


class PracticalStep(Base):
    __tablename__ = "practical_steps"

    id: Mapped[int] = mapped_column(primary_key=True)
    practical_id: Mapped[int] = mapped_column(ForeignKey("practicals.id", ondelete="CASCADE"))
    position: Mapped[int] = mapped_column(Integer, default=0)
    step_text: Mapped[str] = mapped_column(Text)
    observation: Mapped[Optional[str]] = mapped_column(Text)

    practical: Mapped[Practical] = relationship(back_populates="steps")
