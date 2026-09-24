import io
from unittest.mock import AsyncMock, MagicMock
import pytest
from app.core.config import Settings
from app.core.constants import DocumentModelId
from app.services.document_intelligence.analyzer import DocumentAnalyzerService
from app.services.document_intelligence.client import DocumentIntelligenceClientManager


@pytest.mark.asyncio
async def test_analyzer_service_mocked_azure():
    settings = Settings(
        AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT="https://test.cognitiveservices.azure.com/",
        AZURE_DOCUMENT_INTELLIGENCE_KEY="secret-key",
    )

    # Mock Azure Poller & Client
    mock_result = MagicMock()
    mock_result.pages = [MagicMock()]
    mock_result.content = "Sample invoice text"
    mock_result.tables = []
    mock_result.key_value_pairs = []
    mock_result.documents = []

    mock_poller = AsyncMock()
    mock_poller.result.return_value = mock_result

    mock_azure_client = AsyncMock()
    mock_azure_client.begin_analyze_document.return_value = mock_poller

    mock_client_manager = MagicMock(spec=DocumentIntelligenceClientManager)
    mock_client_manager.get_client.return_value = mock_azure_client

    analyzer = DocumentAnalyzerService(
        settings=settings,
        client_manager=mock_client_manager,
    )

    stream = io.BytesIO(b"%PDF-1.4 mock content")
    response = await analyzer.analyze_document_stream(
        document_stream=stream,
        model_id=DocumentModelId.INVOICE,
    )

    assert response.model_id == DocumentModelId.INVOICE.value
    assert response.page_count == 1
    assert response.content == "Sample invoice text"
    assert "execution_time_ms" in response.metadata
