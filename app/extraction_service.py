from __future__ import annotations

import hashlib
import json
from typing import Any

from .backend_selection import select_extraction_backend


class ExtractionServiceError(RuntimeError):
    pass


def extract_product(
    *,
    document: str,
    fields: list[str],
    env: dict[str, str] | None = None,
    ollama_generate: Any | None = None,
) -> dict[str, Any]:
    if not isinstance(document, str) or not document:
        raise ExtractionServiceError("document must be non-empty text")

    if not isinstance(fields, list) or not fields:
        raise ExtractionServiceError("fields must be a non-empty list")

    if not all(isinstance(field, str) and field for field in fields):
        raise ExtractionServiceError("fields must contain non-empty text")

    if len(set(fields)) != len(fields):
        raise ExtractionServiceError("fields must not contain duplicates")

    backend = select_extraction_backend(
        env=env,
        ollama_generate=ollama_generate,
    )

    result = backend.extract(document, fields)

    if not isinstance(result, dict):
        raise ExtractionServiceError("backend result must be an object")

    if set(result) != {"fields", "source_spans", "warnings"}:
        raise ExtractionServiceError("backend result schema is invalid")

    canonical = json.dumps(
        result,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )

    return {
        "product": "document_extraction",
        "backend": backend.__class__.__name__,
        "result": result,
        "result_sha256": hashlib.sha256(
            canonical.encode("utf-8")
        ).hexdigest(),
    }
