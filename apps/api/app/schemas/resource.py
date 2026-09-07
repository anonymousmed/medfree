from pydantic import BaseModel, ConfigDict, Field, computed_field


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
    local_storage_key: str | None = None

    @computed_field  # type: ignore[misc]
    @property
    def read_url(self) -> str | None:
        """Stable in-browser URL for a public, published resource (e.g. a PDF
        that the browser renders inline). Only exposed when the resource is
        actually public + published, matching the storage-access gate."""
        if not self.local_storage_key:
            return None
        if self.visibility != "public" or self.review_status != "published":
            return None
        from app.core.storage import get_storage

        return get_storage().get_public_url(self.local_storage_key)


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
