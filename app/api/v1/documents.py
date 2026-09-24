from typing import Optional
from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from app.api.dependencies import get_document_service
from app.core.constants import DocumentModelId
from app.core.security import validate_api_key
from app.models.response import AnalyzeDocumentResponse, InvoiceExtractionResponse
from app.services.document_service import DocumentService

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post(
    "/analyze",
    response_model=AnalyzeDocumentResponse,
    status_code=status.HTTP_200_OK,
    summary="Upload and analyze a PDF document",
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
    service: DocumentService = Depends(get_document_service),
) -> AnalyzeDocumentResponse:
    """Uploads and analyzes a PDF document."""
    return await service.analyze_document(
        file=file,
        model_id=model_id,
        pages=pages,
        locale=locale,
        save_to_storage=save_to_storage,
    )


@router.post(
    "/extract/invoice",
    response_model=InvoiceExtractionResponse,
    status_code=status.HTTP_200_OK,
    summary="Direct invoice extraction endpoint",
)
async def extract_invoice(
    file: UploadFile = File(..., description="PDF invoice file to extract"),
    pages: Optional[str] = Form(default=None, description="Page range or selection"),
    _api_key: str = Depends(validate_api_key),
    service: DocumentService = Depends(get_document_service),
) -> InvoiceExtractionResponse:
    """Directly extracts structured invoice data from a PDF."""
    return await service.extract_invoice(
        file=file,
        pages=pages,
    )


@router.post(
    "/scan-document",
    response_model=AnalyzeDocumentResponse,
    status_code=status.HTTP_200_OK,
    operation_id="Scan_Document",
    name="Scan_Document",
    summary="Scan document",
)
@router.post(
    "/Scan_Document",
    response_model=AnalyzeDocumentResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
async def scan_document(
    file: UploadFile = File(..., description="Document file to scan (PDF, PNG, JPEG, TIFF, BMP)"),
    model_id: DocumentModelId = Form(
        default=DocumentModelId.LAYOUT,
        description="Azure Document Intelligence model ID to use for scanning",
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
    service: DocumentService = Depends(get_document_service),
) -> AnalyzeDocumentResponse:
    """Scans and analyzes a document (PDF, PNG, JPEG, TIFF, BMP)."""
    return await service.scan_document(
        file=file,
        model_id=model_id,
        pages=pages,
        locale=locale,
        save_to_storage=save_to_storage,
    )
