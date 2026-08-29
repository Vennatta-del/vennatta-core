import pytest

from app.ollama_backend import OllamaBackendError, OllamaExtractionBackend


def valid_generate(**kwargs):
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


def test_valid_structured_output_is_accepted():
    backend = OllamaExtractionBackend(
        model="test-model",
        generate=valid_generate,
    )

    result = backend.extract("title: Report A", ["title"])

    assert result["fields"] == {"title": "Report A"}
    assert result["source_spans"][0]["text"] == "Report A"


def test_model_cannot_invent_unrequested_fields():
    def generate(**kwargs):
        return {
            "fields": {"secret": "invented"},
            "source_spans": [],
            "warnings": [],
        }

    backend = OllamaExtractionBackend(
        model="test-model",
        generate=generate,
    )

    with pytest.raises(OllamaBackendError):
        backend.extract("title: Report A", ["title"])


def test_model_failure_is_fail_closed():
    def generate(**kwargs):
        raise TimeoutError("simulated timeout")

    backend = OllamaExtractionBackend(
        model="test-model",
        generate=generate,
    )

    with pytest.raises(OllamaBackendError, match="request failed"):
        backend.extract("title: Report A", ["title"])


def test_invalid_span_is_rejected():
    def generate(**kwargs):
        return {
            "fields": {"title": "Wrong"},
            "source_spans": [
                {
                    "field": "title",
                    "text": "Wrong",
                    "start": 7,
                    "end": 12,
                }
            ],
            "warnings": [],
        }

    backend = OllamaExtractionBackend(
        model="test-model",
        generate=generate,
    )

    with pytest.raises(OllamaBackendError):
        backend.extract("title: Report A", ["title"])
