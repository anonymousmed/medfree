"""Curriculum: subjects → topics (curriculum is not hard-coded)."""
from __future__ import annotations

from typing import Optional

from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

# Link types in the curriculum "knowledge graph" (Phase 11). General — supports
# any medical subject, not hard-coded to one.
LINK_PREREQUISITE = "prerequisite"
LINK_RELATED = "related"
LINK_NEXT = "next"

from app.db.base import Base, TimestampMixin

SUBJECT_ANATOMY = "anatomy"
SUBJECT_PHYSIOLOGY = "physiology"
SUBJECT_BIOCHEMISTRY = "biochemistry"


class Subject(Base):
    __tablename__ = "subjects"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[Optional[str]] = mapped_column(Text)
    icon: Mapped[Optional[str]] = mapped_column(String(50))
    color: Mapped[Optional[str]] = mapped_column(String(20))
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(default=True)

    topics: Mapped[list["Topic"]] = relationship(back_populates="subject")


class Topic(TimestampMixin, Base):
    __tablename__ = "topics"

    id: Mapped[int] = mapped_column(primary_key=True)
    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id", ondelete="CASCADE"))
    slug: Mapped[str] = mapped_column(String(150), index=True)
    title: Mapped[str] = mapped_column(String(200))
    summary: Mapped[Optional[str]] = mapped_column(Text)
    learning_objectives: Mapped[Optional[str]] = mapped_column(Text)
    content_markdown: Mapped[Optional[str]] = mapped_column(Text)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_published: Mapped[bool] = mapped_column(default=False)
    # Curriculum "knowledge graph" (Phase 11) — general across subjects.
    difficulty: Mapped[str] = mapped_column(
        String(20), default="medium", server_default="medium", index=True
    )  # basic/intermediate/advanced
    est_minutes: Mapped[int] = mapped_column(Integer, default=0, server_default="0")

    subject: Mapped[Subject] = relationship(back_populates="topics")
    blocks: Mapped[list["TopicBlock"]] = relationship(
        back_populates="topic", cascade="all, delete-orphan"
    )
    # Outgoing links (this topic -> other topics): prerequisites, related, next.
    outgoing_links: Mapped[list["TopicLink"]] = relationship(
        foreign_keys="TopicLink.from_topic_id", back_populates="from_topic",
        cascade="all, delete-orphan",
    )
    incoming_links: Mapped[list["TopicLink"]] = relationship(
        foreign_keys="TopicLink.to_topic_id", back_populates="to_topic",
        cascade="all, delete-orphan",
    )

    __table_args__ = (UniqueConstraint("subject_id", "slug", name="uq_subject_topic_slug"),)


class TopicLink(Base):
    """Directed curriculum link between two topics (a knowledge-graph edge).

    ``link_type`` is one of ``prerequisite`` / ``related`` / ``next``. This is a
    first-class graph so prerequisites are expressed for every subject, not just
    one hard-coded chain.
    """

    __tablename__ = "topic_links"

    id: Mapped[int] = mapped_column(primary_key=True)
    from_topic_id: Mapped[int] = mapped_column(
        ForeignKey("topics.id", ondelete="CASCADE"), index=True
    )
    to_topic_id: Mapped[int] = mapped_column(
        ForeignKey("topics.id", ondelete="CASCADE"), index=True
    )
    link_type: Mapped[str] = mapped_column(String(20), default=LINK_RELATED)
    label: Mapped[Optional[str]] = mapped_column(String(120))
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    from_topic: Mapped["Topic"] = relationship(
        foreign_keys=[from_topic_id], back_populates="outgoing_links"
    )
    to_topic: Mapped["Topic"] = relationship(
        foreign_keys=[to_topic_id], back_populates="incoming_links"
    )

    __table_args__ = (
        UniqueConstraint("from_topic_id", "to_topic_id", "link_type", name="uq_topic_link"),
    )


class TopicBlock(Base):
    """A structured learning block within a topic (the 'learning flow').

    Ordered by ``position`` along the canonical flow (overview → atlas →
    clinical → mcq → viva → flashcards → books → revision).
    """

    __tablename__ = "topic_blocks"

    id: Mapped[int] = mapped_column(primary_key=True)
    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id", ondelete="CASCADE"), index=True)
    position: Mapped[int] = mapped_column(Integer, default=0)
    block_type: Mapped[str] = mapped_column(String(40))  # overview/objectives/atlas/clinical/mcq/viva/flashcard/books/revision/practical
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[Optional[str]] = mapped_column(Text)
    meta: Mapped[Optional[str]] = mapped_column(Text)  # JSON metadata (e.g. {type:'diagram', url:...})
    is_enabled: Mapped[bool] = mapped_column(default=True)

    topic: Mapped[Topic] = relationship(back_populates="blocks")
