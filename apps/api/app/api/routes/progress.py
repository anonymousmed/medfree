"""User progress endpoints (scoped to the authenticated user).

Everything here is derived from REAL, recorded study activity — no fabricated
numbers. The frontend Progress page reads ``GET /progress/overview``, which
aggregates actual quiz attempts, viva attempts, topic progress, streaks/XP and
measured time on site / reading time. Time is captured by the client sending
heartbeats to ``POST /progress/track``, which we persist as analytics events.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_user
from app.core.gamification import get_or_update
from app.db.session import get_session
from app.models.analytics import AnalyticsEvent
from app.models.practice import Question
from app.models.progress import FlashcardReview, QuizAttempt, UserProgress, VivaAttempt
from app.models.subject import Topic
from app.models.user import User

router = APIRouter(prefix="/progress", tags=["progress"])


# --------------------------------------------------------------------------- #
# Tracking heartbeat (time on site / reading time)
# --------------------------------------------------------------------------- #
class TrackProgressRequest(BaseModel):
    kind: str = Field(..., pattern="^(site|reading)$")
    seconds: int = Field(..., ge=1, le=3600)
    subject_slug: str | None = None
    resource_id: int | None = None
    path: str | None = None


@router.post("/track", status_code=201)
async def track_activity(
    payload: TrackProgressRequest,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_db_user),
):
    """Record a slice of active time (browsing the site or reading a book/PDF).
    Persisted as an analytics event so it can be aggregated honestly."""
    session.add(
        AnalyticsEvent(
            user_id=user.id,
            event_type="study_time",
            path=payload.path,
            source="web",
            meta=json.dumps(
                {
                    "seconds": payload.seconds,
                    "kind": payload.kind,
                    "subject_slug": payload.subject_slug,
                    "resource_id": payload.resource_id,
                }
            ),
        )
    )
    await session.commit()
    return {"ok": True, "kind": payload.kind, "seconds": payload.seconds}


# --------------------------------------------------------------------------- #
# Real overview for the Progress page
# --------------------------------------------------------------------------- #
class SubjectMastery(BaseModel):
    subject_slug: str
    attempts: int
    correct: int
    accuracy: float


class WeakArea(BaseModel):
    topic_slug: str
    accuracy: float | None = None
    mastery: float | None = None
    note: str


class ProgressOverview(BaseModel):
    streak: int
    longest_streak: int
    xp: int
    level: int
    quiz_attempts: int
    quiz_correct: int
    quiz_accuracy: float
    viva_attempts: int
    topics_started: int
    topics_completed: int
    flashcards_due: int
    time_on_site_seconds: int
    reading_seconds: int
    subject_mastery: list[SubjectMastery]
    weak_areas: list[WeakArea]


def _meta_field(raw: str | None, key: str):
    if not raw:
        return None
    try:
        return json.loads(raw).get(key)
    except Exception:
        return None


@router.get("/overview", response_model=ProgressOverview)
async def overview(
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_db_user),
):
    # Streak / XP / badges (recomputed from real activity in the gamification engine)
    g = await get_or_update(session, user)

    # Quiz
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

    # Viva / topics / flashcards due
    viva = (
        await session.execute(
            select(func.count()).select_from(VivaAttempt).where(VivaAttempt.user_id == user.id)
        )
    ).scalar() or 0
    started = (
        await session.execute(
            select(func.count()).select_from(UserProgress).where(UserProgress.user_id == user.id)
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

    # Time on site + reading (from study_time heartbeats)
    events = (
        await session.execute(
            select(AnalyticsEvent.meta).where(
                AnalyticsEvent.user_id == user.id,
                AnalyticsEvent.event_type == "study_time",
            )
        )
    ).scalars().all()
    time_on_site = 0
    reading = 0
    for m in events:
        secs = _meta_field(m, "seconds")
        kind = _meta_field(m, "kind")
        if isinstance(secs, (int, float)):
            if kind == "reading":
                reading += int(secs)
            else:
                time_on_site += int(secs)

    # Per-subject accuracy from real quiz attempts
    subject_rows = await session.execute(
        select(
            Question.subject_slug,
            func.count(QuizAttempt.id),
            func.sum(case((QuizAttempt.is_correct.is_(True), 1), else_=0)),
        )
        .select_from(QuizAttempt)
        .join(Question, Question.id == QuizAttempt.question_id)
        .where(QuizAttempt.user_id == user.id)
        .group_by(Question.subject_slug)
    )
    subject_mastery = [
        SubjectMastery(
            subject_slug=slug,
            attempts=int(n),
            correct=int(c or 0),
            accuracy=round((int(c or 0) / int(n)) * 100, 1) if n else 0.0,
        )
        for slug, n, c in subject_rows.all()
    ]

    # Weak areas: low quiz accuracy per topic, and low self-reported mastery.
    weak: dict[str, WeakArea] = {}
    topic_rows = await session.execute(
        select(
            Question.topic_slug,
            func.count(QuizAttempt.id),
            func.sum(case((QuizAttempt.is_correct.is_(True), 1), else_=0)),
        )
        .select_from(QuizAttempt)
        .join(Question, Question.id == QuizAttempt.question_id)
        .where(QuizAttempt.user_id == user.id, Question.topic_slug.is_not(None))
        .group_by(Question.topic_slug)
    )
    for slug, n, c in topic_rows.all():
        if not slug:
            continue
        acc = round((int(c or 0) / int(n)) * 100, 1) if n else 0.0
        if acc < 50:
            weak[slug] = WeakArea(topic_slug=slug, accuracy=acc, note="Revise")

    progress_rows = (
        await session.execute(
            select(UserProgress).where(
                UserProgress.user_id == user.id, UserProgress.topic_slug.is_not(None)
            )
        )
    ).scalars().all()
    for p in progress_rows:
        if p.mastery < 40 and p.topic_slug not in weak:
            weak[p.topic_slug] = WeakArea(
                topic_slug=p.topic_slug, mastery=p.mastery, note="Review"
            )

    return ProgressOverview(
        streak=g["streak"]["current"],
        longest_streak=g["streak"]["longest"],
        xp=g["xp"],
        level=g["level"],
        quiz_attempts=attempts,
        quiz_correct=correct,
        quiz_accuracy=round((correct / attempts) * 100, 1) if attempts else 0.0,
        viva_attempts=viva,
        topics_started=started,
        topics_completed=completed,
        flashcards_due=due,
        time_on_site_seconds=time_on_site,
        reading_seconds=reading,
        subject_mastery=subject_mastery,
        weak_areas=list(weak.values()),
    )


# --------------------------------------------------------------------------- #
# Existing per-topic progress endpoints
# --------------------------------------------------------------------------- #
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
