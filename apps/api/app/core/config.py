"""Application settings.

Read from environment variables (see .env.example) and/or a .env file.
The abstraction is intentionally thin so providers (Supabase, Postgres,
object storage) can be swapped later without touching business logic.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- General -----------------------------------------------------------
    app_name: str = "MEDFREE API"
    environment: Literal["development", "staging", "production", "test"] = "development"
    debug: bool = False
    api_v1_prefix: str = "/api"

    # --- Auth (Supabase / managed auth abstraction) -------------------------
    # MEDFREE_AUTH_PROVIDER = "supabase" | "mock"
    auth_provider: Literal["supabase", "mock"] = "mock"
    supabase_url: str | None = None
    supabase_anon_key: str | None = None
    supabase_service_role_key: str | None = None
    supabase_jwt_secret: str | None = None
    auth_jwt_audience: str = "authenticated"
    # Bypass auth in dev when a mock provider is chosen.
    auth_bypass: bool = Field(default=True, description="Dev-only bypass")

    # --- Database ----------------------------------------------------------
    database_url: str | None = None
    db_echo: bool = False

    # --- Object storage (S3-compatible) ------------------------------------
    storage_endpoint: str | None = None
    storage_access_key: str | None = None
    storage_secret_key: str | None = None
    storage_bucket: str = "medfree"
    storage_region: str = "auto"
    # Optional public base URL for served objects. When set (e.g. a public
    # Supabase bucket -> https://<ref>.supabase.co/storage/v1/object/public/
    # or a CDN domain), get_public_url returns base_url + key directly instead
    # of a presigned URL. Leave empty to fall back to presigned URLs.
    storage_public_base_url: str | None = None
    # Local/dev fallback when no S3 creds are present (stores under this dir).
    storage_local_root: str | None = "./storage"
    # Maximum permitted upload size (MB). Guarded at the API layer and, for the
    # local driver, at the byte-write layer. S3 presigned URLs should also carry
    # a ContentLengthRange for real enforcement in production.
    max_upload_mb: int = 200

    # --- Security / rate limiting --------------------------------------------
    # client-facing: search, auth, and admin mutations get tighter budgets.
    rate_limit_anon: int = 60
    rate_limit_authed: int = 300
    rate_limit_auth: int = 10
    rate_limit_search: int = 30
    rate_limit_admin: int = 120
    rate_limit_window: int = 60
    security_headers: bool = True

    # --- Rendering / previews ----------------------------------------------
    cors_origins: list[str] = [
        "http://localhost:3000",
        "https://medfree.vercel.app",
    ]
    cors_allow_credentials: bool = True
    frontend_url: str = "http://localhost:3000"

    # --- Misc ---------------------------------------------------------------
    log_level: str = "INFO"
    featured_region_slug: str = "upper-limb"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
