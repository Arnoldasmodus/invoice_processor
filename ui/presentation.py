import json
from typing import Any, Dict, List, Optional

from app.models.response import InvoiceExtractionResponse


AZURE_FIELD_LABELS = {
    "InvoiceId": "Sąskaitos numeris",
    "InvoiceDate": "Sąskaitos data",
    "DueDate": "Mokėjimo terminas",
    "PurchaseOrder": "Užsakymo numeris",
    "VendorName": "Tiekėjas",
    "VendorAddress": "Tiekėjo adresas",
    "VendorTaxId": "Tiekėjo PVM kodas",
    "CustomerName": "Pirkėjas",
    "CustomerAddress": "Pirkėjo adresas",
    "CustomerTaxId": "Pirkėjo PVM kodas",
    "SubTotal": "Suma be PVM",
    "TotalTax": "PVM",
    "InvoiceTotal": "Bendra suma",
    "AmountDue": "Mokėtina suma",
    "PaymentTerm": "Mokėjimo sąlygos",
    "IBAN": "IBAN",
    "Items": "Prekės ir paslaugos",
}

NORMALIZED_CONFIDENCE_KEYS = {
    "InvoiceId": "invoice_id",
    "InvoiceDate": "invoice_date",
    "DueDate": "due_date",
    "VendorName": "vendor_name",
    "VendorAddress": "vendor_address",
    "VendorTaxId": "vendor_tax_id",
    "CustomerName": "customer_name",
    "CustomerAddress": "customer_address",
    "CustomerTaxId": "customer_tax_id",
    "SubTotal": "subtotal",
    "TotalTax": "total_tax",
    "InvoiceTotal": "invoice_total",
    "PaymentTerm": "payment_details.payment_term",
    "IBAN": "payment_details.iban",
}

LINE_ITEM_FIELDS = (
    ("description", "Aprašymas"),
    ("quantity", "Kiekis"),
    ("unit", "Matavimo vienetas"),
    ("unit_price", "Vieneto kaina"),
    ("amount", "Suma"),
    ("tax", "PVM"),
    ("product_code", "Prekės kodas"),
)

MONETARY_FIELDS = {"SubTotal", "TotalTax", "InvoiceTotal", "AmountDue"}
LINE_ITEM_MONETARY_FIELDS = {"unit_price", "amount", "tax"}


def format_confidence(confidence: Optional[float]) -> str:
    if confidence is None:
        return "Nėra įverčio"
    return f"{confidence * 100:.0f}%"


def _format_number(value: float) -> str:
    return f"{value:,.2f}".replace(",", " ").replace(".", ",")


def _format_value(value: Any, currency: Optional[str] = None) -> str:
    if value is None:
        return "Nerasta"

    if isinstance(value, dict):
        if "amount" in value:
            amount = value["amount"]
            currency = value.get("currency_code") or value.get("currency_symbol") or currency
            if isinstance(amount, (float, int)):
                formatted = _format_number(float(amount))
                return f"{formatted} {currency}" if currency else formatted
        return json.dumps(value, ensure_ascii=False, default=str)

    if isinstance(value, bool):
        return "Taip" if value else "Ne"
    if isinstance(value, (float, int)):
        formatted = _format_number(float(value))
        return f"{formatted} {currency}" if currency else formatted
    if isinstance(value, list):
        return json.dumps(value, ensure_ascii=False, default=str)
    return str(value)


def build_invoice_field_rows(invoice: InvoiceExtractionResponse) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for azure_name, field in invoice.raw_fields.items():
        if azure_name == "Items" or field.value is None:
            continue

        normalized_key = NORMALIZED_CONFIDENCE_KEYS.get(azure_name)
        confidence = (
            invoice.field_confidence.get(normalized_key)
            if normalized_key
            else None
        )
        if confidence is None:
            confidence = field.confidence

        value = _format_value(
            field.value,
            invoice.currency if azure_name in MONETARY_FIELDS else None,
        )
        rows.append(
            {
                "Laukas": AZURE_FIELD_LABELS.get(azure_name, azure_name),
                "Nuskaityta reikšmė": f"{value} | {format_confidence(confidence)}",
            }
        )
    return rows


def build_line_item_rows(invoice: InvoiceExtractionResponse) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for item_index, item in enumerate(invoice.items, start=1):
        for field_name, label in LINE_ITEM_FIELDS:
            value = getattr(item, field_name)
            if value is None:
                continue

            currency = invoice.currency if field_name in LINE_ITEM_MONETARY_FIELDS else None
            formatted = _format_value(value, currency)
            confidence = item.field_confidence.get(field_name)
            rows.append(
                {
                    "Eilutė": str(item_index),
                    "Laukas": label,
                    "Nuskaityta reikšmė": (
                        f"{formatted} | {format_confidence(confidence)}"
                    ),
                }
            )
    return rows