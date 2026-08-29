import pytest

from app.source_spans import SourceSpanError, validate_source_spans


def test_valid_half_open_span():
    document = "Invoice total: $42"
    spans = [
        {
            "field": "total",
            "text": "$42",
            "start": 15,
            "end": 18,
        }
    ]

    assert validate_source_spans(document, spans) == spans


def test_span_text_must_match_document():
    with pytest.raises(SourceSpanError, match="does not match"):
        validate_source_spans(
            "Invoice total: $42",
            [
                {
                    "field": "total",
                    "text": "$99",
                    "start": 15,
                    "end": 18,
                }
            ],
        )


def test_span_offsets_must_be_bounded():
    with pytest.raises(SourceSpanError, match="out of bounds"):
        validate_source_spans(
            "short",
            [{"field": "x", "text": "x", "start": 0, "end": 99}],
        )


def test_malformed_span_is_rejected():
    with pytest.raises(SourceSpanError):
        validate_source_spans("text", [{"field": "x"}])
