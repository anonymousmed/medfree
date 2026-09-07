"""Admin content-management (spec §28, §30, §31, §48).

Provides the missing admin CRUD for resources (edit/publish/unpublish/delete),
the review-queue view, ads list, and book management. All behind ``require_admin``.
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
from app.models.content import Author, Book, BookChapter, License, Resource
from app.models.content_platform import Ad
from app.schemas.resource import ResourceRead

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


# --- Resource edit / delete ----------------------------------------------------
class ResourceUpdate(BaseModel):
    title: str | None = None
    resource_type: str | None = None
    creator: str | None = None
    publisher: str | None = None
    source_url: str | None = None
    rights_status: str | None = None
    ai_usage_status: str | None = None
    attribution_text: str | None = None
    visibility: str | None = None
    review_status: str | None = None


@router.patch("/resources/{resource_id}", response_model=ResourceRead)
async def update_resource(
    resource_id: int,
    payload: ResourceUpdate,
    session: AsyncSession = Depends(get_session),
    token: TokenPayload = Depends(resolve_token),
):
    row = (
        await session.execute(select(Resource).where(Resource.id == resource_id))
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Resource not found")
    changes = payload.model_dump(exclude_unset=True)
    for k, v in changes.items():
        if hasattr(row, k) and k != "id":
            setattr(row, k, v)
    await record_audit(session, action="resource.edit", actor_email=token.email,
                       target_type="resource", target_id=resource_id,
                       detail=", ".join(changes.keys()))
    await session.commit()
    await session.refresh(row)
    return row


@router.delete("/resources/{resource_id}", status_code=204)
async def delete_resource(
    resource_id: int,
    session: AsyncSession = Depends(get_session),
    token: TokenPayload = Depends(resolve_token),
):
    row = (
        await session.execute(select(Resource).where(Resource.id == resource_id))
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Resource not found")
    row.is_active = False
    row.visibility = "private"
    await record_audit(session, action="resource.archive", actor_email=token.email,
                       target_type="resource", target_id=resource_id)
    await session.commit()
    return None


# --- Review queue ----------------------------------------------------------------
@router.get("/reviews")
async def review_queue(session: AsyncSession = Depends(get_session)):
    rows = (
        await session.execute(
            select(Resource)
            .where(Resource.review_status.in_(["draft", "pending_rights", "pending_medical_review", "approved"]))
            .order_by(Resource.id.desc())
            .limit(200)
        )
    ).scalars().all()
    return [
        {
            "id": r.id, "title": r.title, "resource_type": r.resource_type,
            "rights_status": r.rights_status, "review_status": r.review_status,
            "medical_review_status": r.medical_review_status, "visibility": r.visibility,
            "ai_usage_status": r.ai_usage_status,
        }
        for r in rows
    ]


# --- Ads list (admin) -------------------------------------------------------------
@router.get("/ads")
async def admin_ads(session: AsyncSession = Depends(get_session)):
    rows = (await session.execute(select(Ad).order_by(Ad.id.desc()).limit(200))).scalars().all()
    return [
        {
            "id": a.id, "placement": a.placement, "title": a.title,
            "target_url": a.target_url, "campaign_id": a.campaign_id,
            "priority": a.priority, "is_active": a.is_active,
            "start_at": a.start_at.isoformat() if a.start_at else None,
            "end_at": a.end_at.isoformat() if a.end_at else None,
        }
        for a in rows
    ]


# --- Book management ----------------------------------------------------------------
class BookCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=300)
    author_name: str | None = None
    edition: str | None = None
    publisher: str | None = None
    isbn: str | None = None
    year: int | None = None
    subject_slug: str | None = None


@router.post("/books", status_code=201)
async def create_book(
    payload: BookCreate,
    session: AsyncSession = Depends(get_session),
    token: TokenPayload = Depends(resolve_token),
):
    author = None
    if payload.author_name:
        author = (
            await session.execute(select(Author).where(Author.name == payload.author_name))
        ).scalar_one_or_none()
        if author is None:
            author = Author(name=payload.author_name)
            session.add(author)
            await session.flush()
    book = Book(
        title=payload.title, author_id=author.id if author else None,
        edition=payload.edition, publisher=payload.publisher, isbn=payload.isbn,
        year=payload.year, subject_slug=payload.subject_slug,
    )
    session.add(book)
    await record_audit(session, action="book.create", actor_email=token.email,
                       target_type="book", detail=f"title='{payload.title}'")
    await session.commit()
    await session.refresh(book)
    return {"id": book.id, "title": book.title}


@router.delete("/books/{book_id}", status_code=204)
async def delete_book(
    book_id: int,
    session: AsyncSession = Depends(get_session),
    token: TokenPayload = Depends(resolve_token),
):
    book = (await session.execute(select(Book).where(Book.id == book_id))).scalar_one_or_none()
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    await session.delete(book)
    await record_audit(session, action="book.delete", actor_email=token.email,
                       target_type="book", target_id=book_id)
    await session.commit()
    return None
