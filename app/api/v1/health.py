from fastapi import APIRouter, Depends, status
from app.api.dependencies import get_health_service
from app.models.response import HealthResponse
from app.services.health_service import HealthService

router = APIRouter(prefix="/health", tags=["Health Checks"])


@router.get(
    "/live",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Liveness probe",
)
async def liveness(
    service: HealthService = Depends(get_health_service),
) -> HealthResponse:
    """Check application liveness."""
    return service.get_liveness()


@router.get(
    "/ready",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Readiness probe",
)
async def readiness(
    service: HealthService = Depends(get_health_service),
) -> HealthResponse:
    """Check external dependencies readiness."""
    return service.get_readiness()
