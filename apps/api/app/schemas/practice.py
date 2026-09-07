from pydantic import BaseModel, ConfigDict, Field


class QuestionOptionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    option_text: str


class QuestionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    subject_slug: str
    topic_slug: str | None = None
    stem: str
    qtype: str
    difficulty: str
    image_url: str | None = None
    options: list[QuestionOptionRead]


class QuestionAttemptRequest(BaseModel):
    selected_option_id: int


class QuestionAttemptResult(BaseModel):
    question_id: int
    selected_option_id: int
    is_correct: bool
    correct_option_id: int
    explanation: str | None = None
    reference: str | None = None


class VivaQuestionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    subject_slug: str
    topic_slug: str | None = None
    prompt: str
    difficulty: str


class VivaAttemptRequest(BaseModel):
    student_answer: str = Field(min_length=1)
    self_rating: int | None = Field(default=None, ge=1, le=5)


class VivaAttemptResult(BaseModel):
    viva_question_id: int
    model_answer: str
    key_points: str | None = None


class FlashcardRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    subject_slug: str
    topic_slug: str | None = None
    front: str
    back: str
    card_type: str


class FlashcardReviewRequest(BaseModel):
    quality: int = Field(ge=0, le=5)


class FlashcardReviewResult(BaseModel):
    id: int
    quality: int
    interval_days: int
    due_at: str
