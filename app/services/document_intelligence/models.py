from enum import Enum
from typing import List
from pydantic import BaseModel


class SupportedModel(str, Enum):
    """Enum of verified prebuilt models supported in Document Intelligence."""
    INVOICE = "prebuilt-invoice"
    RECEIPT = "prebuilt-receipt"
    LAYOUT = "prebuilt-layout"
    READ = "prebuilt-read"
    CONTRACT = "prebuilt-contract"
    TAX_US_W2 = "prebuilt-tax.us.w2"


class ModelCapabilities(BaseModel):
    """Capabilities metadata for an Azure Document Intelligence model."""
    model_id: str
    description: str
    supports_key_value_pairs: bool
    supports_tables: bool
    supports_line_items: bool
    supported_file_types: List[str]


MODEL_CATALOG = {
    SupportedModel.INVOICE: ModelCapabilities(
        model_id=SupportedModel.INVOICE.value,
        description="Extracts vendor, customer, line items, totals, dates, and tax breakdown from invoices.",
        supports_key_value_pairs=True,
        supports_tables=True,
        supports_line_items=True,
        supported_file_types=["application/pdf", "image/png", "image/jpeg", "image/tiff"],
    ),
    SupportedModel.LAYOUT: ModelCapabilities(
        model_id=SupportedModel.LAYOUT.value,
        description="Extracts text, selection marks, tables, and document structure layout.",
        supports_key_value_pairs=False,
        supports_tables=True,
        supports_line_items=False,
        supported_file_types=["application/pdf", "image/png", "image/jpeg", "image/tiff"],
    ),
    SupportedModel.READ: ModelCapabilities(
        model_id=SupportedModel.READ.value,
        description="High accuracy OCR text extraction with print and handwritten style detection.",
        supports_key_value_pairs=False,
        supports_tables=False,
        supports_line_items=False,
        supported_file_types=["application/pdf", "image/png", "image/jpeg", "image/tiff"],
    ),
}
