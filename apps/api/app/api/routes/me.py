"""Per-user learning utilities: bookmarks, notes + progress shortcut.

All routes are scoped to the authenticated user (server-side persistence).
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_user
from app.db.session import get_session
from app.models.progress import Bookmark, Note
from app.models.user import User
from app.schemas.learning import BookmarkCreate, BookmarkRead, NoteCreate, NoteRead, NoteUpdate

router = APIRouter(prefix="/me", tags=["me"])


# --- Profile (spec §18) --------------------------------------------------------
class ProfileUpdate(BaseModel):
    display_name: str | None = None
    course: str | None = None
    year_of_study: str | None = None
    university: str | None = None
    country: str | None = None
    preferred_language: str | None = None
    study_goal: str | None = None


@router.get("/profile")
async def get_profile(
    session: AsyncSession = Depends(get_session), user: User = Depends(get_db_user)
):
    return {
        "id": user.id,
        "display_name": user.display_name,
        "avatar_url": user.avatar_url,
        "course": user.course,
        "year_of_study": user.year_of_study,
        "university": user.university,
        "country": user.country,
        "preferred_language": user.preferred_language,
        "study_goal": user.study_goal,
        "email": user.email,
        "highest_role": user.highest_role,
    }


@router.patch("/profile", response_model=ProfileUpdate)
async def update_profile(
    payload: ProfileUpdate,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_db_user),
):
    changes = payload.model_dump(exclude_unset=True)
    for k, v in changes.items():
        if hasattr(user, k):
            setattr(user, k, v)
    await session.commit()
    await session.refresh(user)
    return ProfileUpdate(**changes)


# --- Bookmarks ---------------------------------------------------------------
@router.get("/bookmarks", response_model=list[BookmarkRead])
async def list_bookmarks(
    session: AsyncSession = Depends(get_session), user: User = Depends(get_db_user)
):
    result = await session.execute(
        select(Bookmark).where(Bookmark.user_id == user.id).order_by(Bookmark.id.desc()).limit(100)
    )
    return list(result.scalars().all())


@router.post("/bookmarks", response_model=BookmarkRead, status_code=status.HTTP_201_CREATED)
async def add_bookmark(
    payload: BookmarkCreate,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_db_user),
):
    row = Bookmark(
        user_id=user.id,
        target_type=payload.target_type,
        target_id=payload.target_id,
        target_slug=payload.target_slug,
        title=payload.title,
        note=payload.note,
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return row


@router.delete("/bookmarks/{bookmark_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bookmark(
    bookmark_id: int,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_db_user),
):
    row = (
        await session.execute(
            select(Bookmark).where(Bookmark.id == bookmark_id, Bookmark.user_id == user.id)
        )
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Bookmark not found")
    await session.delete(row)
    await session.commit()


# --- Notes -------------------------------------------------------------------
@router.get("/notes", response_model=list[NoteRead])
async def list_notes(
    session: AsyncSession = Depends(get_session), user: User = Depends(get_db_user)
):
    result = await session.execute(
        select(Note).where(Note.user_id == user.id).order_by(Note.id.desc()).limit(100)
    )
    return list(result.scalars().all())


@router.post("/notes", response_model=NoteRead, status_code=status.HTTP_201_CREATED)
async def add_note(
    payload: NoteCreate,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_db_user),
):
    row = Note(
        user_id=user.id,
        target_type=payload.target_type,
        target_id=payload.target_id,
        target_slug=payload.target_slug,
        body=payload.body,
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return row


@router.patch("/notes/{note_id}", response_model=NoteRead)
async def update_note(
    note_id: int,
    payload: NoteUpdate,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_db_user),
):
    row = (
        await session.execute(select(Note).where(Note.id == note_id, Note.user_id == user.id))
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Note not found")
    row.body = payload.body
    if payload.is_pinned is not None:
        row.is_pinned = payload.is_pinned
    await session.commit()
    await session.refresh(row)
    return row


@router.delete("/notes/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_note(
    note_id: int,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_db_user),
):
    row = (
        await session.execute(select(Note).where(Note.id == note_id, Note.user_id == user.id))
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Note not found")
    await session.delete(row)
    await session.commit()
