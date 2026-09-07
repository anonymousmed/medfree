from pydantic import BaseModel, ConfigDict


class PracticalStepRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    position: int
    step_text: str
    observation: str | None = None


class PracticalRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    subject_slug: str
    topic_slug: str | None = None
    title: str
    objective: str | None = None
    video_url: str | None = None
    is_published: bool


class PracticalDetail(PracticalRead):
    requirements: str | None = None
    principle: str | None = None
    preparation: str | None = None
    observation: str | None = None
    interpretation: str | None = None
    common_mistakes: str | None = None
    safety_notes: str | None = None
    clinical_significance: str | None = None
    reference_text: str | None = None
    steps: list[PracticalStepRead] = []
