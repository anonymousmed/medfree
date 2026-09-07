"""Reporting / error system (spec §36).

Every content page can surface a "Report an error" flow. Reports are queued for
admin review (never auto-resolved). Captures a category, optional detail and the
actor (anonymous allowed) so students can flag medical errors, typos, broken
links, rights issues, etc.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

# Report categories.
CATEGORY_MEDICAL = "medical_error"
CATEGORY_TYPO = "typo"
CATEGORY_BROKEN_LINK = "broken_link"
CATEGORY_INCORRECT_IMAGE = "incorrect_image"
CATEGORY_COPYRIGHT = "copyright_issue"
CATEGORY_OUTDATED = "outdated"
CATEGORY_INAPPROPRIATE = "inappropriate"
CATEGORY_TECHNICAL = "technical"

REPORT_CATEGORIES = [
    CATEGORY_MEDICAL,
    CATEGORY_TYPO,
    CATEGORY_BROKEN_LINK,
    CATEGORY_INCORRECT_IMAGE,
    CATEGORY_COPYRIGHT,
    CATEGORY_OUTDATED,
    CATEGORY_INAPPROPRIATE,
    CATEGORY_TECHNICAL,
]


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(primary_key=True)
    reporter_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True
    )
    target_type: Mapped[str] = mapped_column(String(40), index=True)
    # topic / resource / atlas_structure / book / question / viva
    target_id: Mapped[Optional[int]] = mapped_column(Integer)
    target_slug: Mapped[Optional[str]] = mapped_column(String(200))
    category: Mapped[str] = mapped_column(String(40), index=True)
    title: Mapped[Optional[str]] = mapped_column(String(300))
    detail: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), default="open")
    # open / under_review / resolved / dismissed
    handled_by: Mapped[Optional[str]] = mapped_column(String(200))
    resolution: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
