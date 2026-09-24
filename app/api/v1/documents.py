import io
from typing import List, Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
import structlog
from app.api.dependencies import (
    get_analyzer_service,
    get_pdf_validator,
    get_storage_service,
)
from app.core.constants import DocumentAnalysisFeature, DocumentModelId
from app.core.exceptions import InvalidDocumentException
from app.core.security import validate_api_key
from app.models.response import AnalyzeDocumentResponse, InvoiceExtractionResponse
from app.services.document_intelligence.analyzer import DocumentAnalyzerService
from app.services.pdf.validator import PDFValidator
from app.services.storage.base import BaseStorageService
from app.utils.file_utils import sanitize_filename

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post(
    "/analyze",
    response_model=AnalyzeDocumentResponse,
    status_code=status.HTTP_200_OK,
    summary="Upload and analyze a PDF document",
    description="Uploads a PDF invoice or document, validates its contents, and extracts structured data using Azure Document Intelligence.",
)
async def analyze_document(
    file: UploadFile = File(..., description="PDF document file to analyze"),
    model_id: DocumentModelId = Form(
        default=DocumentModelId.INVOICE,
        description="Azure Document Intelligence model ID to use for analysis",
    ),
    pages: Optional[str] = Form(
        default=None,
        description="Page range or selection to analyze (e.g., '1-2', '1,3')",
    ),
    locale: Optional[str] = Form(
        default=None,
        description="Locale hint (e.g., 'en-US', 'lt-LT')",
    ),
    save_to_storage: bool = Form(
        default=True,
        description="Whether to persist the uploaded file in document storage",
    ),
    _api_key: str = Depends(validate_api_key),
    analyzer: DocumentAnalyzerService = Depends(get_analyzer_service),
    pdf_validator: PDFValidator = Depends(get_pdf_validator),
    storage: BaseStorageService = Depends(get_storage_service),
) -> AnalyzeDocumentResponse:
    if file.content_type != "application/pdf":
        raise InvalidDocumentException(
            f"Unsupported file type: {file.content_type}. Only application/pdf is supported."
        )

    file_bytes = await file.read()
    if not file_bytes:
        raise InvalidDocumentException("Uploaded file is empty.")

    # Validate PDF structure, encryption, size, and page limits
    page_count, is_valid = pdf_validator.validate_pdf_bytes(file_bytes)

    # Optionally persist in storage
    storage_key = None
    if save_to_storage:
        clean_name = sanitize_filename(file.filename or "invoice.pdf")
        storage_key = await storage.save_file(clean_name, file_bytes)

    # Perform Document Analysis
    stream = io.BytesIO(file_bytes)
    result = await analyzer.analyze_document_stream(
        document_stream=stream,
        model_id=model_id,
        pages=pages,
        locale=locale,
    )

    if storage_key:
        result.metadata["storage_key"] = storage_key
    result.metadata["original_filename"] = file.filename
    result.metadata["detected_pages"] = page_count

    return result


@router.post(
    "/extract/invoice",
    response_model=InvoiceExtractionResponse,
    status_code=status.HTTP_200_OK,
    summary="Direct invoice extraction endpoint",
    description="Streamlined endpoint specifically returning only structured invoice extraction fields.",
)
async def extract_invoice(
    file: UploadFile = File(..., description="PDF invoice file to extract"),
    pages: Optional[str] = Form(default=None),
    _api_key: str = Depends(validate_api_key),
    analyzer: DocumentAnalyzerService = Depends(get_analyzer_service),
    pdf_validator: PDFValidator = Depends(get_pdf_validator),
) -> InvoiceExtractionResponse:
    if file.content_type != "application/pdf":
        raise InvalidDocumentException("Only application/pdf is supported.")

    file_bytes = await file.read()
    pdf_validator.validate_pdf_bytes(file_bytes)

    stream = io.BytesIO(file_bytes)
    result = await analyzer.analyze_document_stream(
        document_stream=stream,
        model_id=DocumentModelId.INVOICE,
        pages=pages,
    )

    if not result.invoice_data:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Failed to extract invoice data from the provided document.",
        )

    return result.invoice_data
