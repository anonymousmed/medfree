"""Resource API — the RBAC enforcement point for ADMIN-ONLY upload (mandate #6/#7).

Public read is allowed when a resource is published/visible. Direct uploads are
guarded by ``require_admin`` which returns **403 Forbidden** for students and
contributors. Contributor submissions go through ``/resources/submit`` and only
create a review record — they are never published directly.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin, resolve_token
from app.core.auth import TokenPayload
from app.db.session import get_session
from app.models.content import License, Resource
from app.schemas.resource import ResourceRead, ResourceSubmissionRequest, ResourceUploadRequest

router = APIRouter(prefix="/resources", tags=["resources"])


@router.get("", response_model=list[ResourceRead])
async def list_resources(session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(Resource)
        .where(
            Resource.visibility == "public",
            Resource.review_status == "published",
        )
        .limit(100)
    )
    return result.scalars().all()


@router.get("/{resource_id}", response_model=ResourceRead)
async def get_resource(resource_id: int, session: AsyncSession = Depends(get_session)):
    row = (
        await session.execute(
            select(Resource).where(Resource.id == resource_id, Resource.visibility == "public")
        )
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Resource not found")
    return row


@router.post(
    "/upload",
    response_model=ResourceRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
)
async def upload_resource(
    payload: ResourceUploadRequest,
    session: AsyncSession = Depends(get_session),
):
    """ADMIN-ONLY. Students/contributors get 403 Forbidden (enforced in deps)."""
    if payload.rights_status == "review_required":
        raise HTTPException(
            status_code=422,
            detail="Cannot publish a resource with rights_status=review_required",
        )

    license_row = None
    if payload.license_name:
        license_row = (
            await session.execute(select(License).where(License.name == payload.license_name))
        ).scalar_one_or_none()

    resource = Resource(
        title=payload.title,
        resource_type=payload.resource_type,
        creator=payload.creator,
        publisher=payload.publisher,
        source_url=payload.source_url,
        local_storage_key=payload.storage_key,
        license_id=license_row.id if license_row else None,
        rights_status=payload.rights_status,
        ai_usage_status=payload.ai_usage_status,
        attribution_text=payload.attribution_text,
        visibility=payload.visibility,
        review_status=(
            "published" if payload.visibility == "public" else "draft"
        ),
        medical_review_status="approved",
        verified_by="admin",
    )
    session.add(resource)
    await session.commit()
    await session.refresh(resource)
    return resource


@router.post(
    "/submit",
    response_model=ResourceRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(resolve_token)],
)
async def submit_resource(
    payload: ResourceSubmissionRequest,
    session: AsyncSession = Depends(get_session),
    token: TokenPayload = Depends(resolve_token),
):
    """Contributor submission — enters review, is NEVER auto-published.

    Returns a resource with review_status=draft and visibility=private.
    A genuine submission → moderation → review workflow can be layered on top.
    """
    resource = Resource(
        title=payload.title,
        resource_type=payload.resource_type,
        local_storage_key=payload.storage_key,
        rights_status="review_required",
        review_status="draft",
        visibility="private",
        verified_by=token.email or token.sub,
    )
    session.add(resource)
    await session.commit()
    await session.refresh(resource)
    return resource
