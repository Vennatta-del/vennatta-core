from __future__ import annotations

import json
from typing import Any, Callable

from .source_spans import validate_source_spans


class OllamaBackendError(RuntimeError):
    pass


class OllamaExtractionBackend:
    def __init__(
        self,
        *,
        model: str,
        generate: Callable[..., Any],
    ) -> None:
        self.model = model
        self._generate = generate

    def extract(
        self,
        document: str,
        fields: list[str],
    ) -> dict[str, Any]:
        schema = {
            "type": "object",
            "required": ["fields", "source_spans", "warnings"],
            "properties": {
                "fields": {"type": "object"},
                "source_spans": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["field", "text", "start", "end"],
                    },
                },
                "warnings": {
                    "type": "array",
                    "items": {"type": "string"},
                },
            },
        }

        prompt = (
            "Extract only values supported by the document. "
            "Never invent missing values. "
            f"Requested fields: {fields}\n"
            f"Document:\n{document}"
        )

        try:
            raw = self._generate(
                model=self.model,
                prompt=prompt,
                format=schema,
                stream=False,
                options={"temperature": 0},
            )
        except Exception as exc:
            raise OllamaBackendError("Ollama request failed") from exc

        try:
            if isinstance(raw, str):
                parsed = json.loads(raw)
            elif isinstance(raw, dict) and isinstance(raw.get("response"), str):
                parsed = json.loads(raw["response"])
            elif isinstance(raw, dict):
                parsed = raw
            else:
                raise TypeError("unsupported Ollama response")
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            raise OllamaBackendError(
                "Ollama returned invalid structured output"
            ) from exc

        if not isinstance(parsed, dict):
            raise OllamaBackendError("Ollama output must be an object")

        extracted = parsed.get("fields", {})
        spans = parsed.get("source_spans", [])
        warnings = parsed.get("warnings", [])

        if not isinstance(extracted, dict):
            raise OllamaBackendError("Ollama fields must be an object")
        if not isinstance(warnings, list) or not all(
            isinstance(item, str) for item in warnings
        ):
            raise OllamaBackendError("Ollama warnings are invalid")

        try:
            validated_spans = validate_source_spans(document, spans)
        except Exception as exc:
            raise OllamaBackendError(
                "Ollama returned invalid source spans"
            ) from exc

        span_fields = {span["field"] for span in validated_spans}
        if set(extracted) - span_fields:
            raise OllamaBackendError(
                "every extracted field must have a source span"
            )

        if set(extracted) - set(fields):
            raise OllamaBackendError(
                "Ollama returned a field that was not requested"
            )

        return {
            "fields": extracted,
            "source_spans": validated_spans,
            "warnings": warnings,
        }
