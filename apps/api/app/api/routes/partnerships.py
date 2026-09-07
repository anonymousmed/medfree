"""Partnerships (Step 20).

Public:
- ``GET /partners``            — active, approved partner directory (institutions
  + faculty + student groups).
- ``POST /partners/interest``  — submit a partnership interest (queued for review).

Admin:
- ``GET /admin/partners``, ``POST /admin/partners`` (create an institution)
- ``PATCH /admin/partners/{id}`` (edit / feature / activate)
- ``GET /admin/partnership-requests``, ``PATCH /admin/partnership-requests/{id}``
  (accept / decline / add notes)

No visitor-submitted interest is ever auto-published; it enters the review queue.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin
from app.db.session import get_session
from app.models.partnership import Institution, PartnershipRequest

router = APIRouter(tags=["partnerships"])


class PartnershipInterest(BaseModel):
    organization_type: str = "medical_college"
    organization_name: str = Field(..., min_length=2, max_length=300)
    contact_name: str = Field(..., min_length=2, max_length=200)
    contact_email: str = Field(..., min_length=3, max_length=255)
    contact_phone: str | None = None
    goal: str | None = None
    message: str | None = None


class AdminInstitutionCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=300)
    kind: str = "medical_college"
    country: str | None = None
    region: str | None = None
    website: str | None = None
    contact_email: str | None = None
    description: str | None = None
    logo_key: str | None = None
    is_featured: bool = False


@router.get("/partners")
async def partner_directory(session: AsyncSession = Depends(get_session)):
    rows = (
        await session.execute(
            select(Institution)
            .where(Institution.is_active.is_(True))
            .order_by(Institution.is_featured.desc(), Institution.id.desc())
            .limit(200)
        )
    ).scalars().all()
    return [
        {
            "id": r.id,
            "name": r.name,
            "kind": r.kind,
            "country": r.country,
            "region": r.region,
            "website": r.website,
            "contact_email": r.contact_email,
            "description": r.description,
            "logo_key": r.logo_key,
            "is_featured": r.is_featured,
        }
        for r in rows
    ]


@router.post("/partners/interest", status_code=201)
async def submit_interest(
    payload: PartnershipInterest,
    session: AsyncSession = Depends(get_session),
):
    req = PartnershipRequest(
        organization_type=payload.organization_type,
        organization_name=payload.organization_name,
        contact_name=payload.contact_name,
        contact_email=payload.contact_email,
        contact_phone=payload.contact_phone,
        goal=payload.goal,
        message=payload.message,
        status="pending",
    )
    session.add(req)
    await session.commit()
    return {"id": req.id, "status": "pending", "message": "Thanks! We'll review your partnership interest."}


# --- Admin --------------------------------------------------------------------
admin_router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


@admin_router.get("/partners")
async def admin_partners(session: AsyncSession = Depends(get_session)):
    rows = (
        await session.execute(select(Institution).order_by(Institution.id.desc()).limit(300))
    ).scalars().all()
    return [
        {
            "id": r.id, "name": r.name, "kind": r.kind, "country": r.country,
            "website": r.website, "is_featured": r.is_featured, "is_active": r.is_active,
        }
        for r in rows
    ]


@admin_router.post("/partners", status_code=201)
async def create_institution(
    payload: AdminInstitutionCreate,
    session: AsyncSession = Depends(get_session),
):
    inst = Institution(
        name=payload.name,
        kind=payload.kind,
        country=payload.country,
        region=payload.region,
        website=payload.website,
        contact_email=payload.contact_email,
        description=payload.description,
        logo_key=payload.logo_key,
        is_featured=payload.is_featured,
    )
    session.add(inst)
    await session.commit()
    await session.refresh(inst)
    return {"id": inst.id, "name": inst.name, "is_active": inst.is_active}


@admin_router.patch("/partners/{partner_id}")
async def update_institution(
    partner_id: int,
    payload: dict,
    session: AsyncSession = Depends(get_session),
):
    inst = (
        await session.execute(select(Institution).where(Institution.id == partner_id))
    ).scalar_one_or_none()
    if inst is None:
        raise HTTPException(status_code=404, detail="Institution not found")
    for k, v in payload.items():
        if hasattr(inst, k) and not k.startswith("id"):
            setattr(inst, k, v)
    await session.commit()
    return {"id": inst.id, "name": inst.name, "is_active": inst.is_active, "is_featured": inst.is_featured}


@admin_router.get("/partnership-requests")
async def partnership_requests(session: AsyncSession = Depends(get_session)):
    rows = (
        await session.execute(
            select(PartnershipRequest).order_by(PartnershipRequest.id.desc()).limit(300)
        )
    ).scalars().all()
    return [
        {
            "id": r.id, "organization_type": r.organization_type,
            "organization_name": r.organization_name, "contact_name": r.contact_name,
            "contact_email": r.contact_email, "goal": r.goal, "message": r.message,
            "status": r.status, "admin_notes": r.admin_notes,
        }
        for r in rows
    ]


@admin_router.patch("/partnership-requests/{request_id}")
async def update_partnership_request(
    request_id: int,
    payload: dict,
    session: AsyncSession = Depends(get_session),
):
    req = (
        await session.execute(select(PartnershipRequest).where(PartnershipRequest.id == request_id))
    ).scalar_one_or_none()
    if req is None:
        raise HTTPException(status_code=404, detail="Request not found")
    for k, v in payload.items():
        if hasattr(req, k) and not k.startswith("id"):
            setattr(req, k, v)
    await session.commit()
    return {"id": req.id, "status": req.status}
