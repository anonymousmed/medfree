"""Object-storage uploads (spec §50, §63). ADMIN-ONLY at the API layer.

Flow:
 1. Client (authorized admin) calls ``POST /storage/presign`` with filename +
    resource_type → receives ``{ storage_key, upload_url }``.
 2. Client PUTs the bytes to ``upload_url`` (S3 presigned, or a local/dev target).
 3. Client calls ``POST /storage/confirm`` with the same ``storage_key`` plus
    metadata → validates the type (file-type allowlist), records the resource
    metadata + audit log, returns the created resource.

Public ``GET /storage/{key}`` serves stored bytes (local driver) or redirects to
a signed URL (S3). Only approved/public content is exposed via the library routes.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin, resolve_token
from app.core.auth import TokenPayload
from app.core.config import settings
from app.core.security import client_ip, record_audit
from app.core.storage import get_storage, new_storage_key
from app.db.session import get_session
from app.models.content import License, Resource
from app.schemas.resource import ResourceRead
from app.api.routes.security import guess_content_type, validate_upload_type

router = APIRouter(prefix="/storage", tags=["storage"])


MAX_UPLOAD_BYTES = max(1, settings.max_upload_mb) * 1024 * 1024


class PresignRequest(BaseModel):
    filename: str = Field(..., min_length=1, max_length=200)
    resource_type: str = Field(..., min_length=1, max_length=60)
    size_bytes: int | None = Field(default=None, ge=0)
    content_type: str | None = Field(default=None, max_length=120)


class ConfirmUpload(BaseModel):
    storage_key: str = Field(..., min_length=1)
    filename: str = Field(..., min_length=1, max_length=200)
    resource_type: str = Field(..., min_length=1, max_length=60)
    title: str = Field(..., min_length=1, max_length=300)
    size_bytes: int | None = Field(default=None, ge=0)
    creator: str | None = None
    publisher: str | None = None
    source_url: str | None = None
    license_name: str | None = None
    rights_status: str = "review_required"
    ai_usage_status: str = "unknown"
    attribution_text: str | None = None
    visibility: str = "private"
    description: str | None = None


@router.post(
    "/presign",
    dependencies=[Depends(require_admin)],
)
async def presign(payload: PresignRequest):
    ok, msg = validate_upload_type(payload.filename, payload.resource_type)
    if not ok:
        raise HTTPException(status_code=422, detail=msg)
    if payload.size_bytes is not None and payload.size_bytes > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail=f"File exceeds {settings.max_upload_mb} MB limit")
    storage = get_storage()
    key = new_storage_key(payload.resource_type, payload.filename)
    # Critical for in-browser reading: a PDF must be stored as
    # ``application/pdf`` (not the octet-stream default) so browsers render it
    # inline instead of forcing a download. Prefer the client-supplied type,
    # otherwise derive it from the filename; surface it back so the client PUTs
    # the exact same Content-Type the URL was signed with.
    content_type = payload.content_type or guess_content_type(payload.filename)
    upload_url = storage.presign_upload(key, content_type=content_type)
    return {"storage_key": key, "upload_url": upload_url, "expires_in": 3600, "content_type": content_type}


@router.post(
    "/confirm",
    status_code=201,
    response_model=ResourceRead,
    dependencies=[Depends(require_admin)],
)
async def confirm_upload(
    payload: ConfirmUpload,
    session: AsyncSession = Depends(get_session),
    token: TokenPayload = Depends(resolve_token),
):
    ok, msg = validate_upload_type(payload.filename, payload.resource_type)
    if not ok:
        raise HTTPException(status_code=422, detail=msg)
    if payload.rights_status == "review_required":
        raise HTTPException(
            status_code=422,
            detail="Cannot publish a resource with rights_status=review_required",
        )
    if payload.size_bytes is not None and payload.size_bytes > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail=f"File exceeds {settings.max_upload_mb} MB limit")

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
        review_status=("published" if payload.visibility == "public" else "draft"),
        medical_review_status="approved",
        verified_by=token.email or token.sub,
    )
    session.add(resource)
    await record_audit(
        session, action="resource.upload", actor_email=token.email,
        target_type="resource", detail=f"title='{payload.title}' type='{payload.resource_type}'",
    )
    await session.commit()
    await session.refresh(resource)
    return resource


@router.get("/{storage_key:path}")
async def serve_storage(
    storage_key: str, session: AsyncSession = Depends(get_session)
):
    # Only expose bytes that belong to a PUBLIC, PUBLISHED resource. Private,
    # unlisted, draft or unknown-key content is never served, so unpublished
    # material cannot be fetched by guessing a key. (Keys are UUIDs anyway.)
    res = (
        await session.execute(
            select(Resource).where(Resource.local_storage_key == storage_key)
        )
    ).scalar_one_or_none()
    if res is None or res.visibility != "public" or res.review_status != "published":
        raise HTTPException(status_code=404, detail="File not found")
    storage = get_storage()
    url = storage.get_public_url(storage_key)
    if url and url.startswith("http"):
        return RedirectResponse(url=url)
    try:
        data = storage.get_bytes(storage_key)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
    return Response(content=data, media_type="application/octet-stream")
