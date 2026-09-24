from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.core.constants import DocumentAnalysisFeature, DocumentModelId


class AnalyzeDocumentRequest(BaseModel):
    """Configuration options when analyzing a document."""
    model_config = ConfigDict(str_strip_whitespace=True)

    model_id: DocumentModelId = Field(
        default=DocumentModelId.INVOICE,
        description="Azure Document Intelligence model to execute",
        examples=[DocumentModelId.INVOICE.value],
    )
    pages: Optional[str] = Field(
        default=None,
        description="Specific pages or page ranges to analyze (e.g., '1-3', '1,2,5')",
        examples=["1-2"],
    )
    features: Optional[List[DocumentAnalysisFeature]] = Field(
        default=None,
        description="Optional analysis features to enable",
    )
    locale: Optional[str] = Field(
        default=None,
        description="Locale hint for text extraction (e.g., 'en-US', 'lt-LT')",
        examples=["en-US"],
    )
