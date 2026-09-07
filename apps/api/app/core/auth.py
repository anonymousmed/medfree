"""Auth abstraction.

MEDFREE supports pluggable auth providers. The *interface* (a ``TokenPayload``
and a verifier) stays constant so providers can be swapped without touching
the rest of the app.

Providers:
- ``supabase`` : verify Supabase JWT access tokens (recommended for MVP).
- ``mock``     : dev-only, decode a deliberately unsigned payload so local
                 testing works without a real Supabase project.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Protocol

from fastapi import HTTPException, status
import httpx

from app.core.config import settings


@dataclass(frozen=True)
class TokenPayload:
    sub: str
    email: str | None
    role: str
    is_superuser: bool = False


class AuthProvider(Protocol):
    def verify(self, token: str) -> TokenPayload: ...


class MockAuthProvider:
    """Dev-only provider used when ``auth_provider == mock``.

    Decodes a base64url ``{"sub","email","role"}`` payload so that local
    integration tests / local dev can simulate any role. NEVER use in prod.
    """

    def verify(self, token: str) -> TokenPayload:
        if settings.auth_bypass:
            # Allow a fully-insecure default JWT for local dev.
            import base64
            import json

            def _b64decode(payload: str) -> bytes:
                return base64.urlsafe_b64decode(payload + "===")

            header, body, _ = token.split(".")
            _ = json.loads(_b64decode(header))
            data = json.loads(_b64decode(body))
            return TokenPayload(
                sub=str(data.get("sub", "00000000-0000-0000-0000-000000000000")),
                email=data.get("email"),
                role=data.get("role", "student"),
                is_superuser=bool(data.get("is_superuser", False)),
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Mock auth disabled",
        )


class SupabaseAuthProvider:
    """Verify a Supabase JWT.

    Modern Supabase projects sign access tokens with an EC key (ES256) published
    at ``/auth/v1/.well-known/jwks.json`` (or an RSA key), so we validate against
    the project's **JWKS** first. A legacy ``HS256`` token signed with the
    ``SUPABASE_JWT_SECRET`` is accepted as a fallback (older projects). Requires
    ``supabase_url``; falls back to the JWT secret if it is set and JWKS fails.
    """

    def _decode_with_secret(self, token: str) -> dict:
        from jose import jwt

        return jwt.decode(
            token,
            settings.supabase_jwt_secret,
            audience=settings.auth_jwt_audience,
            options={"verify_aud": True},
        )

    def _decode_with_jwks(self, token: str) -> dict:
        from jose import jwt

        jwks_url = f"{settings.supabase_url.rstrip('/')}/auth/v1/.well-known/jwks.json"
        try:
            # Short timeout; we only fetch keys at token-verify time.
            resp = httpx.get(jwks_url, timeout=5.0, follow_redirects=True)
            resp.raise_for_status()
            jwks = resp.json()
            payload = jwt.decode(
                token,
                jwks,
                audience=settings.auth_jwt_audience,
                options={"verify_aud": True},
            )
            return payload
        except Exception:
            # Fall through to the legacy JWT-secret path below.
            raise

    def verify(self, token: str) -> TokenPayload:
        payload: dict | None = None

        # 1) JWKS path (preferred — handles ES256/RS256). Requires supabase_url.
        if settings.supabase_url:
            try:
                payload = self._decode_with_jwks(token)
            except Exception:
                payload = None

        # 2) Legacy HS256 path with the project JWT secret.
        if payload is None and settings.supabase_jwt_secret:
            try:
                payload = self._decode_with_secret(token)
            except Exception:
                payload = None

        if payload is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
            )

        exp = payload.get("exp")
        if exp is not None and exp < int(time.time()):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired",
            )

        # Map Supabase app_metadata.role onto our RBAC roles.
        app_meta = payload.get("app_metadata", {}) or {}
        raw_role = app_meta.get("role") or payload.get("role") or "student"
        role = normalize_role(raw_role)
        is_superuser = role == "super_admin" or bool(app_meta.get("is_superuser"))

        return TokenPayload(
            sub=str(payload.get("sub")),
            email=payload.get("email"),
            role=role,
            is_superuser=is_superuser,
        )


def normalize_role(role: str) -> str:
    """Map any provider role string onto MEDFREE canonical roles."""
    allowed = [
        "student",
        "contributor",
        "reviewer",
        "medical_reviewer",
        "moderator",
        "content_admin",
        "super_admin",
    ]
    r = (role or "student").strip().lower().replace("-", "_").replace(" ", "_")
    return r if r in allowed else "student"


def get_auth_provider() -> AuthProvider:
    if settings.auth_provider == "supabase":
        return SupabaseAuthProvider()
    return MockAuthProvider()


# Singleton-ish provider.
_provider: AuthProvider | None = None


def auth_provider() -> AuthProvider:
    global _provider
    if _provider is None:
        _provider = get_auth_provider()
    return _provider
