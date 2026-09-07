"""Steps 16–20: Analytics, Security (audit/rate-limit/file-type), Partnerships."""
import pytest


# --- Step 16: Analytics -------------------------------------------------------
@pytest.mark.asyncio
async def test_track_event_anonymous(client):
    resp = await client.post("/api/analytics/events", json={"event_type": "atlas_open", "path": "/atlas"})
    assert resp.status_code == 201
    assert resp.json()["ok"] is True


@pytest.mark.asyncio
async def test_track_search_and_analytics_admin(client, auth_headers):
    await client.post("/api/analytics/search", json={"query": "median nerve", "result_count": 5})
    await client.post("/api/analytics/search", json={"query": "quantum physics", "result_count": 0})

    # Admin can read aggregate analytics.
    resp = await client.get("/api/admin/analytics", headers=auth_headers("content_admin"))
    assert resp.status_code == 200
    data = resp.json()
    assert data["search"]["volume"] >= 2
    assert data["search"]["failed"] >= 1
    assert data["users"]["total"] >= 0


@pytest.mark.asyncio
async def test_admin_analytics_requires_admin(client, auth_headers):
    resp = await client.get("/api/admin/analytics", headers=auth_headers("student"))
    assert resp.status_code == 403


# --- Step 17: Security ---------------------------------------------------------
@pytest.mark.asyncio
async def test_audit_log_recorded_on_role_change(client, db_engine, auth_headers):
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.models.user import User

    async with AsyncSession(db_engine) as session:
        u = User(supabase_id="audit-subject", email="target@x.com", is_active=True)
        session.add(u)
        await session.flush()
        uid = u.id
        await session.commit()

    admin = auth_headers("content_admin")
    resp = await client.post(f"/api/admin/users/{uid}/role", json={"role": "reviewer"}, headers=admin)
    assert resp.status_code == 200

    logs = await client.get("/api/admin/audit-logs", headers=admin)
    assert logs.status_code == 200
    actions = [r["action"] for r in logs.json()]
    assert "user.role_change" in actions


@pytest.mark.asyncio
async def test_audit_log_requires_admin(client, auth_headers):
    resp = await client.get("/api/admin/audit-logs", headers=auth_headers("student"))
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_security_headers_present(client):
    # Any response should carry the hardened headers.
    resp = await client.head("/api/health")
    assert resp.status_code in (200, 405, 404)  # head may 405; but present via middleware
    h = resp.headers
    # Headers are attached on the actual response; use GET to be safe.
    if "x-content-type-options" not in h:
        r2 = await client.get("/api/health")
        assert r2.headers.get("x-content-type-options") == "nosniff"


def test_validate_upload_type():
    from app.api.routes.security import validate_upload_type

    ok, msg = validate_upload_type("notes.pdf", "document")
    assert ok and msg is None
    ok, msg = validate_upload_type("virus.exe", "document")
    assert not ok and "not allowed" in msg
    ok, msg = validate_upload_type("model.glb", "model")
    assert ok


@pytest.mark.asyncio
async def test_rate_limit_triggers_429(client):
    # Hit the search endpoint repeatedly beyond its configurable limit.
    from app.core.config import settings

    rl = settings.rate_limit_search
    limit_status = None
    for _ in range(rl + 2):
        r = await client.get("/api/search?q=m")
        if r.status_code == 429:
            limit_status = 429
            break
    assert limit_status == 429


# --- Step 20: Partnerships ------------------------------------------------------
@pytest.mark.asyncio
async def test_submit_partnership_interest(client):
    resp = await client.post(
        "/api/partners/interest",
        json={
            "organization_type": "medical_college",
            "organization_name": "Example Medical College",
            "contact_name": "Dr. A",
            "contact_email": "dr.a@example.com",
            "goal": "Collaborate on content",
        },
    )
    assert resp.status_code == 201
    assert resp.json()["status"] == "pending"


@pytest.mark.asyncio
async def test_partner_directory_and_admin(client, db_engine, auth_headers):
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.models.partnership import Institution

    async with AsyncSession(db_engine) as session:
        session.add(Institution(name="Partner College", kind="medical_college", is_active=True))
        await session.commit()

    public = await client.get("/api/partners")
    assert public.status_code == 200
    assert any(p["name"] == "Partner College" for p in public.json())

    admin = auth_headers("content_admin")
    # Create via admin.
    created = await client.post(
        "/api/admin/partners",
        json={"name": "New College", "kind": "university", "is_featured": True},
        headers=admin,
    )
    assert created.status_code == 201

    created_id = created.json()["id"]
    patched = await client.patch(f"/api/admin/partners/{created_id}", json={"is_active": False}, headers=admin)
    assert patched.status_code == 200
    assert patched.json()["is_active"] is False


@pytest.mark.asyncio
async def test_partnership_admin_requires_admin(client, auth_headers):
    resp = await client.get("/api/admin/partners", headers=auth_headers("student"))
    assert resp.status_code == 403
