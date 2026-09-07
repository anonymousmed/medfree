"""Books & chapters (read). Books are the knowledge/reference layer,
NOT the primary product experience. Direct upload/admin is admin-only.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import get_session
from app.models.content import Book, BookChapter, Resource
from app.schemas.library import (
    AuthorRead,
    BookChapterRead,
    BookDetail,
    BookRead,
)

router = APIRouter(prefix="/books", tags=["books"])


@router.get("", response_model=list[BookRead])
async def list_books(
    subject: str | None = Query(None),
    q: str | None = Query(None),
    limit: int = Query(50, le=100),
    session: AsyncSession = Depends(get_session),
):
    stmt = select(Book)
    if subject:
        stmt = stmt.where(Book.subject_slug == subject)
    if q:
        stmt = stmt.where(Book.title.ilike(f"%{q}%"))
    result = await session.execute(stmt.order_by(Book.title).limit(limit))
    return result.scalars().all()


@router.get("/{book_id}", response_model=BookDetail)
async def get_book(book_id: int, session: AsyncSession = Depends(get_session)):
    row = (
        await session.execute(
            select(Book)
            .options(
                selectinload(Book.author),
                selectinload(Book.resource).selectinload(Resource.license),
                selectinload(Book.chapters),
            )
            .where(Book.id == book_id)
        )
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Book not found")

    res = row.resource

    return BookDetail(
        id=row.id,
        title=row.title,
        edition=row.edition,
        publisher=row.publisher,
        isbn=row.isbn,
        year=row.year,
        subject_slug=row.subject_slug,
        source_url=res.source_url if res else None,
        rights_status=res.rights_status if res else None,
        license_name=res.license.name if res and res.license else None,
        author=(
            AuthorRead(id=a.id, name=a.name, affiliation=a.affiliation, website=a.website)
            if (a := row.author)
            else None
        ),
        chapters=row.chapters,
    )


@router.get("/{book_id}/chapters", response_model=list[BookChapterRead])
async def list_chapters(book_id: int, session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(BookChapter)
        .where(BookChapter.book_id == book_id)
        .order_by(BookChapter.chapter_index)
    )
    return result.scalars().all()
