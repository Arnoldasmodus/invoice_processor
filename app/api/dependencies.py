from functools import lru_cache
from typing import AsyncGenerator
from fastapi import Depends
from app.core.config import Settings, get_settings
from app.core.security import validate_api_key
from app.services.document_intelligence.analyzer import DocumentAnalyzerService
from app.services.document_intelligence.client import DocumentIntelligenceClientManager
from app.services.document_intelligence.parser import DocumentIntelligenceParser
from app.services.document_service import DocumentService
from app.services.health_service import HealthService
from app.services.pdf.validator import PDFValidator
from app.services.pdf.splitter import PDFSplitter
from app.services.storage.base import BaseStorageService
from app.services.storage.local_storage import LocalStorageService


@lru_cache
def get_azure_client_manager(
    settings: Settings = Depends(get_settings),
) -> DocumentIntelligenceClientManager:
    """Dependency provider for Azure Document Intelligence client manager."""
    return DocumentIntelligenceClientManager(settings=settings)


def get_document_parser() -> DocumentIntelligenceParser:
    """Dependency provider for document parser."""
    return DocumentIntelligenceParser()


def get_pdf_validator(
    settings: Settings = Depends(get_settings),
) -> PDFValidator:
    """Dependency provider for PDF validator."""
    return PDFValidator(settings=settings)


def get_pdf_splitter() -> PDFSplitter:
    """Dependency provider for PDF splitter."""
    return PDFSplitter()


def get_storage_service(
    settings: Settings = Depends(get_settings),
) -> BaseStorageService:
    """Dependency provider for document storage service."""
    return LocalStorageService(settings=settings)


def get_analyzer_service(
    settings: Settings = Depends(get_settings),
    client_manager: DocumentIntelligenceClientManager = Depends(get_azure_client_manager),
    parser: DocumentIntelligenceParser = Depends(get_document_parser),
) -> DocumentAnalyzerService:
    """Dependency provider for DocumentAnalyzerService."""
    return DocumentAnalyzerService(
        settings=settings,
        client_manager=client_manager,
        parser=parser,
    )


def get_document_service(
    settings: Settings = Depends(get_settings),
    analyzer: DocumentAnalyzerService = Depends(get_analyzer_service),
    pdf_validator: PDFValidator = Depends(get_pdf_validator),
    storage: BaseStorageService = Depends(get_storage_service),
) -> DocumentService:
    """Dependency provider for DocumentService workflow orchestrator."""
    return DocumentService(
        settings=settings,
        analyzer=analyzer,
        pdf_validator=pdf_validator,
        storage=storage,
    )


def get_health_service(
    settings: Settings = Depends(get_settings),
) -> HealthService:
    """Dependency provider for HealthService."""
    return HealthService(settings=settings)
