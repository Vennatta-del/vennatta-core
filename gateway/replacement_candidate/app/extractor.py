from __future__ import annotations

import re
from typing import Any

from .source_spans import validate_source_spans


class ExtractionError(ValueError):
    pass


def extract_marked_fields(
    document: str,
    fields: list[str],
) -> dict[str, Any]:
    extracted: dict[str, Any] = {}
    spans: list[dict[str, Any]] = []

    for field in fields:
        pattern = re.compile(
            rf"(?im)^\s*{re.escape(field)}\s*:\s*(.+?)\s*$"
        )
        match = pattern.search(document)

        if match is None:
            continue

        value = match.group(1)
        start = match.start(1)
        end = match.end(1)

        extracted[field] = value
        spans.append(
            {
                "field": field,
                "text": value,
                "start": start,
                "end": end,
            }
        )

    return {
        "fields": extracted,
        "source_spans": validate_source_spans(document, spans),
        "warnings": [],
    }
