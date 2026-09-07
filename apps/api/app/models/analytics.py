"""Analytics models.

Kept intentionally lightweight and non-invasive: events are anonymous where
possible (``user_id`` is optional), and no personal data is captured beyond what
the product already knows for study progress. Aggregates are computed on demand
in the admin analytics endpoint (no separate OLAP layer needed at MVP scale).
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy import func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AnalyticsEvent(Base):
    """A high-level product/learning event (e.g. page_view, atlas_explore)."""

    __tablename__ = "analytics_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True
    )
    # e.g. page_view, atlas_open, atlas_explore, quiz_start, viva_start,
    # flashcard_review, topic_open, book_open, search_run, signup.
    event_type: Mapped[str] = mapped_column(String(60), index=True)
    source: Mapped[Optional[str]] = mapped_column(String(60))  # web / android / ios
    session_id: Mapped[Optional[str]] = mapped_column(String(80), index=True)
    path: Mapped[Optional[str]] = mapped_column(String(300))
    meta: Mapped[Optional[str]] = mapped_column(Text)  # JSON blob
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class SearchEvent(Base):
    """A search interaction, used for search analytics (most searched, failed)."""

    __tablename__ = "search_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True
    )
    query: Mapped[str] = mapped_column(String(300), index=True)
    result_count: Mapped[int] = mapped_column(Integer, default=0)
    is_failed: Mapped[bool] = mapped_column(Boolean, default=False)
    target_type: Mapped[Optional[str]] = mapped_column(String(40))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
