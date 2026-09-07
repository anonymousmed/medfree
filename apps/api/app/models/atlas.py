"""Human Atlas — first-class system (centerpiece of the product).

An anatomical structure is the canonical node. 3D models reference structures
through ``atlas_model_parts``; annotations and relationships link everything.
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy import Boolean, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class AnatomicalRegion(Base):
    __tablename__ = "anatomical_regions"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(150))
    parent_id: Mapped[Optional[int]] = mapped_column(ForeignKey("anatomical_regions.id"))
    sort_order: Mapped[int] = mapped_column(Integer, default=0)


class AnatomicalSystem(Base):
    __tablename__ = "anatomical_systems"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(150))
    icon: Mapped[Optional[str]] = mapped_column(String(50))
    sort_order: Mapped[int] = mapped_column(Integer, default=0)


class AnatomicalStructure(Base):
    __tablename__ = "anatomical_structures"

    id: Mapped[int] = mapped_column(primary_key=True)
    stable_structure_id: Mapped[Optional[str]] = mapped_column(String(120), unique=True, index=True)
    preferred_name: Mapped[str] = mapped_column(String(200), index=True)
    latin_name: Mapped[Optional[str]] = mapped_column(String(200))
    synonyms: Mapped[Optional[str]] = mapped_column(Text)
    region_id: Mapped[Optional[int]] = mapped_column(ForeignKey("anatomical_regions.id"))
    system_id: Mapped[Optional[int]] = mapped_column(ForeignKey("anatomical_systems.id"))
    parent_id: Mapped[Optional[int]] = mapped_column(ForeignKey("anatomical_structures.id"))
    description: Mapped[Optional[str]] = mapped_column(Text)
    clinical_notes: Mapped[Optional[str]] = mapped_column(Text)
    surface_anatomy: Mapped[Optional[str]] = mapped_column(Text)
    embryology: Mapped[Optional[str]] = mapped_column(Text)
    histology: Mapped[Optional[str]] = mapped_column(Text)
    radiology: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), default="review_required")


class AnatomicalRelationship(Base):
    __tablename__ = "anatomical_relationships"

    id: Mapped[int] = mapped_column(primary_key=True)
    structure_a: Mapped[int] = mapped_column(ForeignKey("anatomical_structures.id", ondelete="CASCADE"))
    structure_b: Mapped[int] = mapped_column(ForeignKey("anatomical_structures.id", ondelete="CASCADE"))
    relation_type: Mapped[str] = mapped_column(String(50))  # e.g. "supplies", "medial_to"
    description: Mapped[Optional[str]] = mapped_column(Text)
    source: Mapped[Optional[str]] = mapped_column(String(300))


class AtlasModel(Base):
    __tablename__ = "atlas_models"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    source: Mapped[Optional[str]] = mapped_column(String(300))
    license: Mapped[Optional[str]] = mapped_column(String(100))
    creator: Mapped[Optional[str]] = mapped_column(String(200))
    file_key: Mapped[str] = mapped_column(String(500))
    format: Mapped[str] = mapped_column(String(20), default="glb")
    version: Mapped[str] = mapped_column(String(30), default="1.0.0")
    checksum: Mapped[Optional[str]] = mapped_column(String(64))
    region_id: Mapped[Optional[int]] = mapped_column(ForeignKey("anatomical_regions.id"))
    optimization_status: Mapped[str] = mapped_column(String(40), default="pending")
    review_status: Mapped[str] = mapped_column(String(40), default="review_required")
    default_visibility: Mapped[Optional[dict]] = mapped_column(JSON)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False)


class AtlasModelPart(Base):
    __tablename__ = "atlas_model_parts"

    id: Mapped[int] = mapped_column(primary_key=True)
    model_id: Mapped[int] = mapped_column(ForeignKey("atlas_models.id", ondelete="CASCADE"))
    structure_id: Mapped[Optional[int]] = mapped_column(ForeignKey("anatomical_structures.id", ondelete="SET NULL"))
    mesh_name: Mapped[str] = mapped_column(String(200))
    material: Mapped[Optional[str]] = mapped_column(String(200))
    visibility: Mapped[bool] = mapped_column(Boolean, default=True)
    highlight_config: Mapped[Optional[dict]] = mapped_column(JSON)


class AtlasAnnotation(Base):
    __tablename__ = "atlas_annotations"

    id: Mapped[int] = mapped_column(primary_key=True)
    model_id: Mapped[int] = mapped_column(ForeignKey("atlas_models.id", ondelete="CASCADE"))
    structure_id: Mapped[Optional[int]] = mapped_column(ForeignKey("anatomical_structures.id", ondelete="SET NULL"))
    label: Mapped[str] = mapped_column(String(200))
    description: Mapped[Optional[str]] = mapped_column(Text)
    position_x: Mapped[Optional[float]] = mapped_column(Float)
    position_y: Mapped[Optional[float]] = mapped_column(Float)
    position_z: Mapped[Optional[float]] = mapped_column(Float)


class AtlasReview(Base):
    __tablename__ = "atlas_reviews"

    id: Mapped[int] = mapped_column(primary_key=True)
    model_id: Mapped[int] = mapped_column(ForeignKey("atlas_models.id", ondelete="CASCADE"))
    reviewer: Mapped[str] = mapped_column(String(150))
    review_type: Mapped[str] = mapped_column(String(40))  # medical / quality / rights
    result: Mapped[str] = mapped_column(String(40))  # approved / rejected / changes_requested
    notes: Mapped[Optional[str]] = mapped_column(Text)
