from app.extraction_backend import (
    DeterministicExtractionBackend,
    get_local_backend,
)


def test_local_backend_is_deterministic():
    backend = get_local_backend()

    first = backend.extract(
        "title: Report A",
        ["title", "author"],
    )
    second = backend.extract(
        "title: Report A",
        ["title", "author"],
    )

    assert first == second
    assert first["fields"] == {"title": "Report A"}
    assert "author" not in first["fields"]


def test_local_backend_uses_reviewed_implementation():
    assert isinstance(
        get_local_backend(),
        DeterministicExtractionBackend,
    )
