from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.core.constants import ProcessingStatus


class InvoiceEntity(BaseModel):
    """Domain representation of an invoice record."""
    model_config = ConfigDict(str_strip_whitespace=True)

    id: Optional[str] = Field(None, description="System internal ID")
    invoice_number: Optional[str] = Field(None, description="Extracted invoice number")
    vendor_name: Optional[str] = Field(None, description="Vendor name")
    customer_name: Optional[str] = Field(None, description="Customer name")
    total_amount: Optional[float] = Field(None, description="Total invoice amount")
    currency: Optional[str] = Field("EUR", description="Currency")
    issue_date: Optional[str] = Field(None, description="Date of issuance")
    due_date: Optional[str] = Field(None, description="Payment due date")
    status: ProcessingStatus = Field(default=ProcessingStatus.COMPLETED)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ProcessedDocument(BaseModel):
    """Domain model tracking processed document file and extraction result."""
    model_config = ConfigDict(str_strip_whitespace=True)

    document_id: str = Field(..., description="Unique document ID")
    filename: str = Field(..., description="Original filename")
    file_size_bytes: int = Field(..., description="File size in bytes")
    mime_type: str = Field(..., description="MIME type")
    page_count: int = Field(1, description="Total pages")
    storage_path: Optional[str] = Field(None, description="Storage location path")
    status: ProcessingStatus = Field(default=ProcessingStatus.PENDING)
    extracted_data: Optional[Dict[str, Any]] = Field(None, description="Structured extraction output")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
