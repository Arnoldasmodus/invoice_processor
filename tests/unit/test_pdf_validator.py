import pytest
from app.core.config import Settings
from app.core.exceptions import DocumentSizeLimitExceededException, InvalidDocumentException
from app.services.pdf.validator import PDFValidator


def test_pdf_validator_valid_pdf(valid_pdf_bytes: bytes):
    settings = Settings(MAX_FILE_SIZE_MB=5, MAX_PAGE_COUNT=10)
    validator = PDFValidator(settings=settings)

    page_count, is_valid = validator.validate_pdf_bytes(valid_pdf_bytes)
    assert is_valid is True
    assert page_count == 1


def test_pdf_validator_size_exceeded():
    settings = Settings(MAX_FILE_SIZE_MB=1)
    validator = PDFValidator(settings=settings)

    with pytest.raises(DocumentSizeLimitExceededException):
        validator.validate_size(2 * 1024 * 1024)


def test_pdf_validator_corrupt_bytes():
    settings = Settings(MAX_FILE_SIZE_MB=5, MAX_PAGE_COUNT=10)
    validator = PDFValidator(settings=settings)

    with pytest.raises(InvalidDocumentException):
        validator.validate_pdf_bytes(b"not-a-pdf-corrupt-data")
