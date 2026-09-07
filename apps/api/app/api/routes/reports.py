"""Reporting / error system (spec §36).

Every content page can surface a "Report an error" flow. Student reports go to
an admin review queue. Public submission is anonymous-friendly, rate-limited,
and never auto-resolves anything.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import bearer_scheme, require_admin
from app.core.auth import auth_provider
from app.core.security import rate_limit, record_audit
from app.db.session import get_session
from app.models.report import REPORT_CATEGORIES, Report
from app.models.user import User

router = APIRouter(tags=["reports"])


class SubmitReport(BaseModel):
    target_type: str = Field(..., min_length=1, max_length=40)
    target_id: int | None = None
    target_slug: str | None = None
    category: str
    title: str | None = None
    detail: str | None = None


@router.post(
    "/resources/report",
    status_code=201,
    dependencies=[Depends(rate_limit("report", 5, 300))],
)
async def submit_report(
    payload: SubmitReport,
    session: AsyncSession = Depends(get_session),
    credentials: object | None = Depends(bearer_scheme),
):
    if payload.category not in REPORT_CATEGORIES:
        raise HTTPException(status_code=422, detail="Unknown report category")

    # Anonymous-friendly: capture the reporter only when a valid token is present.
    reporter = None
    try:
        if credentials is not None and getattr(credentials, "credentials", None):
            token = auth_provider().verify(credentials.credentials)
            user = (
                await session.execute(select(User).where(User.supabase_id == token.sub))
            ).scalar_one_or_none()
            reporter = user.id if user else None
    except Exception:
        reporter = None

    rep = Report(
        reporter_id=reporter,
        target_type=payload.target_type,
        target_id=payload.target_id,
        target_slug=payload.target_slug,
        category=payload.category,
        title=payload.title,
        detail=payload.detail,
        status="open",
    )
    session.add(rep)
    await session.commit()
    return {"id": rep.id, "status": "open", "message": "Thank you — we'll review this."}


# --- Admin review queue --------------------------------------------------------
admin_router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


@admin_router.get("/reports")
async def list_reports(
    session: AsyncSession = Depends(get_session),
    status: str | None = None,
    limit: int = 100,
):
    stmt = select(Report).order_by(Report.id.desc()).limit(min(limit, 500))
    if status:
        stmt = stmt.where(Report.status == status)
    rows = (await session.execute(stmt)).scalars().all()
    return [
        {
            "id": r.id, "target_type": r.target_type, "target_id": r.target_id,
            "target_slug": r.target_slug, "category": r.category, "title": r.title,
            "detail": r.detail, "status": r.status, "handled_by": r.handled_by,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]


class ResolveReport(BaseModel):
    status: str = Field(..., pattern=r"^(open|under_review|resolved|dismissed)$")
    resolution: str | None = None


@admin_router.patch("/reports/{report_id}")
async def resolve_report(
    report_id: int,
    payload: ResolveReport,
    session: AsyncSession = Depends(get_session),
):
    rep = (
        await session.execute(select(Report).where(Report.id == report_id))
    ).scalar_one_or_none()
    if rep is None:
        raise HTTPException(status_code=404, detail="Report not found")
    rep.status = payload.status
    if payload.status in ("resolved", "dismissed"):
        rep.resolution = payload.resolution
    await record_audit(session, action="report.resolve", target_type="report",
                       target_id=report_id, detail=f"status={payload.status}")
    await session.commit()
    return {"id": rep.id, "status": rep.status}
