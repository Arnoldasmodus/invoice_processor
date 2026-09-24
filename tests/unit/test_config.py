from app.core.config import Settings


def test_settings_default_values():
    settings = Settings(
        AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT="https://test.cognitiveservices.azure.com/",
        AZURE_DOCUMENT_INTELLIGENCE_KEY="dummy",
    )
    assert settings.APP_NAME == "Invoice Processor API"
    assert settings.API_V1_PREFIX == "/api/v1"
    assert settings.MAX_FILE_SIZE_MB == 20
    assert settings.max_file_size_bytes == 20 * 1024 * 1024
