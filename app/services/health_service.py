from typing import Any, Dict
from app.core.config import Settings
from app.models.response import HealthResponse
from app.services.base import BaseService


class HealthService(BaseService):
    """Handles application health and readiness checks."""

    def __init__(self, settings: Settings) -> None:
        super().__init__(settings)

    def get_liveness(self) -> HealthResponse:
        """Evaluates whether the application process is running."""
        return HealthResponse(
            status="ok",
            version=self.settings.APP_VERSION,
            environment=self.settings.ENVIRONMENT,
            details={"live": True},
        )

    def get_readiness(self) -> HealthResponse:
        """Evaluates connectivity and configuration of external integrations."""
        azure_configured = bool(
            self.settings.AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT
            and self.settings.AZURE_DOCUMENT_INTELLIGENCE_KEY
        )

        return HealthResponse(
            status="ready" if azure_configured else "degraded",
            version=self.settings.APP_VERSION,
            environment=self.settings.ENVIRONMENT,
            details={
                "azure_configured": azure_configured,
                "storage_type": self.settings.STORAGE_TYPE,
            },
        )
