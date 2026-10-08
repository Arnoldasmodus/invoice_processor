from unittest.mock import AsyncMock
import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from app.api.dependencies import get_document_service
from app.models.response import AnalyzeDocumentResponse, InvoiceExtractionResponse
from app.services.document_service import DocumentService


@pytest.mark.asyncio
async def test_health_live(async_client: AsyncClient):
    response = await async_client.get("/api/v1/health/live")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


@pytest.mark.asyncio
async def test_analyze_document_endpoint(app: FastAPI, async_client: AsyncClient, valid_pdf_bytes: bytes):
    mock_service = AsyncMock(spec=DocumentService)
    mock_service.analyze_document.return_value = AnalyzeDocumentResponse(
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

    app.dependency_overrides[get_document_service] = lambda: mock_service

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


@pytest.mark.asyncio
async def test_scan_document_endpoint(app: FastAPI, async_client: AsyncClient, valid_pdf_bytes: bytes):
    mock_service = AsyncMock(spec=DocumentService)
    mock_service.scan_document.return_value = AnalyzeDocumentResponse(
        model_id="prebuilt-layout",
        page_count=1,
        content="Scanned Document text",
        metadata={"execution_time_ms": 120},
    )

    app.dependency_overrides[get_document_service] = lambda: mock_service

    try:
        files = {"file": ("document.pdf", valid_pdf_bytes, "application/pdf")}
        response = await async_client.post(
            "/api/v1/documents/scan-document",
            files=files,
            data={"model_id": "prebuilt-layout"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["model_id"] == "prebuilt-layout"
        assert data["content"] == "Scanned Document text"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_extract_invoice_endpoint(app: FastAPI, async_client: AsyncClient, valid_pdf_bytes: bytes):
    mock_service = AsyncMock(spec=DocumentService)
    mock_service.extract_invoice.return_value = InvoiceExtractionResponse(
        invoice_id="INV-999",
        vendor_name="Global Vendor",
        invoice_total=1250.50,
        currency="EUR",
    )

    app.dependency_overrides[get_document_service] = lambda: mock_service

    try:
        files = {"file": ("invoice.pdf", valid_pdf_bytes, "application/pdf")}
        response = await async_client.post("/api/v1/documents/extract/invoice", files=files)

        assert response.status_code == 200
        data = response.json()
        assert data["invoice_id"] == "INV-999"
        assert data["vendor_name"] == "Global Vendor"
    finally:
        app.dependency_overrides.clear()


def test_openapi_has_no_authorization_scheme(app: FastAPI):
    openapi = app.openapi()

    assert "securitySchemes" not in openapi.get("components", {})
    assert "security" not in openapi["paths"]["/api/v1/documents/analyze"]["post"]
