"""Shared test fixtures.

Uses an in-memory SQLite DB and the dev ``mock`` auth provider so integration
tests can simulate any role without a live Supabase project.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# Make ``app`` (the FastAPI package under apps/api) importable.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "apps" / "api"))

# Configure BEFORE importing the app so the Settings singleton picks it up.
os.environ.setdefault("AUTH_PROVIDER", "mock")
os.environ.setdefault("AUTH_BYPASS", "true")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("ENVIRONMENT", "test")

import pytest  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine  # noqa: E402

from app.db.base import Base  # noqa: E402
from app.main import app  # noqa: E402


def _make_token(role: str, sub: str = "test-user", email: str = "t@example.com") -> str:
    """Build a mock JWT-esque token (header.payload.signature) for the mock provider."""
    import base64
    import json

    def enc(obj: dict) -> str:
        return base64.urlsafe_b64encode(json.dumps(obj).encode()).decode().rstrip("=")

    header = enc({"alg": "none", "typ": "JWT"})
    body = enc({"sub": sub, "email": email, "role": role})
    return f"{header}.{body}."


@pytest.fixture
async def db_engine():
    # Use a file-backed SQLite so every session/connection sees the same data.
    import tempfile

    f = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    f.close()
    engine = create_async_engine(f"sqlite+aiosqlite:///{f.name}", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()
    import os

    os.unlink(f.name)


@pytest.fixture
async def client(db_engine):
    session_factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)

    async def _get_session():
        async with session_factory() as s:
            yield s

    app.dependency_overrides = {}

    from app.db.session import get_session as real_get_session  # noqa: E402

    app.dependency_overrides[real_get_session] = _get_session

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides = {}


@pytest.fixture
def auth_headers():
    def _build(role: str) -> dict:
        return {"Authorization": f"Bearer {_make_token(role)}"}

    return _build


@pytest.fixture(autouse=True)
def _clear_rate_limits():
    """Reset the in-memory rate-limit windows between tests so shared buckets
    (keyed on the test client host) don't cause cross-test 429s."""
    from app.core.security import clear_rate_limits

    clear_rate_limits()
    yield
    clear_rate_limits()
