"""Admin API — Admin-only routes. Guarded by ``require_admin`` at the backend.

Covers: stats, user management, resource review workflow, versioning, and the
Atlas model management entry points (admin-only). All routes are behind
``require_admin`` (content_admin / super_admin), so students/contributors get
403 at the dependency layer — never only via hidden UI.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import require_admin, resolve_token
from app.core.auth import TokenPayload
from app.core.security import client_ip, record_audit
from app.db.session import get_session
from app.models.atlas import (
    AnatomicalRegion,
    AnatomicalStructure,
    AtlasAnnotation,
    AtlasModel,
    AtlasModelPart,
)
from app.models.content import (
    License,
    Resource,
    ResourceVersion,
    REVIEW_APPROVED,
    REVIEW_PUBLISHED,
    RIGHTS_REVIEW_REQUIRED,
)
from app.models.user import User, UserRole
from app.schemas.resource import ResourceRead

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


# --- Stats / dashboard -------------------------------------------------------
@router.get("/stats")
async def stats(session: AsyncSession = Depends(get_session)):
    users = (await session.execute(select(func.count()).select_from(User))).scalar() or 0
    resources = (
        await session.execute(select(func.count()).select_from(Resource))
    ).scalar() or 0
    pending_reviews = (
        await session.execute(
            select(func.count())
            .select_from(Resource)
            .where(Resource.review_status.in_(["draft", "pending_rights", "pending_medical_review"]))
        )
    ).scalar() or 0
    return {
        "users": users,
        "resources": resources,
        "pending_reviews": pending_reviews,
    }


# --- Users -------------------------------------------------------------------
class AdminUserRead(BaseModel):
    id: int
    email: str | None = None
    display_name: str | None = None
    is_active: bool
    roles: list[str]


@router.get("/users", response_model=list[AdminUserRead])
async def admin_users(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(User).options(selectinload(User.roles)).limit(200))
    users = result.scalars().all()
    return [
        AdminUserRead(
            id=u.id,
            email=u.email,
            display_name=u.display_name,
            is_active=u.is_active,
            roles=[r.role for r in u.roles],
        )
        for u in users
    ]


class UpdateRoleRequest(BaseModel):
    role: str = Field(..., min_length=1, max_length=50)


@router.post("/users/{user_id}/role", response_model=AdminUserRead)
async def set_user_role(
    user_id: int,
    payload: UpdateRoleRequest,
    session: AsyncSession = Depends(get_session),
    request: Request = None,
    token: TokenPayload = Depends(resolve_token),
):
    user = (await session.execute(select(User).options(selectinload(User.roles)).where(User.id == user_id))).scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    if payload.role not in {r.role for r in user.roles}:
        session.add(UserRole(user_id=user.id, role=payload.role))
        await record_audit(
            session,
            action="user.role_change",
            # ``audit_logs.actor_id`` is an INTEGER FK to users.id; use the local
            # user's integer id. ``token.sub`` is the Supabase UUID and would
            # raise a DB error if passed here.
            actor_id=user.id,
            actor_email=token.email,
            target_type="user",
            target_id=user_id,
            detail=f"Added role {payload.role}",
            ip_address=client_ip(request),
        )
        await session.commit()
        # The dependency session uses expire_on_commit=False, so the just-added
        # role is not visible on the cached User. Expire + reload to return the
        # updated role list in the response.
        session.expire_all()
        user = (
            await session.execute(select(User).options(selectinload(User.roles)).where(User.id == user_id))
        ).scalar_one()
    return AdminUserRead(
        id=user.id, email=user.email, display_name=user.display_name,
        is_active=user.is_active, roles=[r.role for r in user.roles],
    )


# --- Resources / review workflow --------------------------------------------
@router.get("/resources", response_model=list[ResourceRead])
async def admin_resources(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Resource).order_by(Resource.id.desc()).limit(200))
    return list(result.scalars().all())


class ReviewDecision(BaseModel):
    decision: str = Field(..., description="approve | reject | publish")


@router.post("/resources/{resource_id}/review", response_model=ResourceRead)
async def review_resource(
    resource_id: int,
    payload: ReviewDecision,
    session: AsyncSession = Depends(get_session),
    request: Request = None,
    token: TokenPayload = Depends(resolve_token),
):
    """Medical/review workflow. Rejection halts; publishing is blocked for
    review_required rights. Never silently publishes unknown-license content."""
    row = (await session.execute(select(Resource).where(Resource.id == resource_id))).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Resource not found")

    if payload.decision == "approve":
        if row.rights_status == RIGHTS_REVIEW_REQUIRED:
            raise HTTPException(status_code=422, detail="Blocked: rights_status=review_required")
        row.review_status = REVIEW_APPROVED
        row.medical_review_status = "approved"
    elif payload.decision == "reject":
        row.review_status = "rejected"
        row.visibility = "private"
    elif payload.decision == "publish":
        if row.rights_status == RIGHTS_REVIEW_REQUIRED:
            raise HTTPException(status_code=422, detail="Blocked: rights_status=review_required")
        row.review_status = REVIEW_PUBLISHED
        row.visibility = "public"
        row.medical_review_status = "approved"
    else:
        raise HTTPException(status_code=422, detail="Unknown decision")
    await record_audit(
        session,
        action=f"resource.{payload.decision}",
        actor_email=token.email,
        target_type="resource",
        target_id=resource_id,
        detail=f"review_status → {row.review_status}",
        ip_address=client_ip(request),
    )
    await session.commit()
    await session.refresh(row)
    return row


class VersionRequest(BaseModel):
    version_label: str = Field(..., min_length=1)
    storage_key: str | None = None
    checksum: str | None = None
    change_note: str | None = None


@router.post("/resources/{resource_id}/versions", response_model=ResourceRead)
async def version_resource(
    resource_id: int,
    payload: VersionRequest,
    session: AsyncSession = Depends(get_session),
    token: TokenPayload = Depends(resolve_token),
):
    row = (await session.execute(select(Resource).where(Resource.id == resource_id))).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Resource not found")
    session.add(
        ResourceVersion(
            resource_id=row.id,
            version_label=payload.version_label,
            storage_key=payload.storage_key,
            checksum=payload.checksum,
            change_note=payload.change_note,
            created_by=token.email,
        )
    )
    await session.commit()
    await session.refresh(row)
    return row


# --- Atlas model management (admin-only upload) ------------------------------
class AtlasModelIngest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    file_key: str = Field(..., min_length=1)
    format: str = "glb"
    source: str | None = None
    license: str | None = None
    creator: str | None = None
    region_slug: str | None = None


@router.post("/atlas/models", status_code=status.HTTP_201_CREATED)
async def ingest_atlas_model(
    payload: AtlasModelIngest,
    session: AsyncSession = Depends(get_session),
    request: Request = None,
    token: TokenPayload = Depends(resolve_token),
):
    if not payload.license:
        raise HTTPException(status_code=422, detail="A license/rights record is required for 3D assets")
    region = None
    if payload.region_slug:
        region = (
            await session.execute(select(AnatomicalRegion).where(AnatomicalRegion.slug == payload.region_slug))
        ).scalar_one_or_none()
    model = AtlasModel(
        title=payload.title,
        file_key=payload.file_key,
        format=payload.format,
        source=payload.source,
        license=payload.license,
        creator=payload.creator,
        region_id=region.id if region else None,
        review_status="review_required",
        is_published=False,
    )
    session.add(model)
    await record_audit(
        session,
        action="atlas.model_ingest",
        actor_email=token.email,
        target_type="atlas_model",
        detail=f"Model '{payload.title}' ({payload.file_key})",
        ip_address=client_ip(request),
    )
    await session.commit()
    await session.refresh(model)
    return {"id": model.id, "review_status": model.review_status}


class ModelPartIngest(BaseModel):
    model_id: int
    mesh_name: str = Field(..., min_length=1)
    structure_name: str | None = None
    label: str | None = None


@router.post("/atlas/models/{model_id}/parts", status_code=status.HTTP_201_CREATED)
async def ingest_atlas_part(
    model_id: int,
    payload: ModelPartIngest,
    session: AsyncSession = Depends(get_session),
):
    model = (await session.execute(select(AtlasModel).where(AtlasModel.id == model_id))).scalar_one_or_none()
    if model is None:
        raise HTTPException(status_code=404, detail="Model not found")
    structure = None
    if payload.structure_name:
        structure = (
            await session.execute(
                select(AnatomicalStructure).where(AnatomicalStructure.preferred_name == payload.structure_name)
            )
        ).scalar_one_or_none()
    part = AtlasModelPart(
        model_id=model.id,
        mesh_name=payload.mesh_name,
        structure_id=structure.id if structure else None,
    )
    session.add(part)
    if payload.label and structure:
        session.add(
            AtlasAnnotation(model_id=model.id, structure_id=structure.id, label=payload.label)
        )
    await session.commit()
    return {"id": part.id, "structure_id": part.structure_id}
