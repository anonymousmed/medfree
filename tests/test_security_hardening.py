"""Regression tests for access-control hardening:
- oversized uploads rejected (413)
- storage serve only exposes public, published resources (404 otherwise)
"""
import os

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.storage import get_storage
from app.models.content import Resource

# Ensure the local driver writes to a throwaway dir during tests.
TEST_STORAGE = "/tmp/medfree_test_storage"


@pytest.fixture(autouse=True)
def _test_storage_dir():
    from app.core import storage as storage_mod

    # Point the cached driver at a temp dir and reset the singleton.
    storage_mod._driver = None
    from app.core.config import settings

    settings.storage_local_root = TEST_STORAGE
    get_storage()
    yield
    storage_mod._driver = None
    try:
        import shutil

        shutil.rmtree(TEST_STORAGE, ignore_errors=True)
    except Exception:
        pass


@pytest.mark.asyncio
async def test_presign_rejects_oversized(client, auth_headers):
    resp = await client.post(
        "/api/storage/presign",
        json={"filename": "big.pdf", "resource_type": "document", "size_bytes": 999 * 1024 * 1024},
        headers=auth_headers("content_admin"),
    )
    assert resp.status_code == 413


@pytest.mark.asyncio
async def test_serve_storage_blocks_private(client, db_engine):
    key = "uploads/test/secret.txt"
    get_storage().put_bytes(key, b"secret")
    async with AsyncSession(db_engine) as s:
        s.add(Resource(
            title="secret", resource_type="document", local_storage_key=key,
            rights_status="review_required", review_status="draft", visibility="private",
        ))
        await s.commit()
    resp = await client.get(f"/api/storage/{key}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_serve_storage_serves_public_published(client, db_engine):
    key = "uploads/test/public.txt"
    get_storage().put_bytes(key, b"hello public")
    async with AsyncSession(db_engine) as s:
        s.add(Resource(
            title="public", resource_type="document", local_storage_key=key,
            rights_status="open_license", review_status="published", visibility="public",
        ))
        await s.commit()
    resp = await client.get(f"/api/storage/{key}")
    assert resp.status_code == 200
    assert resp.text == "hello public"


@pytest.mark.asyncio
async def test_serve_storage_blocks_unknown_key(client, db_engine):
    resp = await client.get("/api/storage/uploads/nope/doesnotexist.txt")
    assert resp.status_code == 404
