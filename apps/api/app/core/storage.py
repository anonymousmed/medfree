"""Object-storage abstraction (provider-agnostic).

MEDFREE stores books, PDFs/EPUBs, images, diagrams and 3D assets in S3-compatible
object storage (spec §7, §50, §63). The rest of the app talks to a thin
``StorageDriver`` interface so the provider can be swapped (Cloudflare R2,
Supabase Storage, AWS S3, Backblaze B2) via env vars only.

Two drivers:
- ``LocalStorageDriver`` — file-system mock used in local dev/CI (no credentials),
  with a deterministic path under ``MEDFREE_STORAGE_DIR``.
- ``S3StorageDriver``     — boto3-backed driver used in production when
  ``STORAGE_ACCESS_KEY``/``STORAGE_SECRET_KEY``/``STORAGE_ENDPOINT`` are set.

Uploads are admin-gated at the API layer; this module only deals with bytes/keys.
"""
from __future__ import annotations

import hashlib
import os
import uuid
from pathlib import Path
from typing import Protocol

from app.core.config import settings


class StorageDriver(Protocol):
    def presign_upload(self, key: str, content_type: str | None = None) -> str: ...
    def put_bytes(self, key: str, data: bytes, content_type: str | None = None) -> None: ...
    def get_bytes(self, key: str) -> bytes: ...
    def get_public_url(self, key: str) -> str | None: ...
    def delete(self, key: str) -> None: ...
    def exists(self, key: str) -> bool: ...


class LocalStorageDriver:
    """Filesystem-backed driver for local/dev. Not for production use."""

    def __init__(self, root: str | None = None):
        self.root = Path(root or settings.storage_local_root or "./storage")

    def _path(self, key: str) -> Path:
        # Prevent path traversal.
        safe = key.replace("..", "").lstrip("/")
        p = (self.root / safe).resolve()
        if not str(p).startswith(str(self.root.resolve())):
            raise ValueError("Invalid storage key")
        return p

    def presign_upload(self, key: str, content_type: str | None = None) -> str:
        return f"local://{key}"

    def put_bytes(self, key: str, data: bytes, content_type: str | None = None) -> None:
        max_bytes = settings.max_upload_mb * 1024 * 1024
        if max_bytes and len(data) > max_bytes:
            raise ValueError(f"File exceeds the {settings.max_upload_mb} MB upload limit")
        p = self._path(key)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)

    def get_bytes(self, key: str) -> bytes:
        return self._path(key).read_bytes()

    def get_public_url(self, key: str) -> str | None:
        p = self._path(key)
        if not p.exists():
            return None
        return f"/api/storage/{key}"

    def delete(self, key: str) -> None:
        p = self._path(key)
        if p.exists():
            p.unlink()

    def exists(self, key: str) -> bool:
        return self._path(key).exists()


class S3StorageDriver:
    """boto3-backed driver for production. Requires STORAGE_ACCESS_KEY/SECRET."""

    def __init__(self):
        import boto3  # type: ignore

        self.bucket = settings.storage_bucket
        endpoint = settings.storage_endpoint
        region = settings.storage_region or "auto"
        # Supabase's S3-compatible API (endpoint .../storage/v1/s3) requires the
        # *virtual* region "auto" in the request signature — even though the
        # bucket physically lives in e.g. ap-southeast-1. Signing with the
        # physical region makes presigned upload/download URLs fail with
        # "Missing signature" / AccessDenied (403). Force "auto" for Supabase.
        if endpoint and "supabase.co" in endpoint:
            region = "auto"
        self.client = boto3.client(
            "s3",
            endpoint_url=endpoint,
            aws_access_key_id=settings.storage_access_key,
            aws_secret_access_key=settings.storage_secret_key,
            region_name=region,
        )

    def presign_upload(self, key: str, content_type: str | None = None) -> str:
        params = {
            "Bucket": self.bucket,
            "Key": key,
            "ContentType": content_type or "application/octet-stream",
        }
        return self.client.generate_presigned_url(
            "put_object", Params=params, ExpiresIn=3600
        )

    def put_bytes(self, key: str, data: bytes, content_type: str | None = None) -> None:
        self.client.put_object(
            Bucket=self.bucket, Key=key, Body=data,
            ContentType=content_type or "application/octet-stream",
        )

    def get_bytes(self, key: str) -> bytes:
        resp = self.client.get_object(Bucket=self.bucket, Key=key)
        return resp["Body"].read()

    def get_public_url(self, key: str) -> str | None:
        # If a public base URL is configured (public Supabase bucket / CDN),
        # serve the canonical public object URL; otherwise use a presigned URL.
        base = getattr(settings, "storage_public_base_url", None)
        if base:
            base = base.rstrip("/")
            return f"{base}/{key.lstrip('/')}"
        return self.client.generate_presigned_url(
            "get_object", Params={"Bucket": self.bucket, "Key": key}, ExpiresIn=3600
        )

    def delete(self, key: str) -> None:
        self.client.delete_object(Bucket=self.bucket, Key=key)
    def exists(self, key: str) -> bool:
        try:
            self.client.head_object(Bucket=self.bucket, Key=key)
            return True
        except Exception:
            return False


_driver: StorageDriver | None = None


def get_storage() -> StorageDriver:
    """Return the configured storage driver (S3 when creds present, else Local)."""
    global _driver
    if _driver is not None:
        return _driver
    if settings.storage_access_key and settings.storage_secret_key:
        _driver = S3StorageDriver()
    else:
        _driver = LocalStorageDriver()
    return _driver


def compute_checksum(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def new_storage_key(resource_type: str, filename: str, folder: str = "uploads") -> str:
    ext = os.path.splitext(filename)[1].lower() or ".bin"
    name = uuid.uuid4().hex
    return f"{folder}/{resource_type}/{name}{ext}"
