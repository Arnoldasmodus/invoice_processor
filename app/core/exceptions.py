from typing import Any, Dict, Optional
from fastapi import Request, status
from fastapi.responses import JSONResponse
import structlog

logger = structlog.get_logger(__name__)


class InvoiceProcessorException(Exception):
    """Base exception for application."""

    def __init__(self, message: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details or {}


class InvalidDocumentException(InvoiceProcessorException):
    """Raised when uploaded document is corrupted, password-protected, or invalid."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, status_code=status.HTTP_400_BAD_REQUEST, details=details)


class DocumentSizeLimitExceededException(InvoiceProcessorException):
    """Raised when uploaded document exceeds size or page count limits."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, status_code=status.HTTP_413_CONTENT_TOO_LARGE, details=details)


class AzureServiceException(InvoiceProcessorException):
    """Raised when Azure Document Intelligence service fails."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, status_code=status.HTTP_502_BAD_GATEWAY, details=details)


class StorageException(InvoiceProcessorException):
    """Raised when file storage operations fail."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, details=details)


async def custom_exception_handler(request: Request, exc: InvoiceProcessorException) -> JSONResponse:
    """Global handler for application exceptions."""
    logger.error("Application error", path=request.url.path, message=exc.message, status_code=exc.status_code, details=exc.details)
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "type": exc.__class__.__name__,
                "message": exc.message,
                "details": exc.details,
            }
        },
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all unhandled exception handler."""
    logger.exception("Unhandled server error", path=request.url.path, error=str(exc))
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "type": "InternalServerError",
                "message": "An unexpected error occurred while processing your request.",
                "details": {},
            }
        },
    )
