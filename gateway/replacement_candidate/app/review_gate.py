from __future__ import annotations

import hashlib
import json
from typing import Any


class ReviewGateError(RuntimeError):
    pass


def review_product_result(
    *,
    product: dict[str, Any],
    document: str,
    requested_fields: list[str],
) -> dict[str, Any]:
    if not isinstance(product, dict):
        raise ReviewGateError("product result must be an object")

    required = {"product", "backend", "result", "result_sha256"}
    if set(product) != required:
        raise ReviewGateError("product result schema is invalid")

    if product["product"] != "document_extraction":
        raise ReviewGateError("unsupported product")

    if not isinstance(document, str) or not document:
        raise ReviewGateError("document must be non-empty text")

    if not isinstance(requested_fields, list) or not requested_fields:
        raise ReviewGateError("requested_fields must be non-empty")

    result = product["result"]
    if not isinstance(result, dict):
        raise ReviewGateError("embedded result must be an object")

    if set(result) != {"fields", "source_spans", "warnings"}:
        raise ReviewGateError("embedded result schema is invalid")

    fields = result["fields"]
    spans = result["source_spans"]
    warnings = result["warnings"]

    if not isinstance(fields, dict):
        raise ReviewGateError("result fields must be an object")

    if not isinstance(spans, list):
        raise ReviewGateError("result source_spans must be a list")

    if not isinstance(warnings, list):
        raise ReviewGateError("result warnings must be a list")

    if set(fields) - set(requested_fields):
        raise ReviewGateError("result contains an unrequested field")

    span_by_field: dict[str, dict[str, Any]] = {}

    for span in spans:
        if not isinstance(span, dict):
            raise ReviewGateError("source span must be an object")

        field = span.get("field")
        text = span.get("text")
        start = span.get("start")
        end = span.get("end")

        if (
            not isinstance(field, str)
            or not isinstance(text, str)
            or not isinstance(start, int)
            or not isinstance(end, int)
        ):
            raise ReviewGateError("source span is malformed")

        if start < 0 or end < start or end > len(document):
            raise ReviewGateError("source span is out of bounds")

        if document[start:end] != text:
            raise ReviewGateError("source span does not match document")

        if field in span_by_field:
            raise ReviewGateError("duplicate source span field")

        span_by_field[field] = span

    if set(fields) != set(span_by_field):
        raise ReviewGateError(
            "every extracted field must have exactly one source span"
        )

    canonical = json.dumps(
        result,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    expected_hash = hashlib.sha256(
        canonical.encode("utf-8")
    ).hexdigest()

    if product["result_sha256"] != expected_hash:
        raise ReviewGateError("result hash mismatch")

    return {
        "reviewed": True,
        "review_status": "approved",
        "product": product,
    }
