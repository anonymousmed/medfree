"""Verifies the ADMIN-ONLY upload mandate at the backend (mandate #7).

Students and contributors MUST receive 403 even when the frontend never shows
an upload button. The mock auth provider lets us simulate each role.
"""
import pytest

UPLOAD_PAYLOAD = {
    "title": "OpenStax Anatomy",
    "resource_type": "book",
    "creator": "OpenStax",
    "publisher": "OpenStax",
    "source_url": "https://openstax.org/",
    "license_name": "CC BY-NC-SA",
    "rights_status": "open_license",
    "ai_usage_status": "true",
    "visibility": "public",
}


@pytest.mark.asyncio
async def test_student_cannot_upload(client, auth_headers):
    resp = await client.post(
        "/api/resources/upload", json=UPLOAD_PAYLOAD, headers=auth_headers("student")
    )
    assert resp.status_code == 403, resp.text


@pytest.mark.asyncio
async def test_contributor_cannot_upload(client, auth_headers):
    resp = await client.post(
        "/api/resources/upload", json=UPLOAD_PAYLOAD, headers=auth_headers("contributor")
    )
    assert resp.status_code == 403, resp.text


@pytest.mark.asyncio
async def test_contributor_submit_goes_to_review(client, auth_headers):
    resp = await client.post(
        "/api/resources/submit",
        json={"title": "My notes", "resource_type": "notes"},
        headers=auth_headers("contributor"),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["review_status"] == "draft"
    assert data["visibility"] == "private"


@pytest.mark.asyncio
async def test_content_admin_can_upload(client, auth_headers):
    resp = await client.post(
        "/api/resources/upload", json=UPLOAD_PAYLOAD, headers=auth_headers("content_admin")
    )
    assert resp.status_code == 201, resp.text


@pytest.mark.asyncio
async def test_super_admin_can_upload(client, auth_headers):
    resp = await client.post(
        "/api/resources/upload", json=UPLOAD_PAYLOAD, headers=auth_headers("super_admin")
    )
    assert resp.status_code == 201, resp.text


@pytest.mark.asyncio
async def test_admin_publish_blocked_when_rights_unverified(client, auth_headers):
    """Even admins cannot publish a resource whose rights_status is review_required."""
    # Create with review_required → should be rejected at upload.
    payload = dict(UPLOAD_PAYLOAD)
    payload["rights_status"] = "review_required"
    resp = await client.post(
        "/api/resources/upload", json=payload, headers=auth_headers("super_admin")
    )
    assert resp.status_code == 422, resp.text


@pytest.mark.asyncio
async def test_admin_can_assign_role_without_500(client, auth_headers):
    """Regression: POST /admin/users/{id}/role must succeed and record an audit
    row. It previously crashed with a 500 because the Supabase UUID token.sub
    was written into the INTEGER audit_logs.actor_id FK."""
    # Auto-provision a user via /me (creates a local user row + role).
    prov = await client.get("/api/me/profile", headers=auth_headers("super_admin"))
    assert prov.status_code == 200

    users_resp = await client.get("/api/admin/users", headers=auth_headers("super_admin"))
    assert users_resp.status_code == 200
    users = users_resp.json()
    assert users, "expected at least one user"
    uid = users[0]["id"]

    resp = await client.post(
        f"/api/admin/users/{uid}/role",
        json={"role": "content_admin"},
        headers=auth_headers("super_admin"),
    )
    assert resp.status_code == 200, resp.text
    assert "content_admin" in resp.json()["roles"], resp.text
