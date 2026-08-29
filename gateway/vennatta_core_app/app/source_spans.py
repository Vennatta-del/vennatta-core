from __future__ import annotations

from typing import Any


class SourceSpanError(ValueError):
    pass


def validate_source_spans(
    document: str,
    spans: Any,
) -> list[dict[str, Any]]:
    if not isinstance(spans, list):
        raise SourceSpanError("source_spans must be a list")

    validated: list[dict[str, Any]] = []

    for span in spans:
        if not isinstance(span, dict):
            raise SourceSpanError("each source span must be an object")

        field = span.get("field")
        text = span.get("text")
        start = span.get("start")
        end = span.get("end")

        if not isinstance(field, str) or not field:
            raise SourceSpanError("source span field must be non-empty text")
        if not isinstance(text, str):
            raise SourceSpanError("source span text must be text")
        if not isinstance(start, int) or not isinstance(end, int):
            raise SourceSpanError("source span offsets must be integers")
        if start < 0 or end < start or end > len(document):
            raise SourceSpanError("source span offsets are out of bounds")
        if document[start:end] != text:
            raise SourceSpanError(
                "source span text does not match document offsets"
            )

        validated.append(
            {
                "field": field,
                "text": text,
                "start": start,
                "end": end,
            }
        )

    return validated
