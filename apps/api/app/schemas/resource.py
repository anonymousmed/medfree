from pydantic import BaseModel, ConfigDict, Field


class ResourceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    resource_type: str
    creator: str | None = None
    publisher: str | None = None
    source_url: str | None = None
    rights_status: str
    ai_usage_status: str
    review_status: str
    visibility: str


class ResourceUploadRequest(BaseModel):
    """Metadata for an admin upload. The file bytes are streamed via a signed
    upload URL to object storage; this payload records the metadata after the
    rights/license/review gates. POSTing here is guarded by require_admin."""

    title: str = Field(min_length=1, max_length=300)
    resource_type: str = Field(min_length=1, max_length=60)
    creator: str | None = None
    publisher: str | None = None
    source_url: str | None = None
    storage_key: str | None = None
    license_name: str | None = None
    rights_status: str = "review_required"
    ai_usage_status: str = "unknown"
    attribution_text: str | None = None
    visibility: str = "private"


class ResourceSubmissionRequest(BaseModel):
    """Contributor submission (goes to review, does NOT publish)."""

    title: str = Field(min_length=1, max_length=300)
    resource_type: str = Field(min_length=1, max_length=60)
    notes: str | None = None
    storage_key: str | None = None
