from __future__ import annotations

from typing import Any


MAX_DOCUMENT_CHARACTERS = 10_000
MAX_FIELDS = 20
MIN_FIELD_NAME_LENGTH = 1
MAX_FIELD_NAME_LENGTH = 64


class ProductValidationError(ValueError):
    pass


def validate_extraction_request(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ProductValidationError("request body must be an object")

    document = payload.get("document")
    if not isinstance(document, str) or not document:
        raise ProductValidationError(
            "document is required and must be non-empty text"
        )

    if len(document) > MAX_DOCUMENT_CHARACTERS:
        raise ProductValidationError(
            "document exceeds the maximum character limit"
        )

    fields = payload.get("fields")
    if not isinstance(fields, list) or not fields:
        raise ProductValidationError(
            "fields is required and must be a non-empty list"
        )

    if len(fields) > MAX_FIELDS:
        raise ProductValidationError(
            "too many fields requested"
        )

    normalized_fields: list[str] = []
    for field in fields:
        if not isinstance(field, str):
            raise ProductValidationError("field names must be strings")
        if not (
            MIN_FIELD_NAME_LENGTH
            <= len(field)
            <= MAX_FIELD_NAME_LENGTH
        ):
            raise ProductValidationError(
                "field name length is outside the permitted range"
            )
        normalized_fields.append(field)

    options = payload.get("options", {})
    if not isinstance(options, dict):
        raise ProductValidationError("options must be an object")

    return {
        "document": document,
        "fields": normalized_fields,
        "options": options,
    }
