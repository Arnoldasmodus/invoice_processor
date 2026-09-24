from app.core.config import Settings
from app.services.health_service import HealthService


def test_health_service_liveness():
    settings = Settings(APP_VERSION="1.0.0", ENVIRONMENT="test")
    service = HealthService(settings=settings)
    result = service.get_liveness()

    assert result.status == "ok"
    assert result.version == "1.0.0"
    assert result.environment == "test"
    assert result.details == {"live": True}


def test_health_service_readiness_configured():
    settings = Settings(
        APP_VERSION="1.0.0",
        ENVIRONMENT="test",
        AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT="https://test.cognitiveservices.azure.com/",
        AZURE_DOCUMENT_INTELLIGENCE_KEY="secret-key",
        STORAGE_TYPE="local",
    )
    service = HealthService(settings=settings)
    result = service.get_readiness()

    assert result.status == "ready"
    assert result.details["azure_configured"] is True
    assert result.details["storage_type"] == "local"


def test_health_service_readiness_degraded():
    settings = Settings(
        APP_VERSION="1.0.0",
        ENVIRONMENT="test",
        AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT="",
        AZURE_DOCUMENT_INTELLIGENCE_KEY="",
    )
    service = HealthService(settings=settings)
    result = service.get_readiness()

    assert result.status == "degraded"
    assert result.details["azure_configured"] is False
