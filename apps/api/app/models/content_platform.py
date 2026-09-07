"""Admin-controlled advertising & announcements (controlled placement)."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Integer, String, Text, UnicodeText
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class Ad(Base):
    __tablename__ = "ads"

    id: Mapped[int] = mapped_column(primary_key=True)
    image_key: Mapped[Optional[str]] = mapped_column(String(500))  # object-storage key / URL
    title: Mapped[Optional[str]] = mapped_column(String(200))
    target_url: Mapped[Optional[str]] = mapped_column(String(500))
    placement: Mapped[str] = mapped_column(String(50), default="homepage")  # homepage/dashboard/resource/learning/announcement
    start_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    end_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    priority: Mapped[int] = mapped_column(Integer, default=0)
    alt_text: Mapped[Optional[str]] = mapped_column(String(300))
    advertiser: Mapped[Optional[str]] = mapped_column(String(200))
    campaign_id: Mapped[Optional[str]] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Announcement(Base):
    __tablename__ = "announcements"

    id: Mapped[int] = mapped_column(primary_key=True)
    kind: Mapped[str] = mapped_column(String(40), default="system")  # system/resource/atlas/maintenance/event
    title: Mapped[str] = mapped_column(String(200))
    body: Mapped[Optional[str]] = mapped_column(Text)
    link: Mapped[Optional[str]] = mapped_column(String(500))
    publish_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    expire_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
