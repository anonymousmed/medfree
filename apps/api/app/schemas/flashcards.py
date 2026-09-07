from pydantic import BaseModel, ConfigDict


class FlashcardRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    subject_slug: str
    topic_slug: str | None = None
    front: str
    back: str
    card_type: str


class FlashcardReviewRequest(BaseModel):
    quality: int  # 0-5


class FlashcardReviewResult(BaseModel):
    id: int
    quality: int
    interval_days: int
    due_at: str


class FlashcardStats(BaseModel):
    total_cards: int
    due_now: int
    reviewed: int
    average_interval_days: float
