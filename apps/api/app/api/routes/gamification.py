"""Gamification endpoints (streak / XP / badges) — per authenticated user."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_user
from app.core.gamification import get_or_update
from app.db.session import get_session
from app.models.user import User

router = APIRouter(prefix="/gamification", tags=["gamification"])


@router.get("/summary")
async def summary(
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_db_user),
):
    return await get_or_update(session, user)
