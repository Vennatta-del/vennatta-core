from __future__ import annotations

from typing import Protocol

from .extractor import extract_marked_fields


class ExtractionBackend(Protocol):
    def extract(
        self,
        document: str,
        fields: list[str],
    ) -> dict:
        ...


class DeterministicExtractionBackend:
    def extract(
        self,
        document: str,
        fields: list[str],
    ) -> dict:
        return extract_marked_fields(document, fields)


def get_local_backend() -> ExtractionBackend:
    return DeterministicExtractionBackend()
