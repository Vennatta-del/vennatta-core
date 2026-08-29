import pytest

from app.backend_selection import (
    BackendSelectionError,
    select_extraction_backend,
)
from app.extraction_backend import DeterministicExtractionBackend
from app.ollama_backend import OllamaExtractionBackend


def test_deterministic_backend_is_default():
    backend = select_extraction_backend(env={})

    assert isinstance(backend, DeterministicExtractionBackend)


def test_deterministic_backend_is_selected_explicitly():
    backend = select_extraction_backend(
        env={"EXTRACTION_BACKEND": "deterministic"},
    )

    assert isinstance(backend, DeterministicExtractionBackend)


def test_ollama_requires_explicit_generator():
    with pytest.raises(
        BackendSelectionError,
        match="explicit generate callable",
    ):
        select_extraction_backend(
            env={
                "EXTRACTION_BACKEND": "ollama",
                "OLLAMA_MODEL": "test-model",
            },
        )


def test_ollama_requires_model():
    with pytest.raises(
        BackendSelectionError,
        match="OLLAMA_MODEL is required",
    ):
        select_extraction_backend(
            env={"EXTRACTION_BACKEND": "ollama"},
            ollama_generate=lambda **kwargs: {},
        )


def test_ollama_requires_explicit_opt_in():
    backend = select_extraction_backend(
        env={
            "EXTRACTION_BACKEND": "ollama",
            "OLLAMA_MODEL": "test-model",
        },
        ollama_generate=lambda **kwargs: {},
    )

    assert isinstance(backend, OllamaExtractionBackend)


def test_unknown_backend_fails_closed():
    with pytest.raises(
        BackendSelectionError,
        match="unsupported extraction backend",
    ):
        select_extraction_backend(
            env={"EXTRACTION_BACKEND": "unknown"},
        )
