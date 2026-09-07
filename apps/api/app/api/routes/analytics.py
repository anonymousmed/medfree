"""Analytics (Step 16).

Lightweight, non-invasive product & learning analytics plus search analytics.

Public/client ingestion:
- ``POST /analytics/events``  — record a product/learning event (anonymous OK).
- ``POST /analytics/search``  — record a search interaction (for search analytics).

Admin (aggregate):
- ``GET /admin/analytics``    — dashboard aggregates (users, activity, searches,
  most-used structures, retention). Computed on demand from existing tables.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin
from app.api.deps import bearer_scheme as _bearer
from app.core.auth import TokenPayload, auth_provider
from app.core.security import rate_limit
from app.db.session import get_session
from app.models.analytics import AnalyticsEvent, SearchEvent
from app.models.atlas import AnatomicalStructure
from app.models.content import Resource
from app.models.progress import QuizAttempt, UserProgress
from app.models.subject import Topic
from app.models.user import User

router = APIRouter(tags=["analytics"])


class TrackEvent(BaseModel):
    event_type: str = Field(..., min_length=1, max_length=60)
    path: str | None = None
    source: str | None = None
    session_id: str | None = None
    meta: dict | None = None


class TrackSearch(BaseModel):
    query: str = Field(..., min_length=1, max_length=300)
    result_count: int = 0
    target_type: str | None = None


@router.post("/analytics/events", status_code=201)
async def track_event(
    payload: TrackEvent,
    session: AsyncSession = Depends(get_session),
    credentials: dict | None = Depends(_bearer),
):
    user_id = None
    if credentials is not None and getattr(credentials, "credentials", None):
        try:
            token = auth_provider().verify(credentials.credentials)
            user = (
                await session.execute(select(User).where(User.supabase_id == token.sub))
            ).scalar_one_or_none()
            user_id = user.id if user else None
        except Exception:
            user_id = None
    session.add(
        AnalyticsEvent(
            user_id=user_id,
            event_type=payload.event_type,
            path=payload.path,
            source=payload.source,
            session_id=payload.session_id,
            meta=json.dumps(payload.meta) if payload.meta else None,
        )
    )
    await session.commit()
    return {"ok": True}


@router.post("/analytics/search", status_code=201)
async def track_search(
    payload: TrackSearch,
    session: AsyncSession = Depends(get_session),
):
    session.add(
        SearchEvent(
            query=payload.query[:300],
            result_count=payload.result_count,
            target_type=payload.target_type,
            is_failed=payload.result_count == 0,
        )
    )
    await session.commit()
    return {"ok": True}


# --- Admin analytics ----------------------------------------------------------
admin_router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


@admin_router.get("/analytics")
async def analytics_overview(
    session: AsyncSession = Depends(get_session),
    period_days: int = 30,
):
    now = datetime.now(timezone.utc)

    total_users = (await session.execute(select(func.count()).select_from(User))).scalar() or 0
    active_events = (
        await session.execute(
            select(func.count(func.distinct(AnalyticsEvent.user_id))).select_from(AnalyticsEvent)
        )
    ).scalar() or 0
    new_users_30d = (
        await session.execute(
            select(func.count()).select_from(User).where(User.created_at >= period_days_dt(period_days))
        )
    ).scalar() or 0
    topics_completed = (
        await session.execute(
            select(func.count()).select_from(UserProgress).where(UserProgress.state == "completed")
        )
    ).scalar() or 0
    quiz_attempts = (await session.execute(select(func.count()).select_from(QuizAttempt))).scalar() or 0
    quiz_correct = (
        await session.execute(
            select(func.count()).select_from(QuizAttempt).where(QuizAttempt.is_correct.is_(True))
        )
    ).scalar() or 0

    # Search analytics: top queries + failed searches.
    top_queries = (
        await session.execute(
            select(SearchEvent.query, func.count(SearchEvent.id).label("n"))
            .group_by(SearchEvent.query)
            .order_by(func.count(SearchEvent.id).desc())
            .limit(10)
        )
    ).all()
    failed_searches = (
        await session.execute(select(func.count()).select_from(SearchEvent).where(SearchEvent.is_failed.is_(True)))
    ).scalar() or 0
    search_volume = (await session.execute(select(func.count()).select_from(SearchEvent))).scalar() or 0

    # Most-used Atlas structures (via atlas-progressing or event metadata).
    top_structures = (
        await session.execute(
            select(AnalyticsEvent.meta, func.count(AnalyticsEvent.id))
            .where(AnalyticsEvent.event_type == "atlas_structure")
            .group_by(AnalyticsEvent.meta)
            .order_by(func.count(AnalyticsEvent.id).desc())
            .limit(8)
        )
    ).all()

    # Most-read topics (by progress rows referencing a topic slug).
    top_topics = (
        await session.execute(
            select(Topic.title, func.count(UserProgress.id))
            .join(UserProgress, UserProgress.topic_slug == Topic.slug, isouter=True)
            .group_by(Topic.title)
            .order_by(func.count(UserProgress.id).desc())
            .limit(8)
        )
    ).all()

    return {
        "period_days": period_days,
        "users": {
            "total": total_users,
            "active": active_events,
            "new_last_30d": new_users_30d,
        },
        "learning": {
            "topics_completed": topics_completed,
            "quiz_attempts": quiz_attempts,
            "quiz_correct": quiz_correct,
            "quiz_accuracy": round((quiz_correct / quiz_attempts) * 100, 1) if quiz_attempts else 0.0,
        },
        "search": {
            "volume": search_volume,
            "failed": failed_searches,
            "top_queries": [{"query": q, "count": n} for q, n in top_queries],
        },
        "atlas": {
            "top_structures": [
                {"structure": meta_text(m), "count": n} for m, n in top_structures
            ],
        },
        "topics": {"most_engaged": [{"title": t, "count": n} for t, n in top_topics]},
    }


def period_days_dt(days: int):
    from datetime import timedelta

    return datetime.now(timezone.utc) - timedelta(days=days)


def meta_text(raw: str | None) -> str:
    if not raw:
        return ""
    try:
        d = json.loads(raw)
        if isinstance(d, dict):
            return str(d.get("structure") or d.get("name") or "")
        return str(d)
    except Exception:
        return raw
