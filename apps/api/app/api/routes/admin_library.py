"""Admin content-authoring endpoints (admin-only).

Lets an admin create MCQs, viva questions, flashcards and practicals directly
(instead of only via the seed script), including **bulk import** of many items
at once. All endpoints are guarded by ``require_admin`` and write an audit-log
row so changes are traceable.

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


def _validate_options(options: list[OptionIn]) -> None:
    if not any(o.is_correct for o in options):
        raise HTTPException(status_code=422, detail="At least one option must be marked correct")


@router.post("/questions", status_code=201)
async def create_question(
    payload: QuestionCreate,
    session: AsyncSession = Depends(get_session),
    request: Request = None,
    token: TokenPayload = Depends(resolve_token),
):
    _validate_options(payload.options)
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


# --- Bulk import ------------------------------------------------------------
class ImportRequest(BaseModel):
    resource_type: str = Field(..., pattern="^(questions|viva|flashcards|practicals)$")
    # Accept either a list of items, or {"items": [...]} for friendlier UIs.
    items: list[dict] = Field(..., min_length=1, max_length=2000)


def _coerce_items(items: list[dict]) -> list[dict]:
    """If a single item was passed as {'items': [...]} (nested), unwrap it."""
    out: list[dict] = []
    for it in items:
        if isinstance(it, dict) and "items" in it and isinstance(it["items"], list) and len(it) == 1:
            out.extend(it["items"])
        else:
            out.append(it)
    return out


@router.post("/import", status_code=201)
async def import_content(
    payload: ImportRequest,
    session: AsyncSession = Depends(get_session),
    request: Request = None,
    token: TokenPayload = Depends(resolve_token),
):
    """Create many items at once. Admin-only + audited.

    Accepts a JSON array for the given resource_type. Each item is validated
    and created with the same rules as the single-create endpoints.
    """
    rt = payload.resource_type
    items = _coerce_items(payload.items)

    # Validate every item up-front (dry-run) so we never partially create and
    # then roll back the whole transaction. Invalid items are skipped and
    # counted; valid ones are all created together.
    valid: list[dict] = []
    skipped = 0
    for raw in items:
        try:
            if rt == "questions":
                q = QuestionCreate.model_validate(raw)
                _validate_options(q.options)
            elif rt == "viva":
                VivaCreate.model_validate(raw)
            elif rt == "flashcards":
                FlashcardCreate.model_validate(raw)
            elif rt == "practicals":
                PracticalCreate.model_validate(raw)
            else:
                skipped += 1
                continue
            valid.append(raw)
        except Exception:
            skipped += 1

    created_ids: list[int] = []
    for raw in valid:
        if rt == "questions":
            q = QuestionCreate.model_validate(raw)
            obj = Question(
                subject_slug=q.subject_slug, topic_slug=q.topic_slug, stem=q.stem,
                explanation=q.explanation, reference=q.reference, difficulty=q.difficulty,
                learning_objective=q.learning_objective, reviewer=q.reviewer,
                image_url=q.image_url, qtype=q.qtype, is_published=q.is_published,
            )
            session.add(obj)
            await session.flush()
            for i, o in enumerate(q.options):
                session.add(QuestionOption(question_id=obj.id, option_text=o.option_text,
                                           is_correct=o.is_correct, sort_order=o.sort_order or i))
        elif rt == "viva":
            v = VivaCreate.model_validate(raw)
            obj = VivaQuestion(
                subject_slug=v.subject_slug, topic_slug=v.topic_slug, prompt=v.prompt,
                model_answer=v.model_answer, key_points=v.key_points,
                difficulty=v.difficulty, is_published=v.is_published,
            )
            session.add(obj)
        elif rt == "flashcards":
            f = FlashcardCreate.model_validate(raw)
            obj = Flashcard(
                subject_slug=f.subject_slug, topic_slug=f.topic_slug,
                front=f.front, back=f.back, card_type=f.card_type,
            )
            session.add(obj)
        elif rt == "practicals":
            p = PracticalCreate.model_validate(raw)
            obj = Practical(
                subject_slug=p.subject_slug, topic_slug=p.topic_slug, title=p.title,
                objective=p.objective, requirements=p.requirements, principle=p.principle,
                preparation=p.preparation, observation=p.observation,
                interpretation=p.interpretation, common_mistakes=p.common_mistakes,
                safety_notes=p.safety_notes, clinical_significance=p.clinical_significance,
                reference_text=p.reference_text, video_url=p.video_url,
                is_published=p.is_published,
            )
            session.add(obj)
            await session.flush()
            for i, s in enumerate(p.steps):
                session.add(PracticalStep(practical_id=obj.id, step_text=s.step_text,
                                          observation=s.observation, position=s.position or i))

        await session.flush()
        created_ids.append(obj.id)

    if created_ids:
        await record_audit(
            session, action=f"{rt}.import", actor_email=token.email,
            target_type=rt, detail=f"created={len(created_ids)} skipped={skipped}",
            ip_address=client_ip(request),
        )
        await session.commit()

    return {
        "resource_type": rt,
        "created": len(created_ids),
        "skipped": skipped,
        "ids": created_ids,
    }
