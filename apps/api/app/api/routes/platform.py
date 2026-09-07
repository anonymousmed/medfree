"""Ads & Announcements. Public reads return only active items with a valid
schedule; writes are admin-only (enforced at the backend).
"""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin, resolve_token
from app.core.auth import TokenPayload
from app.core.security import client_ip, record_audit
from app.db.session import get_session
from app.models.content_platform import Ad, Announcement

router = APIRouter(tags=["platform"])

# ---------------------------------------------------------------------------
# Public reads (active & in-schedule only)
# ---------------------------------------------------------------------------
@router.get("/ads")
async def active_ad(placement: str = "homepage", session: AsyncSession = Depends(get_session)):
    now = datetime.now(timezone.utc)
    row = (
        await session.execute(
            select(Ad)
            .where(
                Ad.is_active.is_(True),
                Ad.placement == placement,
                (Ad.start_at.is_(None)) | (Ad.start_at <= now),
                (Ad.end_at.is_(None)) | (Ad.end_at >= now),
            )
            .order_by(Ad.priority.desc(), Ad.id.desc())
            .limit(1)
        )
    ).scalar_one_or_none()
    if row is None:
        return None
    return {
        "id": row.id,
        "title": row.title,
        "image_key": row.image_key,
        "target_url": row.target_url,
        "alt_text": row.alt_text,
        "placement": row.placement,
    }


@router.get("/announcements")
async def active_announcement(session: AsyncSession = Depends(get_session)):
    now = datetime.now(timezone.utc)
    rows = (
        await session.execute(
            select(Announcement)
            .where(
                Announcement.is_active.is_(True),
                (Announcement.publish_at.is_(None)) | (Announcement.publish_at <= now),
                (Announcement.expire_at.is_(None)) | (Announcement.expire_at >= now),
            )
            .order_by(Announcement.id.desc())
            .limit(5)
        )
    ).scalars().all()
    return [
        {"id": a.id, "kind": a.kind, "title": a.title, "body": a.body, "link": a.link}
        for a in rows
    ]


# ---------------------------------------------------------------------------
# Admin CRUD (require_admin)
# ---------------------------------------------------------------------------
class AdCreate(BaseModel):
    placement: str = "homepage"
    title: str | None = None
    image_key: str | None = None
    target_url: str | None = None
    alt_text: str | None = None
    advertiser: str | None = None
    campaign_id: str | None = None
    priority: int = 0
    start_at: str | None = None
    end_at: str | None = None
    is_active: bool = True


class AnnouncementCreate(BaseModel):
    kind: str = "system"
    title: str = Field(..., min_length=1, max_length=200)
    body: str | None = None
    link: str | None = None
    publish_at: str | None = None
    expire_at: str | None = None
    is_active: bool = True


def _parse_dt(value: str | None):
    if not value:
        return None
    from datetime import datetime

    return datetime.fromisoformat(value.replace("Z", "+00:00"))


@router.post("/admin/ads", status_code=201, dependencies=[Depends(require_admin)])
async def create_ad(
    payload: AdCreate,
    session: AsyncSession = Depends(get_session),
    request: Request = None,
    token: TokenPayload = Depends(resolve_token),
):
    ad = Ad(
        placement=payload.placement,
        title=payload.title,
        image_key=payload.image_key,
        target_url=payload.target_url,
        alt_text=payload.alt_text,
        advertiser=payload.advertiser,
        campaign_id=payload.campaign_id,
        priority=payload.priority,
        start_at=_parse_dt(payload.start_at),
        end_at=_parse_dt(payload.end_at),
        is_active=payload.is_active,
    )
    session.add(ad)
    await record_audit(
        session,
        action="ad.create",
        actor_email=token.email,
        target_type="ad",
        detail=f"placement={payload.placement} title='{payload.title}'",
        ip_address=client_ip(request),
    )
    await session.commit()
    await session.refresh(ad)
    return {"id": ad.id, "placement": ad.placement, "is_active": ad.is_active}


@router.patch("/admin/ads/{ad_id}", dependencies=[Depends(require_admin)])
async def update_ad(ad_id: int, payload: dict, session: AsyncSession = Depends(get_session)):
    ad = (await session.execute(select(Ad).where(Ad.id == ad_id))).scalar_one_or_none()
    if ad is None:
        raise HTTPException(status_code=404, detail="Ad not found")
    for k, v in payload.items():
        if hasattr(ad, k) and not k.startswith("id"):
            setattr(ad, k, v)
    await session.commit()
    return {"id": ad.id, "is_active": ad.is_active}


@router.delete("/admin/ads/{ad_id}", status_code=204, dependencies=[Depends(require_admin)])
async def delete_ad(ad_id: int, session: AsyncSession = Depends(get_session)):
    ad = (await session.execute(select(Ad).where(Ad.id == ad_id))).scalar_one_or_none()
    if ad is None:
        raise HTTPException(status_code=404, detail="Ad not found")
    await session.delete(ad)
    await session.commit()


@router.post("/admin/announcements", status_code=201, dependencies=[Depends(require_admin)])
async def create_announcement(
    payload: AnnouncementCreate,
    session: AsyncSession = Depends(get_session),
    request: Request = None,
    token: TokenPayload = Depends(resolve_token),
):
    a = Announcement(
        kind=payload.kind,
        title=payload.title,
        body=payload.body,
        link=payload.link,
        publish_at=_parse_dt(payload.publish_at),
        expire_at=_parse_dt(payload.expire_at),
        is_active=payload.is_active,
    )
    session.add(a)
    await record_audit(
        session,
        action="announcement.create",
        actor_email=token.email,
        target_type="announcement",
        detail=f"kind={payload.kind} title='{payload.title}'",
        ip_address=client_ip(request),
    )
    await session.commit()
    await session.refresh(a)
    return {"id": a.id, "kind": a.kind, "title": a.title}
