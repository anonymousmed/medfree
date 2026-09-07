"""Supabase auth-verification regression tests.

Modern Supabase projects sign access tokens with an EC key (ES256) published at
``/auth/v1/.well-known/jwks.json``. ``SupabaseAuthProvider`` must validate against
that JWKS (not just a legacy HS256 ``jwt_secret``). These tests exercise the
provider offline by stubbing the HTTP fetch and jose's decode.
"""
import pytest
from fastapi import HTTPException


@pytest.fixture
def provider(monkeypatch):
    import app.core.auth as auth_mod
    from app.core.config import get_settings

    s = get_settings()
    monkeypatch.setattr(s, "auth_provider", "supabase")
    monkeypatch.setattr(s, "supabase_url", "https://example.supabase.co")
    monkeypatch.setattr(s, "supabase_jwt_secret", "legacy-hs256-secret")
    monkeypatch.setattr(s, "auth_jwt_audience", "authenticated")

    # httpx is imported at module level -> patchable.
    import httpx as _httpx
    monkeypatch.setattr(auth_mod, "httpx", _httpx)
    return auth_mod.SupabaseAuthProvider()


def _fake_jwks_response():
    class _Resp:
        def raise_for_status(self):
            return None

        def json(self):
            return {"keys": [{"kty": "EC", "alg": "ES256", "use": "sig", "kid": "d4d6e76f"}]}

    return _Resp()


@pytest.fixture
def stub_jwks(provider, monkeypatch):
    """Make the JWKS path return a (structurally valid) JWKS and decode succeed."""
    import app.core.auth as auth_mod
    from jose import jwt as _jwt

    monkeypatch.setattr(auth_mod.httpx, "get", lambda *a, **k: _fake_jwks_response())

    def fake_decode(tok, key, **kw):
        assert isinstance(key, dict), "JWKS path should pass the JWKS dict as the key"
        return {
            "sub": "u-supabase-123", "email": "s@example.com",
            "aud": "authenticated", "exp": 4102444800,
            "app_metadata": {"role": "super_admin"},
        }

    monkeypatch.setattr(_jwt, "decode", fake_decode)


@pytest.fixture
def stub_failed_jwks(provider, monkeypatch):
    """JWKS fetch is fine but decode fails -> should fall through; and with no
    valid secret the token must be rejected."""
    import app.core.auth as auth_mod
    from jose import jwt as _jwt

    monkeypatch.setattr(auth_mod.httpx, "get", lambda *a, **k: _fake_jwks_response())

    def boom(tok, key, **kw):
        raise Exception("expired or bad signature")

    monkeypatch.setattr(_jwt, "decode", boom)


def _token():
    import base64, json

    def enc(obj):
        return base64.urlsafe_b64encode(json.dumps(obj).encode()).decode().rstrip("=")

    header = enc({"alg": "ES256", "typ": "JWT", "kid": "d4d6e76f-ec63-4b94-81b0-9b692f6fe6cf"})
    body = enc({"sub": "u-supabase-123", "email": "s@example.com",
                "aud": "authenticated", "exp": 4102444800,
                "app_metadata": {"role": "super_admin"}})
    return f"{header}.{body}.fakesig"


def test_jwks_path_maps_super_admin(provider, stub_jwks):
    pl = provider.verify(_token())
    assert pl.role == "super_admin"
    assert pl.is_superuser is True
    assert pl.sub == "u-supabase-123"


def test_garbage_token_rejected(provider, stub_failed_jwks):
    with pytest.raises(HTTPException) as exc:
        provider.verify("not.a.jwt")
    assert exc.value.status_code == 401
