from fastapi import APIRouter

from app.core.config import settings
from app.schemas.common import HealthRead

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthRead)
async def health() -> HealthRead:
    return HealthRead(
        status="ok",
        version="0.1.0",
        environment=settings.environment,
    )
