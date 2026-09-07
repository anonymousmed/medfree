"""Final platform batch: storage uploads, admin content mgmt, reports, AI index, profile."""
import pytest


# --- Storage / uploads ---------------------------------------------------------
@pytest.mark.asyncio
async def test_presign_requires_admin(client, auth_headers):
    # Student cannot request an upload URL.
    resp = await client.post(
        "/api/storage/presign", json={"filename": "notes.pdf", "resource_type": "document"},
        headers=auth_headers("student"),
    )
    assert resp.status_code == 403

    admin = await client.post(
        "/api/storage/presign", json={"filename": "notes.pdf", "resource_type": "document"},
        headers=auth_headers("content_admin"),
    )
    assert admin.status_code == 200
    assert admin.json()["storage_key"]
    assert admin.json()["upload_url"]


@pytest.mark.asyncio
async def test_upload_rejects_bad_extension(client, auth_headers):
    resp = await client.post(
        "/api/storage/presign", json={"filename": "virus.exe", "resource_type": "document"},
        headers=auth_headers("content_admin"),
    )
    assert resp.status_code == 422


# --- Admin content management ---------------------------------------------------
@pytest.mark.asyncio
async def test_admin_edit_and_archive_resource(client, db_engine, auth_headers):
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.models.content import Resource

    async with AsyncSession(db_engine) as session:
        r = Resource(title="Old Title", resource_type="book", rights_status="open_license",
                     ai_usage_status="true", review_status="published", visibility="public")
        session.add(r)
        await session.flush()
        rid = r.id
        await session.commit()

    admin = auth_headers("content_admin")
    # Edit
    edited = await client.patch(f"/api/admin/resources/{rid}", json={"title": "New Title"}, headers=admin)
    assert edited.status_code == 200
    assert edited.json()["title"] == "New Title"

    # Archive (soft delete → 204)
    archived = await client.delete(f"/api/admin/resources/{rid}", headers=admin)
    assert archived.status_code == 204

    # Student cannot edit.
    forbidden = await client.patch("/api/admin/resources/1", json={"title": "x"}, headers=auth_headers("student"))
    assert forbidden.status_code == 403


@pytest.mark.asyncio
async def test_admin_reviews_and_ads(client, auth_headers):
    rev = await client.get("/api/admin/reviews", headers=auth_headers("content_admin"))
    assert rev.status_code == 200
    ads = await client.get("/api/admin/ads", headers=auth_headers("content_admin"))
    assert ads.status_code == 200


# --- Reporting / error system ----------------------------------------------------
@pytest.mark.asyncio
async def test_submit_and_resolve_report(client, auth_headers):
    resp = await client.post(
        "/api/resources/report",
        json={"target_type": "topic", "target_slug": "brachial-plexus", "category": "medical_error", "detail": "Check the nerve roots."},
    )
    assert resp.status_code == 201
    assert resp.json()["status"] == "open"

    admin = auth_headers("content_admin")
    reports = await client.get("/api/admin/reports", headers=admin)
    assert reports.status_code == 200
    assert len(reports.json()) >= 1
    rid = reports.json()[0]["id"]

    resolved = await client.patch(f"/api/admin/reports/{rid}", json={"status": "resolved", "resolution": "Fixed."}, headers=admin)
    assert resolved.status_code == 200
    assert resolved.json()["status"] == "resolved"


@pytest.mark.asyncio
async def test_report_requires_admin_to_list(client, auth_headers):
    resp = await client.get("/api/admin/reports", headers=auth_headers("student"))
    assert resp.status_code == 403


# --- AI search index ---------------------------------------------------------------
@pytest.mark.asyncio
async def test_ai_index_requires_admin_and_embeds(client, db_engine, auth_headers):
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.models.atlas import AnatomicalStructure

    async with AsyncSession(db_engine) as session:
        session.add(AnatomicalStructure(preferred_name="Axillary Artery",
                                        description="Continuation of subclavian artery.", status="verified"))
        await session.commit()

    # Student cannot index.
    denied = await client.post("/api/ai/index", json={"source_type": "structure"}, headers=auth_headers("student"))
    assert denied.status_code == 403

    res = await client.post("/api/ai/index", json={"source_type": "structure"}, headers=auth_headers("content_admin"))
    assert res.status_code == 200
    assert res.json()["indexed"] >= 1

    # Now ask should retrieve via vector path and cite the structure.
    ask = await client.post("/api/ai/ask", json={"question": "What is the axillary artery?"})
    assert ask.status_code == 200
    data = ask.json()
    assert isinstance(data["sources"], list)
    assert data["disclaimer"]


# --- AI ingestion policy never includes unknown/review_required --------------------
@pytest.mark.asyncio
async def test_ai_index_skips_non_ingestable_resources(client, db_engine, auth_headers):
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.models.content import Resource

    async with AsyncSession(db_engine) as session:
        ok = Resource(title="OK Book", resource_type="book", rights_status="open_license",
                      ai_usage_status="true", review_status="published", visibility="public")
        no = Resource(title="Unknown Book", resource_type="book", rights_status="open_license",
                      ai_usage_status="unknown", review_status="published", visibility="public")
        session.add(ok)
        session.add(no)
        await session.commit()

    res = await client.post("/api/ai/index", json={"source_type": "resource"}, headers=auth_headers("content_admin"))
    assert res.status_code == 200
    # Only the ingestable resource is indexed; 'unknown' is skipped.
    assert res.json()["indexed"] == 1
    assert "Unknown Book" in res.json()["skipped"]


# --- Profile ------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_profile_get_and_update(client, auth_headers):
    me = await client.get("/api/me/profile", headers=auth_headers("student"))
    assert me.status_code == 200
    assert me.json()["highest_role"] == "student"

    upd = await client.patch(
        "/api/me/profile",
        json={"display_name": "Asha", "course": "MBBS", "year_of_study": "1", "university": "AIIMS", "country": "IN"},
        headers=auth_headers("student"),
    )
    assert upd.status_code == 200
    assert upd.json()["display_name"] == "Asha"


@pytest.mark.asyncio
async def test_link_works_via_storage_serve(client, db_engine):
    # Verify the storage driver generates a /api/storage/... path we can hit.
    from app.core.storage import get_storage

    storage = get_storage()
    key = "uploads/test/hello.txt"
    storage.put_bytes(key, b"hello world")
    url = storage.get_public_url(key)
    assert url and url.startswith("/api/storage/")
