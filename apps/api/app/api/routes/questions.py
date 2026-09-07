"""MCQ engine."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_db_user
from app.db.session import get_session
from app.models.practice import Question, QuestionOption
from app.models.progress import QuizAttempt
from app.models.user import User
from app.schemas.practice import (
    QuestionAttemptRequest,
    QuestionAttemptResult,
    QuestionRead,
)

router = APIRouter(prefix="/questions", tags=["questions"])


@router.get("", response_model=list[QuestionRead])
async def list_questions(
    subject: str | None = Query(None),
    topic: str | None = Query(None),
    limit: int = Query(20, le=100),
    session: AsyncSession = Depends(get_session),
):
    stmt = select(Question).where(Question.is_published.is_(True))
    if subject:
        stmt = stmt.where(Question.subject_slug == subject)
    if topic:
        stmt = stmt.where(Question.topic_slug == topic)
    stmt = stmt.options(selectinload(Question.options))
    result = await session.execute(stmt.limit(limit))
    return result.scalars().all()


@router.post("/{question_id}/attempt", response_model=QuestionAttemptResult)
async def attempt_question(
    question_id: int,
    payload: QuestionAttemptRequest,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_db_user),
):
    question = (
        await session.execute(
            select(Question)
            .where(Question.id == question_id)
            .options(selectinload(Question.options))
        )
    ).scalar_one_or_none()
    if question is None:
        raise HTTPException(status_code=404, detail="Question not found")

    selected = next((o for o in question.options if o.id == payload.selected_option_id), None)
    if selected is None:
        raise HTTPException(status_code=422, detail="Invalid option id")

    is_correct = selected.is_correct
    correct_option = next((o for o in question.options if o.is_correct), None)

    session.add(
        QuizAttempt(
            user_id=user.id,
            question_id=question.id,
            selected_option_id=selected.id,
            is_correct=is_correct,
            score=1.0 if is_correct else 0.0,
            answered_at=datetime.now(timezone.utc),
        )
    )
    await session.commit()

    return QuestionAttemptResult(
        question_id=question.id,
        selected_option_id=selected.id,
        is_correct=is_correct,
        correct_option_id=correct_option.id if correct_option else 0,
        explanation=question.explanation,
        reference=question.reference,
    )


@router.get("/recommendations", response_model=list[QuestionRead])
async def recommendations(
    limit: int = Query(10, le=50),
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_db_user),
):
    """Simple recommendation: published questions the user has not attempted yet."""
    attempted = select(QuizAttempt.question_id).where(QuizAttempt.user_id == user.id)
    stmt = (
        select(Question)
        .where(Question.is_published.is_(True), Question.id.not_in(attempted))
        .options(selectinload(Question.options))
        .limit(limit)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


class QuizSessionResult(BaseModel):
    total: int
    correct: int
    accuracy: float
    results: list[QuestionAttemptResult]


class AnswerItem(BaseModel):
    question_id: int
    selected_option_id: int


class QuizAttemptBatch(BaseModel):
    answers: list[AnswerItem] = Field(default_factory=list)


@router.post("/quiz", response_model=QuizSessionResult)
async def quiz_session(
    payload: QuizAttemptBatch,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_db_user),
):
    """Submit a whole quiz. Records all attempts, returns a scored summary."""
    results: list[QuestionAttemptResult] = []
    correct_count = 0
    for item in payload.answers:
        question = (
            await session.execute(
                select(Question)
                .where(Question.id == item.question_id)
                .options(selectinload(Question.options))
            )
        ).scalar_one_or_none()
        if question is None:
            continue
        selected = next((o for o in question.options if o.id == item.selected_option_id), None)
        if selected is None:
            continue
        is_correct = selected.is_correct
        correct_option = next((o for o in question.options if o.is_correct), None)
        if is_correct:
            correct_count += 1
        session.add(
            QuizAttempt(
                user_id=user.id,
                question_id=question.id,
                selected_option_id=selected.id,
                is_correct=is_correct,
                score=1.0 if is_correct else 0.0,
                answered_at=datetime.now(timezone.utc),
            )
        )
        results.append(
            QuestionAttemptResult(
                question_id=question.id,
                selected_option_id=selected.id,
                is_correct=is_correct,
                correct_option_id=correct_option.id if correct_option else 0,
                explanation=question.explanation,
                reference=question.reference,
            )
        )
    await session.commit()
    total = len(results) or 1
    return QuizSessionResult(
        total=len(results),
        correct=correct_count,
        accuracy=round((correct_count / total) * 100, 1),
        results=results,
    )
