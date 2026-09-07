"""Human Atlas API — first-class system (centerpiece).

Public read endpoints for regions, structures, models and search. Write/upload
of 3D models lives under /admin (see admin.py) and is admin-only.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.models.atlas import (
    AnatomicalRegion,
    AnatomicalRelationship,
    AnatomicalStructure,
    AnatomicalSystem,
    AtlasAnnotation,
    AtlasModel,
    AtlasModelPart,
)
from app.schemas.atlas import (
    AtlasModelRead,
    AtlasRegionRead,
    AtlasSearchResult,
    AtlasStructureRead,
)
from pydantic import BaseModel

router = APIRouter(prefix="/atlas", tags=["atlas"])


@router.get("/regions", response_model=list[AtlasRegionRead])
async def list_regions(session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(AnatomicalRegion).order_by(AnatomicalRegion.sort_order)
    )
    return result.scalars().all()


@router.get("/regions/{slug}", response_model=list[AtlasStructureRead])
async def region_structures(slug: str, session: AsyncSession = Depends(get_session)):
    region = await session.execute(
        select(AnatomicalRegion).where(AnatomicalRegion.slug == slug)
    )
    region_row = region.scalar_one_or_none()
    if region_row is None:
        raise HTTPException(status_code=404, detail="Region not found")
    result = await session.execute(
        select(AnatomicalStructure).where(
            AnatomicalStructure.region_id == region_row.id,
            AnatomicalStructure.status == "verified",
        )
    )
    return result.scalars().all()


@router.get("/structures", response_model=list[AtlasStructureRead])
async def list_structures(
    region: str | None = Query(None),
    system: str | None = Query(None),
    session: AsyncSession = Depends(get_session),
):
    stmt = select(AnatomicalStructure).where(AnatomicalStructure.status == "verified")
    if region:
        stmt = stmt.join(AnatomicalRegion).where(AnatomicalRegion.slug == region)
    if system:
        stmt = stmt.where(AnatomicalStructure.system_id.is_not(None))
    result = await session.execute(stmt.limit(200))
    return result.scalars().all()


@router.get("/structures/{slug}", response_model=AtlasStructureRead)
async def get_structure(slug: str, session: AsyncSession = Depends(get_session)):
    stmt = select(AnatomicalStructure).where(
        or_(
            AnatomicalStructure.preferred_name.ilike(slug.replace("-", " ")),
            AnatomicalStructure.preferred_name.ilike(slug),
        )
    )
    row = (await session.execute(stmt.limit(1))).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Structure not found")
    return row


class StructureRelationRead(BaseModel):
    relation_type: str
    description: str | None = None
    related_structure: str
    related_id: int
    direction: str  # "outgoing" | "incoming"


class AtlasSystemRead(BaseModel):
    id: int
    slug: str
    name: str
    icon: str | None = None


class AnnotationRead(BaseModel):
    id: int
    label: str
    description: str | None = None


class ModelPartRead(BaseModel):
    id: int
    mesh_name: str
    material: str | None = None
    structure_id: int | None = None
    visibility: bool = True


@router.get("/systems", response_model=list[AtlasSystemRead])
async def list_systems(session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(AnatomicalSystem).order_by(AnatomicalSystem.sort_order)
    )
    return result.scalars().all()


@router.get("/structures/{id}/relations", response_model=list[StructureRelationRead])
async def structure_relations(id: int, session: AsyncSession = Depends(get_session)):
    """Relationships where structure `id` is either side, resolving the other side's name."""
    rels = (
        await session.execute(
            select(AnatomicalRelationship).where(
                (AnatomicalRelationship.structure_a == id)
                | (AnatomicalRelationship.structure_b == id)
            )
        )
    ).scalars().all()
    out: list[StructureRelationRead] = []
    for r in rels:
        if r.structure_a == id:
            other_id, direction = r.structure_b, "outgoing"
        else:
            other_id, direction = r.structure_a, "incoming"
        other = (
            await session.execute(
                select(AnatomicalStructure).where(AnatomicalStructure.id == other_id)
            )
        ).scalar_one_or_none()
        out.append(
            StructureRelationRead(
                relation_type=r.relation_type,
                description=r.description,
                related_structure=other.preferred_name if other else str(other_id),
                related_id=other_id,
                direction=direction,
            )
        )
    return out


@router.get("/structures/{id}/annotations", response_model=list[AnnotationRead])
async def structure_annotations(id: int, session: AsyncSession = Depends(get_session)):
    """Annotations (pins/labels) attached to a structure across models."""
    result = await session.execute(
        select(AtlasAnnotation).where(AtlasAnnotation.structure_id == id).limit(20)
    )
    return result.scalars().all()


@router.get("/models/{id}/parts", response_model=list[ModelPartRead])
async def model_parts(id: int, session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(AtlasModelPart).where(AtlasModelPart.model_id == id)
    )
    return result.scalars().all()


@router.get("/models/{id}", response_model=AtlasModelRead)
async def get_model(id: int, session: AsyncSession = Depends(get_session)):
    row = (
        await session.execute(
            select(AtlasModel).where(AtlasModel.id == id, AtlasModel.is_published.is_(True))
        )
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Model not found")
    return row


@router.get("/search", response_model=list[AtlasSearchResult])
async def search(q: str = Query(..., min_length=2), session: AsyncSession = Depends(get_session)):
    needle = f"%{q}%"
    result = await session.execute(
        select(AnatomicalStructure)
        .where(
            or_(
                AnatomicalStructure.preferred_name.ilike(needle),
                AnatomicalStructure.synonyms.ilike(needle),
            )
        )
        .limit(25)
    )
    return [
        AtlasSearchResult(
            id=s.id,
            preferred_name=s.preferred_name,
            type="structure",
        )
        for s in result.scalars().all()
    ]
