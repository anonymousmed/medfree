"""Content embeddings for the AI/RAG study assistant (spec §27, §50).

Stores a provider-agnostic embedding vector per content chunk. In production this
maps to a PostgreSQL ``pgvector`` column (vector similarity). In local/CI (SQLite)
the ``app.core.embeddings`` module computes a deterministic hashed vector so the
feature runs without pgvector, and the same cosine-similarity retrieval path is
used either way.

The embedding is only created for content that is AI-eligible (``is_ingestable``),
and only after rights/review gates pass — never for ``unknown`` / ``review_required``.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ContentEmbedding(Base):
    __tablename__ = "content_embeddings"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_type: Mapped[str] = mapped_column(String(40), index=True)
    # topic / structure / resource
    source_id: Mapped[Optional[int]] = mapped_column(Integer, index=True)
    source_key: Mapped[str] = mapped_column(String(300), index=True)  # unique key
    title: Mapped[Optional[str]] = mapped_column(String(300))
    text: Mapped[str] = mapped_column(Text)
    href: Mapped[Optional[str]] = mapped_column(String(400))
    # JSON-encoded list of floats. With pgvector this becomes a native vector column;
    # the JSON rep keeps it portable/across-SQLite.
    vector_json: Mapped[Optional[str]] = mapped_column(Text)
    model_tag: Mapped[str] = mapped_column(String(80), default="medfree-hash-v1")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
