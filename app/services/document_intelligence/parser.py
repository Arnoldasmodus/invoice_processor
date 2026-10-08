from typing import Any, Dict, List, Optional
import structlog
from app.models.common import BoundingBox, KeyValuePair, Point
from app.models.response import (
    AnalyzeDocumentResponse,
    DocumentField,
    DocumentTable,
    InvoiceExtractionResponse,
    LineItem,
    TableCell,
)

logger = structlog.get_logger(__name__)


class DocumentIntelligenceParser:
    """Parses raw Azure Document Intelligence SDK results into standardized Pydantic v2 schemas."""

    @staticmethod
    def _parse_polygon(polygon: Optional[List[float]], page_number: int = 1) -> Optional[BoundingBox]:
        """Converts Azure 1D polygon coordinates [x1, y1, x2, y2, ...] to BoundingBox."""
        if not polygon or len(polygon) < 2:
            return None

        points: List[Point] = []
        for i in range(0, len(polygon), 2):
            if i + 1 < len(polygon):
                points.append(Point(x=float(polygon[i]), y=float(polygon[i + 1])))

        return BoundingBox(page_number=page_number, polygon=points)

    @classmethod
    def parse_tables(cls, raw_tables: Optional[List[Any]]) -> List[DocumentTable]:
        """Parses extracted document tables."""
        if not raw_tables:
            return []

        parsed_tables: List[DocumentTable] = []
        for table in raw_tables:
            cells: List[TableCell] = []
            for cell in getattr(table, "cells", []) or []:
                bb = None
                if hasattr(cell, "bounding_regions") and cell.bounding_regions:
                    br = cell.bounding_regions[0]
                    bb = cls._parse_polygon(
                        getattr(br, "polygon", None),
                        getattr(br, "page_number", 1)
                    )

                cells.append(
                    TableCell(
                        row_index=getattr(cell, "row_index", 0),
                        column_index=getattr(cell, "column_index", 0),
                        row_span=getattr(cell, "row_span", 1) or 1,
                        column_span=getattr(cell, "column_span", 1) or 1,
                        content=getattr(cell, "content", "") or "",
                        confidence=getattr(cell, "confidence", None),
                        bounding_box=bb,
                    )
                )

            table_bb = None
            if hasattr(table, "bounding_regions") and table.bounding_regions:
                br = table.bounding_regions[0]
                table_bb = cls._parse_polygon(
                    getattr(br, "polygon", None),
                    getattr(br, "page_number", 1)
                )

            parsed_tables.append(
                DocumentTable(
                    row_count=getattr(table, "row_count", 0),
                    column_count=getattr(table, "column_count", 0),
                    cells=cells,
                    bounding_box=table_bb,
                )
            )

        return parsed_tables

    @classmethod
    def parse_key_value_pairs(cls, raw_kvps: Optional[List[Any]]) -> List[KeyValuePair]:
        """Parses extracted key-value pairs."""
        if not raw_kvps:
            return []

        parsed_kvps: List[KeyValuePair] = []
        for kvp in raw_kvps:
            key_content = ""
            if hasattr(kvp, "key") and kvp.key:
                key_content = getattr(kvp.key, "content", "") or ""

            value_content = None
            if hasattr(kvp, "value") and kvp.value:
                value_content = getattr(kvp.value, "content", None)

            bb = None
            if hasattr(kvp, "key") and kvp.key and hasattr(kvp.key, "bounding_regions") and kvp.key.bounding_regions:
                br = kvp.key.bounding_regions[0]
                bb = cls._parse_polygon(
                    getattr(br, "polygon", None),
                    getattr(br, "page_number", 1)
                )

            if key_content:
                parsed_kvps.append(
                    KeyValuePair(
                        key=key_content,
                        value=value_content,
                        confidence=getattr(kvp, "confidence", None),
                        bounding_box=bb,
                    )
                )

        return parsed_kvps

    @classmethod
    def _extract_field_value(cls, field: Any) -> Any:
        """Extracts primitive or complex value from an Azure DocumentField object."""
        if field is None:
            return None

        # Check standard typed value properties
        for attr in ("value_string", "value_date", "value_time", "value_phone_number",
                     "value_number", "value_integer", "value_boolean", "value_selection_mark",
                     "value_country_region", "value_signature"):
            val = getattr(field, attr, None)
            if val is not None:
                return val

        if hasattr(field, "value_currency") and field.value_currency is not None:
            curr = field.value_currency
            return {
                "amount": getattr(curr, "amount", None),
                "currency_symbol": getattr(curr, "currency_symbol", None),
                "currency_code": getattr(curr, "currency_code", None),
            }

        if hasattr(field, "value_address") and field.value_address is not None:
            addr = field.value_address
            return {
                "street_address": getattr(addr, "street_address", None),
                "city": getattr(addr, "city", None),
                "state": getattr(addr, "state", None),
                "postal_code": getattr(addr, "postal_code", None),
                "country_region": getattr(addr, "country_region", None),
            }

        if hasattr(field, "value_array") and field.value_array is not None:
            return [cls._extract_field_value(item) for item in field.value_array]

        if hasattr(field, "value_object") and field.value_object is not None:
            return {k: cls._extract_field_value(v) for k, v in field.value_object.items()}

        return getattr(field, "content", None)

    @classmethod
    def parse_invoice_data(cls, raw_documents: Optional[List[Any]]) -> Optional[InvoiceExtractionResponse]:
        """Extracts and maps specialized invoice fields and line items."""
        if not raw_documents:
            return None

        doc = raw_documents[0]
        fields = getattr(doc, "fields", {}) or {}

        def get_field_val(name: str) -> Any:
            f = fields.get(name)
            return cls._extract_field_value(f) if f else None

        def get_field_confidence(name: str) -> Optional[float]:
            field = fields.get(name)
            return getattr(field, "confidence", None) if field else None

        def get_field_amount(name: str) -> Optional[float]:
            val = get_field_val(name)
            if isinstance(val, dict) and "amount" in val:
                return val.get("amount")
            if isinstance(val, (int, float)):
                return float(val)
            return None

        def get_field_currency(name: str) -> Optional[str]:
            val = get_field_val(name)
            if isinstance(val, dict):
                return val.get("currency_code") or val.get("currency_symbol")
            return None

        # Parse Line Items
        items: List[LineItem] = []
        items_field = fields.get("Items")
        if items_field and hasattr(items_field, "value_array") and items_field.value_array:
            for item in items_field.value_array:
                item_obj = getattr(item, "value_object", {}) or {}

                def get_item_subval(k: str) -> Any:
                    f = item_obj.get(k)
                    return cls._extract_field_value(f) if f else None

                def get_item_subamount(k: str) -> Optional[float]:
                    v = get_item_subval(k)
                    if isinstance(v, dict) and "amount" in v:
                        return v.get("amount")
                    if isinstance(v, (int, float)):
                        return float(v)
                    return None

                def get_item_subconfidence(k: str) -> Optional[float]:
                    field = item_obj.get(k)
                    return getattr(field, "confidence", None) if field else None

                items.append(
                    LineItem(
                        description=str(get_item_subval("Description") or "") or None,
                        quantity=float(get_item_subval("Quantity")) if get_item_subval("Quantity") is not None else None,
                        unit=str(get_item_subval("Unit") or "") or None,
                        unit_price=get_item_subamount("UnitPrice"),
                        amount=get_item_subamount("Amount"),
                        tax=get_item_subamount("Tax"),
                        product_code=str(get_item_subval("ProductCode") or "") or None,
                        confidence=getattr(item, "confidence", None),
                        field_confidence={
                            "description": get_item_subconfidence("Description"),
                            "quantity": get_item_subconfidence("Quantity"),
                            "unit": get_item_subconfidence("Unit"),
                            "unit_price": get_item_subconfidence("UnitPrice"),
                            "amount": get_item_subconfidence("Amount"),
                            "tax": get_item_subconfidence("Tax"),
                            "product_code": get_item_subconfidence("ProductCode"),
                        },
                    )
                )

        # Parse raw fields map
        raw_fields_map: Dict[str, DocumentField] = {}
        for key, field_obj in fields.items():
            bb = None
            if hasattr(field_obj, "bounding_regions") and field_obj.bounding_regions:
                br = field_obj.bounding_regions[0]
                bb = cls._parse_polygon(
                    getattr(br, "polygon", None),
                    getattr(br, "page_number", 1)
                )

            raw_fields_map[key] = DocumentField(
                name=key,
                value_type=getattr(field_obj, "type", "string") or "string",
                value=cls._extract_field_value(field_obj),
                content=getattr(field_obj, "content", None),
                confidence=getattr(field_obj, "confidence", None),
                bounding_box=bb,
            )

        currency = (
            get_field_currency("InvoiceTotal")
            or get_field_currency("SubTotal")
            or "EUR"
        )
        currency_confidence = get_field_confidence("InvoiceTotal")
        if currency_confidence is None:
            currency_confidence = get_field_confidence("SubTotal")
        iban_confidence = get_field_confidence("IBAN")
        if iban_confidence is None:
            iban_confidence = get_field_confidence("CustomerAddressRecipient")

        return InvoiceExtractionResponse(
            invoice_id=str(get_field_val("InvoiceId") or "") or None,
            invoice_date=str(get_field_val("InvoiceDate") or "") or None,
            due_date=str(get_field_val("DueDate") or "") or None,
            vendor_name=str(get_field_val("VendorName") or "") or None,
            vendor_address=str(get_field_val("VendorAddress") or "") or None,
            vendor_tax_id=str(get_field_val("VendorTaxId") or "") or None,
            customer_name=str(get_field_val("CustomerName") or "") or None,
            customer_address=str(get_field_val("CustomerAddress") or "") or None,
            customer_tax_id=str(get_field_val("CustomerTaxId") or "") or None,
            subtotal=get_field_amount("SubTotal"),
            total_tax=get_field_amount("TotalTax"),
            invoice_total=get_field_amount("InvoiceTotal"),
            currency=currency,
            payment_details={
                "payment_term": get_field_val("PaymentTerm"),
                "iban": get_field_val("IBAN") or get_field_val("CustomerAddressRecipient"),
            },
            items=items,
            raw_fields=raw_fields_map,
            field_confidence={
                "invoice_id": get_field_confidence("InvoiceId"),
                "invoice_date": get_field_confidence("InvoiceDate"),
                "due_date": get_field_confidence("DueDate"),
                "vendor_name": get_field_confidence("VendorName"),
                "vendor_address": get_field_confidence("VendorAddress"),
                "vendor_tax_id": get_field_confidence("VendorTaxId"),
                "customer_name": get_field_confidence("CustomerName"),
                "customer_address": get_field_confidence("CustomerAddress"),
                "customer_tax_id": get_field_confidence("CustomerTaxId"),
                "subtotal": get_field_confidence("SubTotal"),
                "total_tax": get_field_confidence("TotalTax"),
                "invoice_total": get_field_confidence("InvoiceTotal"),
                "currency": currency_confidence,
                "payment_details.payment_term": get_field_confidence("PaymentTerm"),
                "payment_details.iban": iban_confidence,
            },
        )

    @classmethod
    def parse_result(
        cls,
        model_id: str,
        result: Any,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AnalyzeDocumentResponse:
        """Parses the entire Azure AnalyzeResult into AnalyzeDocumentResponse."""
        page_count = len(getattr(result, "pages", []) or [])
        content = getattr(result, "content", "")
        raw_tables = getattr(result, "tables", None)
        raw_kvps = getattr(result, "key_value_pairs", None)
        raw_docs = getattr(result, "documents", None)

        tables = cls.parse_tables(raw_tables)
        kvps = cls.parse_key_value_pairs(raw_kvps)
        invoice_data = cls.parse_invoice_data(raw_docs) if raw_docs else None

        return AnalyzeDocumentResponse(
            model_id=model_id,
            page_count=page_count if page_count > 0 else 1,
            content=content,
            key_value_pairs=kvps,
            tables=tables,
            invoice_data=invoice_data,
            metadata=metadata or {},
        )
