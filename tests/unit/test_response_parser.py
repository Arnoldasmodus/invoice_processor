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
