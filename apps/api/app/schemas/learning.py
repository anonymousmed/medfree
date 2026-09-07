from pydantic import BaseModel, ConfigDict, Field


class TopicBlockRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    position: int
    block_type: str
    title: str
    content: str | None = None
    meta: str | None = None


class TopicDetailForBlocks(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    title: str
    summary: str | None = None
    learning_objectives: str | None = None
    blocks: list[TopicBlockRead]


class TopicBlockUpsert(BaseModel):
    block_type: str = Field(min_length=1, max_length=40)
    title: str = Field(min_length=1, max_length=200)
    content: str | None = None
    meta: str | None = None
    position: int = Field(default=0, ge=0)


class BookmarkCreate(BaseModel):
    target_type: str = Field(min_length=1, max_length=40)
    target_id: int | None = None
    target_slug: str | None = None
    title: str | None = None
    note: str | None = None


class BookmarkRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    target_type: str
    target_id: int | None = None
    target_slug: str | None = None
    title: str | None = None
    note: str | None = None


class NoteCreate(BaseModel):
    target_type: str = Field(min_length=1, max_length=40)
    target_id: int | None = None
    target_slug: str | None = None
    body: str = Field(min_length=1)


class NoteUpdate(BaseModel):
    body: str = Field(min_length=1)
    is_pinned: bool | None = None


class NoteRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    target_type: str
    target_id: int | None = None
    target_slug: str | None = None
    body: str
    is_pinned: bool
