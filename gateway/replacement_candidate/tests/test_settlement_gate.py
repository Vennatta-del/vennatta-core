import pytest

from app.idempotency_store import IdempotencyStore

from app.extraction_service import extract_product
from app.review_gate import review_product_result
from app.settlement_gate import (
    SettlementAdapter,
    SettlementGateError,
    fulfill_after_settlement,
)


def reviewed_product():
    product = extract_product(
        document="title: Report A",
        fields=["title"],
        env={},
    )
    return review_product_result(
        product=product,
        document="title: Report A",
        requested_fields=["title"],
    )


def verified(**kwargs):
    return {"verified": True}


def test_dry_run_verifies_without_fulfillment(tmp_path):
    adapter = SettlementAdapter(
        verify=verified,
        dry_run=True,
        idempotency_store=IdempotencyStore(
            tmp_path / "idempotency.sqlite3"
        ),
    )

    receipt = adapter.execute(
        reviewed_product=reviewed_product(),
        request_id="req-1",
        payment={"proof": "test"},
    )

    assert receipt.status == "dry_run_verified"
    assert receipt.dry_run is True
    assert receipt.settlement_id is None

    with pytest.raises(SettlementGateError, match="dry-run"):
        fulfill_after_settlement(
            receipt=receipt,
            fulfill=lambda: "paid output",
        )


def test_unverified_payment_fails_closed(tmp_path):
    adapter = SettlementAdapter(
        verify=lambda **kwargs: {"verified": False},
        dry_run=True,
        idempotency_store=IdempotencyStore(
            tmp_path / "idempotency.sqlite3"
        ),
    )

    with pytest.raises(SettlementGateError, match="not verified"):
        adapter.execute(
            reviewed_product=reviewed_product(),
            request_id="req-2",
            payment={"proof": "bad"},
        )


def test_replay_is_rejected(tmp_path):
    adapter = SettlementAdapter(
        verify=verified,
        dry_run=True,
        idempotency_store=IdempotencyStore(
            tmp_path / "idempotency.sqlite3"
        ),
    )
    product = reviewed_product()

    adapter.execute(
        reviewed_product=product,
        request_id="req-3",
        payment={"proof": "test"},
    )

    with pytest.raises(SettlementGateError, match="replayed"):
        adapter.execute(
            reviewed_product=product,
            request_id="req-3",
            payment={"proof": "test"},
        )


def test_live_settlement_requires_confirmation(tmp_path):
    adapter = SettlementAdapter(
        verify=verified,
        settle=lambda **kwargs: {"settled": False},
        dry_run=False,
        idempotency_store=IdempotencyStore(
            tmp_path / "idempotency.sqlite3"
        ),
    )

    with pytest.raises(SettlementGateError, match="not confirmed"):
        adapter.execute(
            reviewed_product=reviewed_product(),
            request_id="req-4",
            payment={"proof": "test"},
        )


def test_fulfillment_requires_confirmed_settlement(tmp_path):
    adapter = SettlementAdapter(
        verify=verified,
        settle=lambda **kwargs: {
            "settled": True,
            "settlement_id": "settle-1",
        },
        dry_run=False,
        idempotency_store=IdempotencyStore(
            tmp_path / "idempotency.sqlite3"
        ),
    )

    receipt = adapter.execute(
        reviewed_product=reviewed_product(),
        request_id="req-5",
        payment={"proof": "test"},
    )

    calls = []
    output = fulfill_after_settlement(
        receipt=receipt,
        fulfill=lambda: calls.append("fulfilled") or "output",
    )

    assert output == "output"
    assert calls == ["fulfilled"]
