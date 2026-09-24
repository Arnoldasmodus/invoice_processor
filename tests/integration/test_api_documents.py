from unittest.mock import AsyncMock
import pytest
from httpx import AsyncClient
from app.api.dependencies import get_analyzer_service, validate_api_key
from app.main import app
from app.models.response import AnalyzeDocumentResponse, InvoiceExtractionResponse


@pytest.mark.asyncio
async def test_health_live(async_client: AsyncClient):
    response = await async_client.get("/api/v1/health/live")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


@pytest.mark.asyncio
async def test_analyze_document_endpoint(async_client: AsyncClient, valid_pdf_bytes: bytes):
    # Mock analyzer service
    mock_analyzer = AsyncMock()
    mock_analyzer.analyze_document_stream.return_value = AnalyzeDocumentResponse(
        model_id="prebuilt-invoice",
        page_count=1,
        content="Invoice 12345",
        metadata={"execution_time_ms": 100},
        invoice_data=InvoiceExtractionResponse(
            invoice_id="INV-12345",
            vendor_name="Acme Corp",
            invoice_total=500.0,
            currency="EUR",
        ),
    )

    app.dependency_overrides[get_analyzer_service] = lambda: mock_analyzer
    app.dependency_overrides[validate_api_key] = lambda: "test-key"

    try:
        files = {"file": ("invoice.pdf", valid_pdf_bytes, "application/pdf")}
        response = await async_client.post("/api/v1/documents/analyze", files=files)

        assert response.status_code == 200
        data = response.json()
        assert data["model_id"] == "prebuilt-invoice"
        assert data["invoice_data"]["invoice_id"] == "INV-12345"
        assert data["invoice_data"]["vendor_name"] == "Acme Corp"
    finally:
        app.dependency_overrides.clear()
