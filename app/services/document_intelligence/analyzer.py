import time
from typing import BinaryIO, List, Optional
from azure.core.exceptions import AzureError
import structlog
from app.core.config import Settings
from app.core.constants import DocumentAnalysisFeature, DocumentModelId
from app.core.exceptions import AzureServiceException
from app.models.response import AnalyzeDocumentResponse
from app.services.base import BaseService
from app.services.document_intelligence.client import DocumentIntelligenceClientManager
from app.services.document_intelligence.parser import DocumentIntelligenceParser

logger = structlog.get_logger(__name__)


class DocumentAnalyzerService(BaseService):
    """Orchestrates document analysis using Azure Document Intelligence."""

    def __init__(
        self,
        settings: Settings,
        client_manager: DocumentIntelligenceClientManager,
        parser: Optional[DocumentIntelligenceParser] = None,
    ) -> None:
        super().__init__(settings)
        self.client_manager = client_manager
        self.parser = parser or DocumentIntelligenceParser()

    async def analyze_document_stream(
        self,
        document_stream: BinaryIO,
        model_id: DocumentModelId = DocumentModelId.INVOICE,
        pages: Optional[str] = None,
        features: Optional[List[DocumentAnalysisFeature]] = None,
        content_type: str = "application/pdf",
    ) -> AnalyzeDocumentResponse:
        """Submits document stream to Azure Document Intelligence and awaits parsed result."""
        client = self.client_manager.get_client()
        start_time = time.perf_counter()

        try:
            feature_strings = [f.value for f in features] if features else None

            self.logger.info(
                "Starting document analysis",
                model_id=model_id.value,
                pages=pages,
                features=feature_strings,
                content_type=content_type,
            )

            kwargs = {}
            if pages:
                kwargs["pages"] = pages
            if feature_strings:
                kwargs["features"] = feature_strings

            poller = await client.begin_analyze_document(
                model_id=model_id.value,
                body=document_stream,
                content_type=content_type,
                **kwargs,
            )

            result = await poller.result()
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

            metadata = {
                "execution_time_ms": duration_ms,
                "model_id": model_id.value,
                "api_version": self.settings.AZURE_DOCUMENT_INTELLIGENCE_API_VERSION,
            }

            self.logger.info("Document analysis succeeded", duration_ms=duration_ms)

            return self.parser.parse_result(
                model_id=model_id.value,
                result=result,
                metadata=metadata,
            )

        except AzureError as e:
            self.logger.error("Azure Document Intelligence call failed", error=str(e))
            raise AzureServiceException(
                message=f"Azure Document Intelligence error: {str(e)}",
                details={"model_id": model_id.value, "azure_error": str(e)},
            ) from e
        except Exception as e:
            self.logger.exception("Unexpected error during document analysis", error=str(e))
            raise AzureServiceException(
                message=f"Document analysis failed: {str(e)}"
            ) from e
