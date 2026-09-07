"""Auth + identity tests (mock provider for local/integration)."""
import base64
import json

import pytest


def _token(role="student", sub="u1", email="u1@example.com"):
    def enc(d):
        return base64.urlsafe_b64encode(json.dumps(d).encode()).decode().rstrip("=")

    return f"{enc({'alg':'none','typ':'JWT'})}.{enc({'sub':sub,'email':email,'role':role})}."


@pytest.mark.asyncio
async def test_me_requires_auth(client):
    resp = await client.get("/api/auth/me")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_me_returns_profile(client, auth_headers):
    resp = await client.get("/api/auth/me", headers=auth_headers("student"))
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == "t@example.com"
    assert data["highest_role"] == "student"


@pytest.mark.asyncio
async def test_identity_endpoint(client, auth_headers):
    resp = await client.get("/api/auth/identity", headers=auth_headers("content_admin"))
    assert resp.status_code == 200
    assert resp.json()["role"] == "content_admin"


@pytest.mark.asyncio
async def test_user_provisioned_with_role(client, auth_headers):
    # First call creates the local user row with the given role.
    resp = await client.get("/api/auth/me", headers=auth_headers("super_admin"))
    assert resp.status_code == 200
    assert resp.json()["highest_role"] == "super_admin"
