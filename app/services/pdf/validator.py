import io
from typing import Tuple
from pypdf import PdfReader
from pypdf.errors import PdfReadError
import structlog
from app.core.config import Settings
from app.core.exceptions import DocumentSizeLimitExceededException, InvalidDocumentException

logger = structlog.get_logger(__name__)


class PDFValidator:
    """Validates PDF size, structure, encryption, and corruption."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def validate_size(self, file_size: int) -> None:
        """Validates that file size does not exceed configured limits."""
        if file_size > self.settings.max_file_size_bytes:
            raise DocumentSizeLimitExceededException(
                f"File size {file_size / (1024 * 1024):.2f}MB exceeds limit of {self.settings.MAX_FILE_SIZE_MB}MB.",
                details={"file_size": file_size, "max_allowed_mb": self.settings.MAX_FILE_SIZE_MB},
            )

    def validate_pdf_bytes(self, content: bytes) -> Tuple[int, bool]:
        """
        Validates PDF content integrity, encryption, and page count.
        Returns (page_count, is_valid).
        """
        self.validate_size(len(content))

        try:
            stream = io.BytesIO(content)
            reader = PdfReader(stream)

            if reader.is_encrypted:
                try:
                    # Attempt empty password decryption
                    decrypted = reader.decrypt("")
                    if not decrypted:
                        raise InvalidDocumentException(
                            "PDF is encrypted with password protection.",
                            details={"is_encrypted": True},
                        )
                except Exception as e:
                    raise InvalidDocumentException(
                        "PDF is password protected and cannot be processed.",
                        details={"error": str(e)},
                    ) from e

            page_count = len(reader.pages)
            if page_count == 0:
                raise InvalidDocumentException("PDF contains 0 pages.")

            if page_count > self.settings.MAX_PAGE_COUNT:
                raise DocumentSizeLimitExceededException(
                    f"PDF page count ({page_count}) exceeds allowed maximum of {self.settings.MAX_PAGE_COUNT} pages.",
                    details={"page_count": page_count, "max_pages": self.settings.MAX_PAGE_COUNT},
                )

            return page_count, True

        except (PdfReadError, ValueError) as e:
            logger.warning("PDF parsing validation failed", error=str(e))
            raise InvalidDocumentException(
                f"Corrupted or invalid PDF format: {str(e)}",
                details={"error": str(e)},
            ) from e
