from pydantic import BaseModel, ConfigDict


class AtlasRegionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    name: str
    parent_id: int | None = None


class AtlasStructureRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    preferred_name: str
    latin_name: str | None = None
    synonyms: str | None = None
    region_id: int | None = None
    system_id: int | None = None
    description: str | None = None
    clinical_notes: str | None = None


class AtlasModelRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    format: str
    version: str
    file_key: str
    license: str | None = None
    is_published: bool


class AtlasSearchResult(BaseModel):
    id: int
    preferred_name: str
    region_slug: str | None = None
    type: str = "structure"
