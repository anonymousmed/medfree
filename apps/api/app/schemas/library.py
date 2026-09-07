from pydantic import BaseModel, ConfigDict


class AuthorRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    affiliation: str | None = None
    website: str | None = None


class BookRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    edition: str | None = None
    publisher: str | None = None
    isbn: str | None = None
    year: int | None = None
    subject_slug: str | None = None


class BookChapterRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    chapter_index: int
    topic_slug: str | None = None


class BookDetail(BookRead):
    source_url: str | None = None
    rights_status: str | None = None
    license_name: str | None = None
    author: AuthorRead | None = None
    chapters: list[BookChapterRead] = []


class SearchResult(BaseModel):
    type: str  # structure/topic/book/resource/question/viva
    id: int
    title: str
    subtitle: str | None = None
    href: str | None = None


class ResourceFilter(BaseModel):
    resource_type: str | None = None
    license: str | None = None
    rights_status: str | None = None
    subject: str | None = None
    q: str | None = None
