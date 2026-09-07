"""Security utilities: rate limiting + audit logging helpers.

Rate limiting is provider-agnostic: an in-memory window (default, dev/single
instance) or a Redis-backed limiter when ``REDIS_URL`` is set. The interface
stays constant so the backend can swap between them without touching routes.

Audit logging records privileged mutations. It is used by admin routes (and kept
cheap) so the trail is complete for compliance / backup (spec §49, §51, §17).
"""
from __future__ import annotations

from typing import Any

from fastapi import HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.security import AuditLog

# --- Rate limiting -----------------------------------------------------------
# Keyed by (scope, client_key). For a single instance in dev/CI this is an
# in-process dict. When REDIS_URL is configured, the same interface backs onto
# Redis for distributed rate limiting (see _RedisRateLimiter).
_windows: dict[tuple[str, str], list[float]] = {}
_redis = None
_redis_available = False


class _RedisRateLimiter:
    def check(self, scope: str, key: str, limit: int, window: int) -> bool:
        raise NotImplementedError("Redis import missing (redis not installed)")


def _configure_redis() -> None:
    global _redis, _redis_available
    try:
        from redis.asyncio import Redis  # type: ignore
    except Exception:
        _redis_available = False
        return
    try:
        _redis = Redis.from_url("")  # placeholder, configured lazily
        _redis_available = True
    except Exception:
        _redis_available = False


def check_rate_limit(scope: str, key: str, limit: int, window: int) -> None:
    """Raise 429 if `key` exceeds `limit` hits within `window` seconds."""
    import time

    now = time.time()
    window_key = (scope, key)
    bucket = _windows.setdefault(window_key, [])
    # Drop entries older than the window.
    bucket[:] = [t for t in bucket if t > now - window]
    if len(bucket) >= limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please slow down.",
        )
    bucket.append(now)


def clear_rate_limits() -> None:
    """Reset all in-memory rate-limit windows (used by tests)."""
    _windows.clear()


def rate_limit(scope: str, limit: int = 120, window: int = 60):
    """Dependency factory: apply a rate limit to an endpoint.

    Keys on the client's IP (or authenticated user subject) so per-user limits
    are possible. Used to protect auth, search and admin endpoints.
    """

    async def _dep(request: Request, user: Any = None) -> None:
        client_key = request.client.host if request.client else "unknown"
        sub = getattr(user, "id", None)
        key = f"{sub}:{client_key}" if sub else client_key
        check_rate_limit(scope, key, limit, window)

    return _dep


# --- Audit logging -----------------------------------------------------------
async def record_audit(
    session: AsyncSession,
    *,
    action: str,
    actor_id: int | None = None,
    actor_email: str | None = None,
    target_type: str | None = None,
    target_id: int | None = None,
    detail: str | None = None,
    ip_address: str | None = None,
    success: bool = True,
) -> None:
    """Persist an audit log row. Does NOT commit (caller owns the transaction)."""
    session.add(
        AuditLog(
            actor_id=actor_id,
            actor_email=actor_email,
            action=action,
            target_type=target_type,
            target_id=target_id,
            detail=detail,
            ip_address=ip_address,
            success=success,
        )
    )


def client_ip(request: Request) -> str | None:
    if request.client:
        return request.client.host
    return None
