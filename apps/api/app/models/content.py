"""Resource / book / license / rights system.

Hosting and direct upload of these is ADMIN-ONLY (see deps.require_admin and
the router). A ``rights_status`` of ``review_required`` blocks publication.
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

RIGHTS_VERIFIED = "verified"
RIGHTS_PERMISSION_GRANTED = "permission_granted"
RIGHTS_PUBLIC_DOMAIN = "public_domain"
RIGHTS_OPEN_LICENSE = "open_license"
RIGHTS_EXTERNAL_ONLY = "external_only"
RIGHTS_REVIEW_REQUIRED = "review_required"
RIGHTS_BLOCKED = "blocked"

REVIEW_DRAFT = "draft"
REVIEW_PENDING_RIGHTS = "pending_rights"
REVIEW_PENDING_MEDICAL = "pending_medical_review"
REVIEW_PENDING_QUALITY = "pending_quality_review"
REVIEW_APPROVED = "approved"
REVIEW_PUBLISHED = "published"
REVIEW_REJECTED = "rejected"
REVIEW_ARCHIVED = "archived"


class License(Base):
    __tablename__ = "licenses"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    license_url: Mapped[Optional[str]] = mapped_column(String(500))
    commercial_allowed: Mapped[bool] = mapped_column(Boolean, default=False)
    modification_allowed: Mapped[bool] = mapped_column(Boolean, default=False)
    redistribution_allowed: Mapped[bool] = mapped_column(Boolean, default=False)
    attribution_required: Mapped[bool] = mapped_column(Boolean, default=True)
    sharealike_required: Mapped[bool] = mapped_column(Boolean, default=False)
    ai_ingestion_allowed: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[Optional[str]] = mapped_column(Text)

    resources: Mapped[list["Resource"]] = relationship(back_populates="license")


class Author(Base):
    __tablename__ = "authors"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), index=True)
    affiliation: Mapped[Optional[str]] = mapped_column(String(300))
    website: Mapped[Optional[str]] = mapped_column(String(500))


class Resource(Base):
    __tablename__ = "resources"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(300), index=True)
    resource_type: Mapped[str] = mapped_column(String(60), index=True)  # book/pdf/epub/diagram/3d/...
    creator: Mapped[Optional[str]] = mapped_column(String(200))
    publisher: Mapped[Optional[str]] = mapped_column(String(200))
    source_url: Mapped[Optional[str]] = mapped_column(String(500))
    local_storage_key: Mapped[Optional[str]] = mapped_column(String(500))
    license_id: Mapped[Optional[int]] = mapped_column(ForeignKey("licenses.id"))
    rights_status: Mapped[str] = mapped_column(String(40), default=RIGHTS_REVIEW_REQUIRED)
    ai_usage_status: Mapped[str] = mapped_column(String(20), default="unknown")  # true/false/unknown
    attribution_text: Mapped[Optional[str]] = mapped_column(Text)
    review_status: Mapped[str] = mapped_column(String(40), default=REVIEW_DRAFT)
    medical_review_status: Mapped[str] = mapped_column(String(40), default="pending")
    visibility: Mapped[str] = mapped_column(String(20), default="private")  # public/private/unlisted
    verified_by: Mapped[Optional[str]] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    license: Mapped[Optional[License]] = relationship(back_populates="resources")
    versions: Mapped[list["ResourceVersion"]] = relationship(back_populates="resource")


class ResourceVersion(Base):
    __tablename__ = "resource_versions"

    id: Mapped[int] = mapped_column(primary_key=True)
    resource_id: Mapped[int] = mapped_column(ForeignKey("resources.id", ondelete="CASCADE"))
    version_label: Mapped[str] = mapped_column(String(50))
    storage_key: Mapped[Optional[str]] = mapped_column(String(500))
    checksum: Mapped[Optional[str]] = mapped_column(String(64))
    change_note: Mapped[Optional[str]] = mapped_column(Text)
    created_by: Mapped[Optional[str]] = mapped_column(String(100))

    resource: Mapped[Resource] = relationship(back_populates="versions")


class Book(Base):
    __tablename__ = "books"

    id: Mapped[int] = mapped_column(primary_key=True)
    resource_id: Mapped[Optional[int]] = mapped_column(ForeignKey("resources.id"))
    author_id: Mapped[Optional[int]] = mapped_column(ForeignKey("authors.id"))
    title: Mapped[str] = mapped_column(String(300))
    edition: Mapped[Optional[str]] = mapped_column(String(100))
    publisher: Mapped[Optional[str]] = mapped_column(String(200))
    isbn: Mapped[Optional[str]] = mapped_column(String(50))
    year: Mapped[Optional[int]] = mapped_column(Integer)
    subject_slug: Mapped[Optional[str]] = mapped_column(String(100))
    reading_progress: Mapped[int] = mapped_column(Integer, default=0)

    author: Mapped[Optional[Author]] = relationship()
    resource: Mapped[Optional[Resource]] = relationship()
    chapters: Mapped[list["BookChapter"]] = relationship(
        back_populates="book", cascade="all, delete-orphan"
    )

    __table_args__ = (UniqueConstraint("resource_id", name="uq_book_resource"),)


class BookChapter(Base):
    __tablename__ = "book_chapters"

    id: Mapped[int] = mapped_column(primary_key=True)
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(300))
    chapter_index: Mapped[int] = mapped_column(Integer, default=0)
    topic_slug: Mapped[Optional[str]] = mapped_column(String(150), index=True)
    content_key: Mapped[Optional[str]] = mapped_column(String(500))

    book: Mapped[Book] = relationship(back_populates="chapters")
