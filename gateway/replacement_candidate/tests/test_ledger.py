import pytest

from app.ledger import InMemoryLedger, LedgerConflict


def test_same_id_same_fingerprint_is_idempotent():
    ledger = InMemoryLedger()
    first = ledger.begin("pid-1234567890", "fp")
    second = ledger.begin("pid-1234567890", "fp")
    assert first == second


def test_same_id_different_fingerprint_conflicts():
    ledger = InMemoryLedger()
    ledger.begin("pid-1234567890", "one")

    with pytest.raises(LedgerConflict):
        ledger.begin("pid-1234567890", "two")


def test_fulfillment_is_replayable():
    ledger = InMemoryLedger()
    ledger.begin("pid-1234567890", "fp")

    stored = ledger.fulfill(
        "pid-1234567890",
        {"status": "candidate-only"},
        "0xtest",
    )

    replay = ledger.get("pid-1234567890")
    assert replay == stored
    assert replay.status == "fulfilled"
    assert replay.transaction_hash == "0xtest"
