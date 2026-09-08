from fastapi import APIRouter

from app.api.routes import (
    admin,
    admin_content,
    admin_library,
    ai,
    analytics,
    atlas,
    auth,
    books,
    flashcards,
    gamification,
    health,
    me,
    partnerships,
    platform,
    practicals,
    progress,
    questions,
    reports,
    resources,
    search,
    security,
    storage,
    subjects,
    viva,
)

api_router = APIRouter()

api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(me.router)
api_router.include_router(subjects.router)
api_router.include_router(atlas.router)
api_router.include_router(books.router)
api_router.include_router(search.router)
api_router.include_router(resources.router)
api_router.include_router(questions.router)
api_router.include_router(viva.router)
api_router.include_router(flashcards.router)
api_router.include_router(practicals.router)
api_router.include_router(progress.router)
api_router.include_router(ai.router)
api_router.include_router(gamification.router)
api_router.include_router(platform.router)
api_router.include_router(analytics.router)
api_router.include_router(analytics.admin_router)
api_router.include_router(security.router)
api_router.include_router(partnerships.router)
api_router.include_router(partnerships.admin_router)
api_router.include_router(storage.router)
api_router.include_router(reports.router)
api_router.include_router(reports.admin_router)
api_router.include_router(admin_content.router)
api_router.include_router(admin_library.router)
api_router.include_router(admin.router)
