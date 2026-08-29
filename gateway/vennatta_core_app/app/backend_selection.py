from __future__ import annotations

import os
from typing import Any

from .extraction_backend import (
    DeterministicExtractionBackend,
    ExtractionBackend,
)
from .ollama_backend import OllamaExtractionBackend


class BackendSelectionError(RuntimeError):
    pass


def select_extraction_backend(
    *,
    env: dict[str, str] | None = None,
    ollama_generate: Any | None = None,
) -> ExtractionBackend:
    values = os.environ if env is None else env
    name = values.get("EXTRACTION_BACKEND", "deterministic").strip().lower()

    if name in {"", "deterministic", "local"}:
        return DeterministicExtractionBackend()

    if name != "ollama":
        raise BackendSelectionError(
            f"unsupported extraction backend: {name}"
        )

    if ollama_generate is None:
        raise BackendSelectionError(
            "Ollama requires an explicit generate callable"
        )

    model = values.get("OLLAMA_MODEL", "").strip()
    if not model:
        raise BackendSelectionError(
            "OLLAMA_MODEL is required when Ollama is selected"
        )

    return OllamaExtractionBackend(
        model=model,
        generate=ollama_generate,
    )
