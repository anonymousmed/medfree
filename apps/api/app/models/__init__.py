"""Import all models so Alembic autogenerate sees them."""
from app.models.analytics import AnalyticsEvent, SearchEvent
from app.models.atlas import (
    AnatomicalRelationship,
    AnatomicalRegion,
    AnatomicalStructure,
    AnatomicalSystem,
    AtlasAnnotation,
    AtlasModel,
    AtlasModelPart,
)
from app.models.content import (
    Author,
    Book,
    BookChapter,
    License,
    Resource,
    ResourceVersion,
)
from app.models.content_platform import Ad, Announcement
from app.models.embedding import ContentEmbedding
from app.models.gamification import (
    GamificationEvent,
    UserBadge,
    UserStreak,
    XPTransaction,
)
from app.models.partnership import Institution, PartnershipRequest
from app.models.practice import (
    Flashcard,
    Practical,
    PracticalStep,
    Question,
    QuestionOption,
    VivaQuestion,
)
from app.models.progress import (
    Bookmark,
    FlashcardReview,
    Note,
    QuizAttempt,
    StudySession,
    UserProgress,
    VivaAttempt,
)
from app.models.report import Report
from app.models.security import AuditLog
from app.models.subject import Subject, Topic, TopicBlock, TopicLink
from app.models.user import User, UserRole

__all__ = [
    "User",
    "UserRole",
    "Subject",
    "Topic",
    "TopicBlock",
    "TopicLink",
    "Bookmark",
    "Note",
    "License",
    "Resource",
    "ResourceVersion",
    "Author",
    "Book",
    "BookChapter",
    "AnatomicalRegion",
    "AnatomicalSystem",
    "AnatomicalStructure",
    "AnatomicalRelationship",
    "AtlasModel",
    "AtlasModelPart",
    "AtlasAnnotation",
    "Question",
    "QuestionOption",
    "VivaQuestion",
    "Flashcard",
    "Practical",
    "PracticalStep",
    "UserProgress",
    "QuizAttempt",
    "VivaAttempt",
    "FlashcardReview",
    "StudySession",
    "UserBadge",
    "UserStreak",
    "XPTransaction",
    "GamificationEvent",
    "Ad",
    "Announcement",
    "AnalyticsEvent",
    "SearchEvent",
    "AuditLog",
    "Institution",
    "PartnershipRequest",
    "ContentEmbedding",
    "Report",
]
