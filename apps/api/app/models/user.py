"""User + RBAC role models."""
from __future__ import annotations

from typing import Optional

from sqlalchemy import Boolean, ForeignKey, String, Table, Column, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

# Canonical RBAC roles. These map onto Supabase app_metadata.role (see auth.py).
ROLE_STUDENT = "student"
ROLE_CONTRIBUTOR = "contributor"
ROLE_REVIEWER = "reviewer"
ROLE_MEDICAL_REVIEWER = "medical_reviewer"
ROLE_MODERATOR = "moderator"
ROLE_CONTENT_ADMIN = "content_admin"
ROLE_SUPER_ADMIN = "super_admin"

ALL_ROLES = [
    ROLE_STUDENT,
    ROLE_CONTRIBUTOR,
    ROLE_REVIEWER,
    ROLE_MEDICAL_REVIEWER,
    ROLE_MODERATOR,
    ROLE_CONTENT_ADMIN,
    ROLE_SUPER_ADMIN,
]


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    supabase_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), unique=True, index=True)
    display_name: Mapped[Optional[str]] = mapped_column(String(255))
    avatar_url: Mapped[Optional[str]] = mapped_column(String(512))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Profile (spec §18) — optional, never required for use.
    course: Mapped[Optional[str]] = mapped_column(String(100))
    year_of_study: Mapped[Optional[str]] = mapped_column(String(30))
    university: Mapped[Optional[str]] = mapped_column(String(255))
    country: Mapped[Optional[str]] = mapped_column(String(100))
    preferred_language: Mapped[Optional[str]] = mapped_column(String(20), default="en")
    study_goal: Mapped[Optional[str]] = mapped_column(String(300))

    roles: Mapped[list["UserRole"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

    @property
    def highest_role(self) -> str:
        rank = {
            ROLE_STUDENT: 0,
            ROLE_CONTRIBUTOR: 1,
            ROLE_REVIEWER: 2,
            ROLE_MEDICAL_REVIEWER: 3,
            ROLE_MODERATOR: 4,
            ROLE_CONTENT_ADMIN: 5,
            ROLE_SUPER_ADMIN: 6,
        }
        return max((r.role for r in self.roles), key=lambda r: rank.get(r, 0))


class UserRole(Base):
    __tablename__ = "user_roles"
    __table_args__ = (UniqueConstraint("user_id", "role", name="uq_user_role"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    role: Mapped[str] = mapped_column(String(50))

    user: Mapped[User] = relationship(back_populates="roles")
