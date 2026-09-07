"""Security models: audit logs for admin/platform mutations.

Every privileged mutation (upload, publish, role change, review decision,
ad/announcement write, content edit) should record an ``AuditLog`` row with the
actor, action, target, and a result. Backups/compliance rely on this trail.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    actor_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True
    )
    actor_email: Mapped[Optional[str]] = mapped_column(String(255))
    # e.g. resource.upload, resource.publish, user.role_change, ad.create,
    # announcement.create, atlas.model_ingest.
    action: Mapped[str] = mapped_column(String(80), index=True)
    target_type: Mapped[Optional[str]] = mapped_column(String(60))
    target_id: Mapped[Optional[int]] = mapped_column(Integer)
    detail: Mapped[Optional[str]] = mapped_column(Text)
    ip_address: Mapped[Optional[str]] = mapped_column(String(64))
    success: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
