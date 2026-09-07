"""MEDFREE FastAPI backend entrypoint.

Run locally:  uvicorn app.main:app --reload
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings


class SecurityHeadersMiddleware:
    """Add basic security headers (CSP, X-Content-Type-Options, etc.).

    Kept as a lightweight middleware so headers apply to every response without
    per-route ceremony. Content-Security-Policy is intentionally permissive (a
    strict policy can break the embedded Atlas/3D and media), but the other
    headers are hardened by default.
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                additions = {
                    b"x-content-type-options": b"nosniff",
                    b"x-frame-options": b"SAMEORIGIN",
                    b"referrer-policy": b"strict-origin-when-cross-origin",
                    b"x-xss-protection": b"1; mode=block",
                    b"permissions-policy": (
                        b"camera=(), microphone=(), geolocation=()"
                    ),
                    b"cross-origin-opener-policy": b"same-origin",
                }
                for k, v in additions.items():
                    headers.append((k, v))
                message["headers"] = headers
            await send(message)

        await self.app(scope, receive, send_wrapper)


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="MEDFREE — Human Atlas-first digital medical university (backend)",
        docs_url="/docs" if settings.environment != "production" else None,
        redoc_url=None,
        openapi_url="/openapi.json",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    if settings.security_headers:
        app.add_middleware(SecurityHeadersMiddleware)

    app.include_router(api_router, prefix=settings.api_v1_prefix)

    @app.get("/")
    async def root():
        return {"service": settings.app_name, "docs": "/docs", "health": "/api/health"}

    return app


app = create_app()
