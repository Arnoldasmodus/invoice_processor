import io
from unittest.mock import AsyncMock, MagicMock
import pytest
from fastapi import HTTPException, UploadFile
from app.core.config import Settings
from app.core.constants import DocumentModelId
from app.core.exceptions import InvalidDocumentException
from app.models.response import AnalyzeDocumentResponse, InvoiceExtractionResponse
from app.services.document_intelligence.analyzer import DocumentAnalyzerService
from app.services.document_service import DocumentService
from app.services.pdf.validator import PDFValidator
from app.services.storage.base import BaseStorageService


@pytest.fixture
def mock_analyzer():
    analyzer = MagicMock(spec=DocumentAnalyzerService)
    analyzer.analyze_document_stream = AsyncMock()
    return analyzer


@pytest.fixture
def mock_pdf_validator():
    validator = MagicMock(spec=PDFValidator)
    validator.validate_pdf_bytes.return_value = (1, True)
    return validator


@pytest.fixture
def mock_storage():
    storage = MagicMock(spec=BaseStorageService)
    storage.save_file = AsyncMock(return_value="stored-key-123")
    return storage


@pytest.fixture
def document_service(mock_analyzer, mock_pdf_validator, mock_storage, test_settings):
    return DocumentService(
        settings=test_settings,
        analyzer=mock_analyzer,
        pdf_validator=mock_pdf_validator,
        storage=mock_storage,
    )


@pytest.mark.asyncio
async def test_analyze_document_success(document_service, mock_analyzer, valid_pdf_bytes):
    mock_analyzer.analyze_document_stream.return_value = AnalyzeDocumentResponse(
        model_id=DocumentModelId.INVOICE.value,
        page_count=1,
        content="Analyzed content",
        metadata={},
    )

    upload_file = UploadFile(
        file=io.BytesIO(valid_pdf_bytes),
        filename="test.pdf",
        headers={"content-type": "application/pdf"},
    )

    response = await document_service.analyze_document(upload_file, save_to_storage=True)

    assert response.model_id == DocumentModelId.INVOICE.value
    assert response.metadata["storage_key"] == "stored-key-123"
    assert response.metadata["original_filename"] == "test.pdf"


@pytest.mark.asyncio
async def test_analyze_document_invalid_mime(document_service):
    upload_file = UploadFile(
        file=io.BytesIO(b"fake data"),
        filename="test.txt",
        headers={"content-type": "text/plain"},
    )

    with pytest.raises(InvalidDocumentException):
        await document_service.analyze_document(upload_file)


@pytest.mark.asyncio
async def test_extract_invoice_missing_data(document_service, mock_analyzer, valid_pdf_bytes):
    mock_analyzer.analyze_document_stream.return_value = AnalyzeDocumentResponse(
        model_id=DocumentModelId.INVOICE.value,
        page_count=1,
        invoice_data=None,
    )

    upload_file = UploadFile(
        file=io.BytesIO(valid_pdf_bytes),
        filename="invoice.pdf",
        headers={"content-type": "application/pdf"},
    )

    with pytest.raises(HTTPException) as exc_info:
        await document_service.extract_invoice(upload_file)

    assert exc_info.value.status_code == 422
