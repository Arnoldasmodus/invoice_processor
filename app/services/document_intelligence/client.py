from typing import Optional
from azure.ai.documentintelligence.aio import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential
import structlog
from app.core.config import Settings
from app.core.exceptions import AzureServiceException

logger = structlog.get_logger(__name__)


class DocumentIntelligenceClientManager:
    """Manages the lifecycle of Azure Document Intelligence async client."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._client: Optional[DocumentIntelligenceClient] = None

    def get_client(self) -> DocumentIntelligenceClient:
        """Returns initialized DocumentIntelligenceClient or raises error if unconfigured."""
        if not self.settings.AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT or not self.settings.AZURE_DOCUMENT_INTELLIGENCE_KEY:
            raise AzureServiceException(
                "Azure Document Intelligence endpoint or key is not configured in settings."
            )

        if self._client is None:
            self._client = DocumentIntelligenceClient(
                endpoint=self.settings.AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT,
                credential=AzureKeyCredential(self.settings.AZURE_DOCUMENT_INTELLIGENCE_KEY),
                api_version=self.settings.AZURE_DOCUMENT_INTELLIGENCE_API_VERSION,
            )
        return self._client

    async def close(self) -> None:
        """Closes the underlying client session."""
        if self._client is not None:
            await self._client.close()
            self._client = None
            logger.info("Azure Document Intelligence client closed")
