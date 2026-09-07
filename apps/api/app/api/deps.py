"""FastAPI dependencies: current user resolution + RBAC guards.

RBAC is enforced HERE (backend), not by hiding UI. Mandate #7:
``POST /resources/upload`` returns 403 for students/contributors even if the
frontend never renders an upload button.
"""
from __future__ import annotations

from typing import Any, Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.auth import TokenPayload, auth_provider
from app.db.session import get_session

bearer_scheme = HTTPBearer(auto_error=False)


def resolve_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> TokenPayload:
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return auth_provider().verify(credentials.credentials)


# --- role guard helper -------------------------------------------------------
ROLE_RANK = {
    "student": 0,
    "contributor": 1,
    "reviewer": 2,
    "medical_reviewer": 3,
    "moderator": 4,
    "content_admin": 5,
    "super_admin": 6,
}


def require_min_role(min_role: str) -> Callable[..., Any]:
    """Return a dependency that requires ``role >= min_role`` in the RBAC ladder."""

    async def _guard(
        payload: TokenPayload = Depends(resolve_token),
    ) -> TokenPayload:
        if ROLE_RANK.get(payload.role, 0) < ROLE_RANK.get(min_role, 0):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires role: {min_role}",
            )
        return payload

    return _guard


require_admin = require_min_role("content_admin")
require_super_admin = require_min_role("super_admin")
require_reviewer = require_min_role("reviewer")


# --- session form of the current user ----------------------------------------
async def get_db_user(
    payload: TokenPayload = Depends(resolve_token),
    session: AsyncSession = Depends(get_session),
):
    """Resolve a DB user row for the authenticated subject.

    In the MVP the Supabase ``users`` table is the source of truth; we upsert a
    local ``users`` record on first login. This is a lightweight lookup.
    """
    from app.models.user import User, UserRole

    stmt = select(User).options(selectinload(User.roles)).where(User.supabase_id == payload.sub)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()
    if user is None:
        # Auto-provision a minimal local user record for convenience.
        user = User(
            supabase_id=payload.sub,
            email=payload.email,
            display_name=payload.email,
            is_active=True,
        )
        session.add(user)
        await session.flush()
        session.add(UserRole(user_id=user.id, role=payload.role))
        await session.commit()
        user = (
            await session.execute(
                select(User).options(selectinload(User.roles)).where(User.id == user.id)
            )
        ).scalar_one()
    return user
