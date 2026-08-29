import pytest

from app.product_validation import (
    MAX_DOCUMENT_CHARACTERS,
    MAX_FIELDS,
    ProductValidationError,
    validate_extraction_request,
)


def valid_payload():
    return {
        "document": "Invoice total is $42.",
        "fields": ["total"],
        "options": {"source_spans": True},
    }


def test_valid_request_is_normalized():
    result = validate_extraction_request(valid_payload())

    assert result["document"] == "Invoice total is $42."
    assert result["fields"] == ["total"]
    assert result["options"]["source_spans"] is True


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"document": "", "fields": ["total"]},
        {"document": "text"},
        {"document": "text", "fields": []},
        {"document": "text", "fields": [1]},
        {"document": "text", "fields": [""]},
    ],
)
def test_invalid_requests_are_rejected(payload):
    with pytest.raises(ProductValidationError):
        validate_extraction_request(payload)


def test_oversized_document_is_rejected():
    payload = valid_payload()
    payload["document"] = "x" * (MAX_DOCUMENT_CHARACTERS + 1)

    with pytest.raises(ProductValidationError, match="maximum"):
        validate_extraction_request(payload)


def test_too_many_fields_are_rejected():
    payload = valid_payload()
    payload["fields"] = [f"field_{i}" for i in range(MAX_FIELDS + 1)]

    with pytest.raises(ProductValidationError, match="too many"):
        validate_extraction_request(payload)


def test_options_must_be_an_object():
    payload = valid_payload()
    payload["options"] = []

    with pytest.raises(ProductValidationError):
        validate_extraction_request(payload)
