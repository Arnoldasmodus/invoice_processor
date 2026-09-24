import io
from typing import List, Optional
from fastapi import HTTPException, UploadFile, status
from app.core.config import Settings
from app.core.constants import DocumentAnalysisFeature, DocumentModelId, SupportedMimeTypes
from app.core.exceptions import InvalidDocumentException
from app.models.response import AnalyzeDocumentResponse, InvoiceExtractionResponse
from app.services.base import BaseService
from app.services.document_intelligence.analyzer import DocumentAnalyzerService
from app.services.pdf.validator import PDFValidator
from app.services.storage.base import BaseStorageService
from app.utils.file_utils import sanitize_filename


class DocumentService(BaseService):
    """Encapsulates document processing, validation, storage, and analysis workflows."""

    def __init__(
        self,
        settings: Settings,
        analyzer: DocumentAnalyzerService,
        pdf_validator: PDFValidator,
        storage: BaseStorageService,
    ) -> None:
        super().__init__(settings)
        self.analyzer = analyzer
        self.pdf_validator = pdf_validator
        self.storage = storage

    async def analyze_document(
        self,
        file: UploadFile,
        model_id: DocumentModelId = DocumentModelId.INVOICE,
        pages: Optional[str] = None,
        locale: Optional[str] = None,
        save_to_storage: bool = True,
    ) -> AnalyzeDocumentResponse:
        """Validates, optionally persists, and analyzes a PDF document."""
        if file.content_type != SupportedMimeTypes.PDF.value:
            raise InvalidDocumentException(
                f"Unsupported file type: {file.content_type}. Only application/pdf is supported."
            )

        file_bytes = await file.read()
        if not file_bytes:
            raise InvalidDocumentException("Uploaded file is empty.")

        page_count, _ = self.pdf_validator.validate_pdf_bytes(file_bytes)

        storage_key = None
        if save_to_storage:
            clean_name = sanitize_filename(file.filename or "invoice.pdf")
            storage_key = await self.storage.save_file(clean_name, file_bytes)

        stream = io.BytesIO(file_bytes)
        result = await self.analyzer.analyze_document_stream(
            document_stream=stream,
            model_id=model_id,
            pages=pages,
            locale=locale,
            content_type="application/pdf",
        )

        if storage_key:
            result.metadata["storage_key"] = storage_key
        result.metadata["original_filename"] = file.filename
        result.metadata["detected_pages"] = page_count

        return result

    async def extract_invoice(
        self,
        file: UploadFile,
        pages: Optional[str] = None,
    ) -> InvoiceExtractionResponse:
        """Validates and directly extracts structured invoice fields."""
        if file.content_type != SupportedMimeTypes.PDF.value:
            raise InvalidDocumentException("Only application/pdf is supported.")

        file_bytes = await file.read()
        if not file_bytes:
            raise InvalidDocumentException("Uploaded file is empty.")

        self.pdf_validator.validate_pdf_bytes(file_bytes)

        stream = io.BytesIO(file_bytes)
        result = await self.analyzer.analyze_document_stream(
            document_stream=stream,
            model_id=DocumentModelId.INVOICE,
            pages=pages,
            content_type="application/pdf",
        )

        if not result.invoice_data:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Failed to extract invoice data from the provided document.",
            )

        return result.invoice_data

    async def scan_document(
        self,
        file: UploadFile,
        model_id: DocumentModelId = DocumentModelId.LAYOUT,
        pages: Optional[str] = None,
        locale: Optional[str] = None,
        save_to_storage: bool = True,
    ) -> AnalyzeDocumentResponse:
        """Validates, optionally persists, and scans a document file (PDF or image)."""
        supported_mimes = [m.value for m in SupportedMimeTypes]
        if file.content_type not in supported_mimes:
            raise InvalidDocumentException(
                f"Unsupported file type: {file.content_type}. Supported types: {', '.join(supported_mimes)}"
            )

        file_bytes = await file.read()
        if not file_bytes:
            raise InvalidDocumentException("Uploaded file is empty.")

        detected_pages = None
        if file.content_type == SupportedMimeTypes.PDF.value:
            page_count, _ = self.pdf_validator.validate_pdf_bytes(file_bytes)
            detected_pages = page_count

        storage_key = None
        if save_to_storage:
            clean_name = sanitize_filename(file.filename or "scanned_document")
            storage_key = await self.storage.save_file(clean_name, file_bytes)

        stream = io.BytesIO(file_bytes)
        result = await self.analyzer.analyze_document_stream(
            document_stream=stream,
            model_id=model_id,
            pages=pages,
            locale=locale,
            content_type=file.content_type or "application/pdf",
        )

        if storage_key:
            result.metadata["storage_key"] = storage_key
        result.metadata["original_filename"] = file.filename
        if detected_pages is not None:
            result.metadata["detected_pages"] = detected_pages

        return result
