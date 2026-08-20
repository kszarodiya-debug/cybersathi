"""Health-check routes."""

from fastapi import APIRouter

from app.core.config import settings
from app.schemas.health import HealthResponse


router = APIRouter(tags=["system"])


@router.get("/health", response_model=HealthResponse)
def versioned_health_check() -> HealthResponse:
    """Return the API liveness response under the versioned API prefix."""

    return HealthResponse(
        status="ok",
        service="cybersathi-api",
        version=settings.app_version,
    )
