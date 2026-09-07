"""Auth is primarily handled by Supabase Auth on the frontend.

The backend exposes identity introspection (``/api/auth/me``) by verifying the
bearer token, plus a lightweight local-user provisioning endpoint for the MVP.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_db_user, resolve_token
from app.core.auth import TokenPayload
from app.core.config import settings
from app.core.security import rate_limit
from app.schemas.auth import TokenIdentity, UserRead

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/me", response_model=UserRead)
async def me(user=Depends(get_db_user)) -> UserRead:
    return UserRead(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        avatar_url=user.avatar_url,
        highest_role=user.highest_role,
    )


@router.get(
    "/identity",
    response_model=TokenIdentity,
    dependencies=[Depends(rate_limit("auth", settings.rate_limit_auth, settings.rate_limit_window))],
)
async def identity(payload: TokenPayload = Depends(resolve_token)) -> TokenIdentity:
    return TokenIdentity(
        sub=payload.sub,
        email=payload.email,
        role=payload.role,
        is_superuser=payload.is_superuser,
    )
