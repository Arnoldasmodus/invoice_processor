from typing import Any, Dict
from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from app.core.config import Settings, get_settings

router = APIRouter(prefix="/health", tags=["Health Checks"])


class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str
    details: Dict[str, Any] = {}


@router.get(
    "/live",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Liveness probe",
)
async def liveness(settings: Settings = Depends(get_settings)) -> HealthResponse:
    """Liveness probe to check if the application process is alive."""
    return HealthResponse(
        status="ok",
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
        details={"live": True},
    )


@router.get(
    "/ready",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Readiness probe",
)
async def readiness(settings: Settings = Depends(get_settings)) -> HealthResponse:
    """Readiness probe to verify all external dependencies and services are accessible."""
    azure_configured = bool(
        settings.AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT and settings.AZURE_DOCUMENT_INTELLIGENCE_KEY
    )
    return HealthResponse(
        status="ready" if azure_configured else "degraded",
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
        details={
            "azure_configured": azure_configured,
            "storage_type": settings.STORAGE_TYPE,
        },
    )
