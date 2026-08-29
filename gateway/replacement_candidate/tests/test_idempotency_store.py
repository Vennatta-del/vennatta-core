from pathlib import Path

from app.idempotency_store import IdempotencyStore


def test_claim_is_durable(tmp_path: Path):
    path = tmp_path / "idempotency.sqlite3"

    first = IdempotencyStore(path)
    assert first.claim("key-1") is True

    second = IdempotencyStore(path)
    assert second.claim("key-1") is False


def test_different_keys_are_independent(tmp_path: Path):
    store = IdempotencyStore(tmp_path / "idempotency.sqlite3")

    assert store.claim("key-1") is True
    assert store.claim("key-2") is True
