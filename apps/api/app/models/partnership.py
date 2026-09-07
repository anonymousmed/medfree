"""Partnership models (Step 20).

Institutions, faculty collaborators and student-group partnerships. These are
public-facing discovery records (a landing/directory) plus a lightweight
interest/request flow. Admins manage the records; any visitor can submit an
interest request which is queued for review (never auto-published).
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class Institution(Base):
    """A partner medical college / institution (public directory entry)."""

    __tablename__ = "institutions"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(300), index=True)
    kind: Mapped[str] = mapped_column(String(60), default="medical_college")
    # medical_college / university / research_institute / ngo / student_group / faculty
    country: Mapped[Optional[str]] = mapped_column(String(100))
    region: Mapped[Optional[str]] = mapped_column(String(150))
    website: Mapped[Optional[str]] = mapped_column(String(400))
    contact_email: Mapped[Optional[str]] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text)
    logo_key: Mapped[Optional[str]] = mapped_column(String(300))
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class PartnershipRequest(TimestampMixin, Base):
    """A submitted partnership interest, queued for admin review."""

    __tablename__ = "partnership_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_type: Mapped[str] = mapped_column(String(60), default="medical_college")
    organization_name: Mapped[str] = mapped_column(String(300))
    contact_name: Mapped[str] = mapped_column(String(200))
    contact_email: Mapped[str] = mapped_column(String(255), index=True)
    contact_phone: Mapped[Optional[str]] = mapped_column(String(60))
    message: Mapped[Optional[str]] = mapped_column(Text)
    goal: Mapped[Optional[str]] = mapped_column(String(300))
    status: Mapped[str] = mapped_column(String(40), default="pending")
    # pending / reviewing / accepted / declined
    handled_by: Mapped[Optional[str]] = mapped_column(String(255))
    admin_notes: Mapped[Optional[str]] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
