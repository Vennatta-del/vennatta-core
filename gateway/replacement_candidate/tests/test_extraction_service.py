import pytest

from app.extraction_service import (
    ExtractionServiceError,
    extract_product,
)


def test_product_uses_deterministic_backend_by_default():
    result = extract_product(
        document="title: Report A",
        fields=["title", "author"],
        env={},
    )

    assert result["product"] == "document_extraction"
    assert result["backend"] == "DeterministicExtractionBackend"
    assert result["result"]["fields"] == {"title": "Report A"}
    assert "result_sha256" in result


def test_product_rejects_empty_document():
    with pytest.raises(
        ExtractionServiceError,
        match="document must be non-empty",
    ):
        extract_product(document="", fields=["title"], env={})


def test_product_rejects_empty_fields():
    with pytest.raises(
        ExtractionServiceError,
        match="fields must be a non-empty list",
    ):
        extract_product(document="title: Report A", fields=[], env={})


def test_product_rejects_duplicate_fields():
    with pytest.raises(
        ExtractionServiceError,
        match="must not contain duplicates",
    ):
        extract_product(
            document="title: Report A",
            fields=["title", "title"],
            env={},
        )


def test_product_ollama_requires_explicit_generator():
    with pytest.raises(
        Exception,
        match="explicit generate callable",
    ):
        extract_product(
            document="title: Report A",
            fields=["title"],
            env={
                "EXTRACTION_BACKEND": "ollama",
                "OLLAMA_MODEL": "test-model",
            },
        )


def test_product_ollama_can_be_injected_for_review():
    def generate(**kwargs):
        return {
            "fields": {"title": "Report A"},
            "source_spans": [
                {
                    "field": "title",
                    "text": "Report A",
                    "start": 7,
                    "end": 15,
                }
            ],
            "warnings": [],
        }

    result = extract_product(
        document="title: Report A",
        fields=["title"],
        env={
            "EXTRACTION_BACKEND": "ollama",
            "OLLAMA_MODEL": "test-model",
        },
        ollama_generate=generate,
    )

    assert result["backend"] == "OllamaExtractionBackend"
    assert result["result"]["fields"] == {"title": "Report A"}
