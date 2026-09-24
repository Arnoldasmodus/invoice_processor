from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.models.common import BoundingBox, KeyValuePair


class DocumentField(BaseModel):
    """Normalized document field with value and confidence."""
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(..., description="Field name")
    value_type: str = Field(..., description="Data type: string, number, date, address, currency, etc.")
    value: Any = Field(None, description="Parsed field value")
    content: Optional[str] = Field(None, description="Raw text representation from document")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Extraction confidence score")
    bounding_box: Optional[BoundingBox] = Field(None, description="Location coordinates")


class TableCell(BaseModel):
    """Single cell inside an extracted table."""
    model_config = ConfigDict(str_strip_whitespace=True)

    row_index: int = Field(..., description="0-based row index")
    column_index: int = Field(..., description="0-based column index")
    row_span: int = Field(1, description="Number of rows spanned")
    column_span: int = Field(1, description="Number of columns spanned")
    content: str = Field(..., description="Cell text content")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Cell confidence")
    bounding_box: Optional[BoundingBox] = Field(None, description="Cell location")


class DocumentTable(BaseModel):
    """Extracted table representation."""
    model_config = ConfigDict(str_strip_whitespace=True)

    row_count: int = Field(..., description="Total rows in table")
    column_count: int = Field(..., description="Total columns in table")
    cells: List[TableCell] = Field(default_factory=list, description="List of cells")
    bounding_box: Optional[BoundingBox] = Field(None, description="Table location")


class LineItem(BaseModel):
    """Standardized line item inside an invoice."""
    model_config = ConfigDict(str_strip_whitespace=True)

    description: Optional[str] = Field(None, description="Item description")
    quantity: Optional[float] = Field(None, description="Quantity")
    unit: Optional[str] = Field(None, description="Unit of measurement")
    unit_price: Optional[float] = Field(None, description="Unit price")
    amount: Optional[float] = Field(None, description="Total item line amount")
    tax: Optional[float] = Field(None, description="Tax amount for this line")
    product_code: Optional[str] = Field(None, description="Product code / SKU")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Confidence")


class InvoiceExtractionResponse(BaseModel):
    """Comprehensive structured invoice data."""
    model_config = ConfigDict(str_strip_whitespace=True)

    invoice_id: Optional[str] = Field(None, description="Invoice number / identifier")
    invoice_date: Optional[str] = Field(None, description="Invoice issue date")
    due_date: Optional[str] = Field(None, description="Invoice due payment date")
    vendor_name: Optional[str] = Field(None, description="Vendor / Supplier name")
    vendor_address: Optional[str] = Field(None, description="Vendor address")
    vendor_tax_id: Optional[str] = Field(None, description="Vendor VAT / Tax ID")
    customer_name: Optional[str] = Field(None, description="Customer / Buyer name")
    customer_address: Optional[str] = Field(None, description="Customer address")
    customer_tax_id: Optional[str] = Field(None, description="Customer VAT / Tax ID")
    subtotal: Optional[float] = Field(None, description="Subtotal before tax")
    total_tax: Optional[float] = Field(None, description="Total tax / VAT")
    invoice_total: Optional[float] = Field(None, description="Grand total amount")
    currency: Optional[str] = Field(None, description="Currency code (e.g. EUR, USD)")
    payment_details: Optional[Dict[str, Any]] = Field(default_factory=dict, description="IBAN, Swift, payment terms")
    items: List[LineItem] = Field(default_factory=list, description="Extracted invoice line items")
    raw_fields: Dict[str, DocumentField] = Field(default_factory=dict, description="All raw fields extracted")


class AnalyzeDocumentResponse(BaseModel):
    """Top-level response envelope for document analysis."""
    model_config = ConfigDict(str_strip_whitespace=True)

    model_id: str = Field(..., description="Model used for analysis")
    page_count: int = Field(..., description="Number of pages analyzed")
    content: Optional[str] = Field(None, description="Full raw text content")
    key_value_pairs: List[KeyValuePair] = Field(default_factory=list, description="Extracted key-value pairs")
    tables: List[DocumentTable] = Field(default_factory=list, description="Extracted tables")
    invoice_data: Optional[InvoiceExtractionResponse] = Field(None, description="Structured invoice output if applicable")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Execution metadata (timing, file size, etc.)")
