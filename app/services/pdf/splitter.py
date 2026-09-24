import io
from typing import List
from pypdf import PdfReader, PdfWriter
import structlog
from app.core.exceptions import InvalidDocumentException

logger = structlog.get_logger(__name__)


class PDFSplitter:
    """Handles PDF page extraction and batch splitting for large documents."""

    @staticmethod
    def extract_page_range(content: bytes, start_page: int, end_page: int) -> bytes:
        """
        Extracts a specific 1-indexed page range [start_page, end_page] from PDF bytes.
        """
        try:
            reader = PdfReader(io.BytesIO(content))
            total_pages = len(reader.pages)

            if start_page < 1 or end_page > total_pages or start_page > end_page:
                raise InvalidDocumentException(
                    f"Invalid page range {start_page}-{end_page}. Document has {total_pages} pages."
                )

            writer = PdfWriter()
            for idx in range(start_page - 1, end_page):
                writer.add_page(reader.pages[idx])

            output_stream = io.BytesIO()
            writer.write(output_stream)
            return output_stream.getvalue()

        except Exception as e:
            logger.error("Failed to extract page range", start=start_page, end=end_page, error=str(e))
            raise InvalidDocumentException(f"Failed to split PDF: {str(e)}") from e

    @classmethod
    def split_into_batches(cls, content: bytes, batch_size: int = 10) -> List[bytes]:
        """
        Splits PDF bytes into sequential batches of max `batch_size` pages.
        """
        try:
            reader = PdfReader(io.BytesIO(content))
            total_pages = len(reader.pages)
            batches: List[bytes] = []

            for start in range(1, total_pages + 1, batch_size):
                end = min(start + batch_size - 1, total_pages)
                batch_bytes = cls.extract_page_range(content, start, end)
                batches.append(batch_bytes)

            return batches
        except Exception as e:
            logger.error("Batch splitting failed", error=str(e))
            raise InvalidDocumentException(f"Failed to batch split PDF: {str(e)}") from e
