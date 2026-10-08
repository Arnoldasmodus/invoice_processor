from types import SimpleNamespace

from app.services.document_intelligence.parser import DocumentIntelligenceParser


def test_parse_polygon():
    polygon = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6]
    bb = DocumentIntelligenceParser._parse_polygon(polygon, page_number=2)

    assert bb is not None
    assert bb.page_number == 2
    assert len(bb.polygon) == 3
    assert bb.polygon[0].x == 0.1
    assert bb.polygon[0].y == 0.2


def test_parse_empty_result():
    class DummyResult:
        pages = []
        content = "Sample raw text"
        tables = None
        key_value_pairs = None
        documents = None

    response = DocumentIntelligenceParser.parse_result(
        model_id="prebuilt-invoice",
        result=DummyResult(),
        metadata={"execution_time_ms": 150},
    )

    assert response.model_id == "prebuilt-invoice"
    assert response.page_count == 1
    assert response.content == "Sample raw text"
    assert response.tables == []
    assert response.key_value_pairs == []
    assert response.invoice_data is None


def test_parse_invoice_field_confidence():
    def field(*, confidence, value_string=None, value_number=None, value_currency=None):
        return SimpleNamespace(
            confidence=confidence,
            value_string=value_string,
            value_number=value_number,
            value_currency=value_currency,
            value_array=None,
            value_object=None,
            value_address=None,
            content=None,
            type="string",
            bounding_regions=None,
        )

    fields = {
        "InvoiceId": field(confidence=0.98, value_string="INV-1042"),
        "TotalTax": field(
            confidence=0.93,
            value_currency=SimpleNamespace(
                amount=20.0,
                currency_symbol="EUR",
                currency_code="EUR",
            ),
        ),
        "Items": SimpleNamespace(
            value_array=[
                SimpleNamespace(
                    confidence=0.91,
                    value_object={
                        "Description": field(confidence=0.94, value_string="Paslauga A"),
                        "Quantity": field(confidence=0.98, value_number=2),
                    },
                )
            ]
        ),
    }

    response = DocumentIntelligenceParser.parse_invoice_data(
        [SimpleNamespace(fields=fields)]
    )

    assert response is not None
    assert response.total_tax == 20.0
    assert response.field_confidence["invoice_id"] == 0.98
    assert response.field_confidence["total_tax"] == 0.93
    assert response.items[0].confidence == 0.91
    assert response.items[0].field_confidence["description"] == 0.94
    assert response.items[0].field_confidence["quantity"] == 0.98
    assert response.items[0].field_confidence["tax"] is None
