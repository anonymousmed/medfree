"""Security routes (Step 17): admin audit-log read + file-type validation helper.

Audit records are written by admin mutation routes (via ``app.core.security``);
this exposes the read side for the admin panel. Also exposes a small file-type
allowlist validator used by the admin upload endpoints.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin
from app.db.session import get_session
from app.models.security import AuditLog

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])

# Allowed upload extensions by resource type (spec §50: never blindly allow
# arbitrary executable files).
#
# NOTE: the admin upload form (AdminUpload.tsx) offers these resource types:
#   book, pdf, epub, image, diagram, 3d, video, audio, slides, dataset,
#   notes, article. Every one of them must resolve to a non-empty allowlist so
#   an otherwise-valid file (e.g. a PDF book) is never rejected with a confusing
#   "file type not allowed" error.
ALLOWED_EXTENSIONS = {
    # Document-like types (PDF is the ubiquitous "book" format on MEDFREE).
    "book": {".pdf", ".epub", ".docx", ".md", ".txt"},
    "pdf": {".pdf"},
    "epub": {".epub"},
    "document": {".pdf", ".epub", ".docx", ".md", ".txt"},
    "notes": {".pdf", ".epub", ".docx", ".md", ".txt"},
    "article": {".pdf", ".docx", ".md", ".txt", ".epub"},
    # Images / diagrams.
    "image": {".jpg", ".jpeg", ".png", ".webp", ".gif", ".svg"},
    "diagram": {".jpg", ".jpeg", ".png", ".webp", ".svg"},
    # Media.
    "video": {".mp4", ".webm", ".mkv"},
    "audio": {".mp3", ".wav", ".ogg", ".m4a"},
    # 3D models.
    "3d": {".glb", ".gltf"},
    "model": {".glb", ".gltf"},
    # Data.
    "dataset": {".csv", ".json", ".xlsx"},
    # Slide decks.
    "slides": {".pdf", ".pptx", ".odp"},
}


def guess_content_type(filename: str) -> str:
    """Best-effort MIME type for a filename (used to store PDFs as
    ``application/pdf`` so the browser renders them inline instead of
    downloading them)."""
    import mimetypes

    ct, _ = mimetypes.guess_type(filename)
    if ct:
        return ct
    ext = os.path.splitext(filename)[1].lower()
    return {
        ".pdf": "application/pdf",
        ".epub": "application/epub+zip",
        ".md": "text/markdown",
        ".txt": "text/plain",
        ".glb": "model/gltf-binary",
        ".gltf": "model/gltf+json",
    }.get(ext, "application/octet-stream")


def validate_upload_type(filename: str, resource_type: str) -> tuple[bool, str | None]:
    """Return (ok, message). Rejects disallowed extensions for a resource type."""
    import os

    ext = os.path.splitext(filename)[1].lower()
    allowed = ALLOWED_EXTENSIONS.get(resource_type)
    if allowed is None:
        return False, f"Unknown resource_type '{resource_type}'."
    if ext not in allowed:
        return False, f"Extension '{ext}' not allowed for type '{resource_type}'."
    return True, None


@router.get("/audit-logs", response_model=list[dict])
async def audit_logs(
    session: AsyncSession = Depends(get_session),
    limit: int = 100,
):
    rows = (
        await session.execute(
            select(AuditLog).order_by(AuditLog.id.desc()).limit(min(limit, 500))
        )
    ).scalars().all()
    return [
        {
            "id": r.id,
            "actor_email": r.actor_email,
            "action": r.action,
            "target_type": r.target_type,
            "target_id": r.target_id,
            "detail": r.detail,
            "ip_address": r.ip_address,
            "success": r.success,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]
