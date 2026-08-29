from app.extractor import extract_marked_fields


def test_extracts_exact_marked_fields_with_spans():
    document = "title: Report A\nauthor: Ada Lovelace"

    result = extract_marked_fields(
        document,
        ["title", "author"],
    )

    assert result["fields"] == {
        "title": "Report A",
        "author": "Ada Lovelace",
    }
    assert len(result["source_spans"]) == 2

    for span in result["source_spans"]:
        assert document[span["start"]:span["end"]] == span["text"]


def test_missing_field_is_not_fabricated():
    result = extract_marked_fields(
        "title: Report A",
        ["title", "author"],
    )

    assert result["fields"] == {"title": "Report A"}
    assert "author" not in result["fields"]
    assert all(
        span["field"] != "author"
        for span in result["source_spans"]
    )


def test_colons_and_special_field_names_are_safe():
    result = extract_marked_fields(
        "invoice.total: $42:00",
        ["invoice.total"],
    )

    assert result["fields"] == {"invoice.total": "$42:00"}
