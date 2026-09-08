"""Admin content-authoring endpoints (admin-only).

Lets an admin create MCQs, viva questions, flashcards and practicals directly
(instead of only via the seed script). All endpoints are guarded by
``require_admin`` and write an audit-log row so changes are traceable.

Gap closed: previously content like flashcards / questions / viva / practicals
could only be created by the seed script; there were only learner-facing
``attempt``/``review`` routes.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import require_admin, resolve_token
from app.core.auth import TokenPayload
from app.core.security import client_ip, record_audit
from app.db.session import get_session
from app.models.practice import Flashcard, Practical, PracticalStep, Question, QuestionOption, VivaQuestion

router = APIRouter(prefix="/admin/content", tags=["admin"], dependencies=[Depends(require_admin)])


# --- MCQs -------------------------------------------------------------------
class OptionIn(BaseModel):
    option_text: str = Field(..., min_length=1)
    is_correct: bool = False
    sort_order: int = 0


class QuestionCreate(BaseModel):
    subject_slug: str = Field(..., min_length=1, max_length=100)
    topic_slug: str | None = None
    stem: str = Field(..., min_length=1)
    explanation: str | None = None
    reference: str | None = None
    difficulty: str = "medium"
    learning_objective: str | None = None
    reviewer: str | None = None
    image_url: str | None = None
    qtype: str = "single_best_answer"
    is_published: bool = True
    options: list[OptionIn] = Field(..., min_length=2, max_length=8)


@router.post("/questions", status_code=201)
async def create_question(
    payload: QuestionCreate,
    session: AsyncSession = Depends(get_session),
    request: Request = None,
    token: TokenPayload = Depends(resolve_token),
):
    if not any(o.is_correct for o in payload.options):
        raise HTTPException(status_code=422, detail="At least one option must be marked correct")
    q = Question(
        subject_slug=payload.subject_slug,
        topic_slug=payload.topic_slug,
        stem=payload.stem,
        explanation=payload.explanation,
        reference=payload.reference,
        difficulty=payload.difficulty,
        learning_objective=payload.learning_objective,
        reviewer=payload.reviewer,
        image_url=payload.image_url,
        qtype=payload.qtype,
        is_published=payload.is_published,
    )
    session.add(q)
    await session.flush()
    for i, o in enumerate(payload.options):
        session.add(
            QuestionOption(
                question_id=q.id,
                option_text=o.option_text,
                is_correct=o.is_correct,
                sort_order=o.sort_order or i,
            )
        )
    await record_audit(
        session, action="question.create", actor_email=token.email,
        target_type="question", detail=f"subject={payload.subject_slug} stem='{payload.stem[:60]}'",
        ip_address=client_ip(request),
    )
    await session.commit()
    row = (
        await session.execute(
            select(Question).options(selectinload(Question.options)).where(Question.id == q.id)
        )
    ).scalar_one()
    return {
        "id": row.id,
        "subject_slug": row.subject_slug,
        "topic_slug": row.topic_slug,
        "stem": row.stem,
        "qtype": row.qtype,
        "difficulty": row.difficulty,
        "image_url": row.image_url,
        "options": [
            {"id": o.id, "option_text": o.option_text, "is_correct": o.is_correct, "sort_order": o.sort_order}
            for o in sorted(row.options, key=lambda x: x.sort_order)
        ],
        "is_published": row.is_published,
    }


# --- Viva -------------------------------------------------------------------
class VivaCreate(BaseModel):
    subject_slug: str = Field(..., min_length=1, max_length=100)
    topic_slug: str | None = None
    prompt: str = Field(..., min_length=1)
    model_answer: str = Field(..., min_length=1)
    key_points: str | None = None
    difficulty: str = "medium"
    is_published: bool = True


@router.post("/viva", status_code=201)
async def create_viva(
    payload: VivaCreate,
    session: AsyncSession = Depends(get_session),
    request: Request = None,
    token: TokenPayload = Depends(resolve_token),
):
    v = VivaQuestion(
        subject_slug=payload.subject_slug,
        topic_slug=payload.topic_slug,
        prompt=payload.prompt,
        model_answer=payload.model_answer,
        key_points=payload.key_points,
        difficulty=payload.difficulty,
        is_published=payload.is_published,
    )
    session.add(v)
    await record_audit(
        session, action="viva.create", actor_email=token.email,
        target_type="viva", detail=f"subject={payload.subject_slug} prompt='{payload.prompt[:60]}'",
        ip_address=client_ip(request),
    )
    await session.commit()
    return {"id": v.id, "subject_slug": v.subject_slug, "topic_slug": v.topic_slug,
            "prompt": v.prompt, "difficulty": v.difficulty, "is_published": v.is_published}


# --- Flashcard --------------------------------------------------------------
class FlashcardCreate(BaseModel):
    subject_slug: str = Field(..., min_length=1, max_length=100)
    topic_slug: str | None = None
    front: str = Field(..., min_length=1)
    back: str = Field(..., min_length=1)
    card_type: str = "basic"


@router.post("/flashcards", status_code=201)
async def create_flashcard(
    payload: FlashcardCreate,
    session: AsyncSession = Depends(get_session),
    request: Request = None,
    token: TokenPayload = Depends(resolve_token),
):
    c = Flashcard(
        subject_slug=payload.subject_slug,
        topic_slug=payload.topic_slug,
        front=payload.front,
        back=payload.back,
        card_type=payload.card_type,
    )
    session.add(c)
    await record_audit(
        session, action="flashcard.create", actor_email=token.email,
        target_type="flashcard", detail=f"subject={payload.subject_slug} front='{payload.front[:60]}'",
        ip_address=client_ip(request),
    )
    await session.commit()
    return {"id": c.id, "subject_slug": c.subject_slug, "topic_slug": c.topic_slug,
            "front": c.front, "back": c.back, "card_type": c.card_type}


# --- Practical --------------------------------------------------------------
class PracticalStepIn(BaseModel):
    step_text: str = Field(..., min_length=1)
    observation: str | None = None
    position: int = 0


class PracticalCreate(BaseModel):
    subject_slug: str = Field(..., min_length=1, max_length=100)
    topic_slug: str | None = None
    title: str = Field(..., min_length=1, max_length=250)
    objective: str | None = None
    requirements: str | None = None
    principle: str | None = None
    preparation: str | None = None
    observation: str | None = None
    interpretation: str | None = None
    common_mistakes: str | None = None
    safety_notes: str | None = None
    clinical_significance: str | None = None
    reference_text: str | None = None
    video_url: str | None = None
    is_published: bool = True
    steps: list[PracticalStepIn] = Field(default_factory=list)


@router.post("/practicals", status_code=201)
async def create_practical(
    payload: PracticalCreate,
    session: AsyncSession = Depends(get_session),
    request: Request = None,
    token: TokenPayload = Depends(resolve_token),
):
    p = Practical(
        subject_slug=payload.subject_slug,
        topic_slug=payload.topic_slug,
        title=payload.title,
        objective=payload.objective,
        requirements=payload.requirements,
        principle=payload.principle,
        preparation=payload.preparation,
        observation=payload.observation,
        interpretation=payload.interpretation,
        common_mistakes=payload.common_mistakes,
        safety_notes=payload.safety_notes,
        clinical_significance=payload.clinical_significance,
        reference_text=payload.reference_text,
        video_url=payload.video_url,
        is_published=payload.is_published,
    )
    session.add(p)
    await session.flush()
    for i, s in enumerate(payload.steps):
        session.add(
            PracticalStep(
                practical_id=p.id, step_text=s.step_text,
                observation=s.observation, position=s.position or i,
            )
        )
    await record_audit(
        session, action="practical.create", actor_email=token.email,
        target_type="practical", detail=f"subject={payload.subject_slug} title='{payload.title}'",
        ip_address=client_ip(request),
    )
    await session.commit()
    row = (
        await session.execute(
            select(Practical).options(selectinload(Practical.steps)).where(Practical.id == p.id)
        )
    ).scalar_one()
    return {
        "id": row.id,
        "subject_slug": row.subject_slug,
        "topic_slug": row.topic_slug,
        "title": row.title,
        "is_published": row.is_published,
        "steps": [
            {"id": s.id, "position": s.position, "step_text": s.step_text}
            for s in sorted(row.steps, key=lambda x: x.position)
        ],
    }
