from app.models.response import DocumentField, InvoiceExtractionResponse, LineItem
from ui.presentation import (
    build_invoice_field_rows,
    build_line_item_rows,
    format_confidence,
)


def test_format_confidence_as_percent():
    assert format_confidence(0.93) == "93%"
    assert format_confidence(None) == "Nėra įverčio"


def test_build_invoice_rows_pairs_value_with_confidence():
    invoice = InvoiceExtractionResponse(
        currency="EUR",
        raw_fields={
            "TotalTax": DocumentField(
                name="TotalTax",
                value_type="currency",
                value={"amount": 20.0, "currency_code": "EUR"},
                confidence=0.93,
            )
        },
        field_confidence={"total_tax": 0.93},
    )

    assert build_invoice_field_rows(invoice) == [
        {"Laukas": "PVM", "Nuskaityta reikšmė": "20,00 EUR | 93%"}
    ]


def test_build_line_item_rows_uses_field_confidence():
    invoice = InvoiceExtractionResponse(
        currency="EUR",
        items=[
            LineItem(
                tax=20.0,
                field_confidence={"tax": 0.93},
            )
        ],
    )

    assert build_line_item_rows(invoice) == [
        {
            "Eilutė": "1",
            "Laukas": "PVM",
            "Nuskaityta reikšmė": "20,00 EUR | 93%",
        }
    ]