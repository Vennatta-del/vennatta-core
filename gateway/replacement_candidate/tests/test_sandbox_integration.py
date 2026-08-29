import hashlib
import json
from pathlib import Path

import pytest

from app.extraction_service import extract_product
from app.facilitator_adapter import FacilitatorAdapter
from app.facilitator_http import FacilitatorHttpClient
from app.idempotency_store import IdempotencyStore
from app.review_gate import review_product_result
from app.settlement_gate import (
    SettlementAdapter,
    SettlementGateError,
    fulfill_after_settlement,
)
from app.x402_config import get_network, get_scheme


class MockFacilitatorTransport:
    def __init__(self) -> None:
        self.calls = []

    def request(self, **kwargs):
        self.calls.append(kwargs)

        path = kwargs["url"].split("/")[-1]

        if path == "verify":
            return {
                "isValid": True,
                "network": "base-sepolia",
                "scheme": "exact",
                "paymentId": "sandbox-payment-1",
            }
        if path == "settle":
            return {
                "success": True,
                "transaction": "sandbox-tx-1",
            }

        raise RuntimeError(f"unexpected path: {path}")


@pytest.fixture
def sandbox_stack(tmp_path: Path):
    transport = MockFacilitatorTransport()

    http_client = FacilitatorHttpClient(
        request=transport.request,
        base_url="https://sandbox.facilitator.example",
        expected_network="base-sepolia",
        expected_scheme="exact",
        live_enabled=True,
    )

    adapter = FacilitatorAdapter(http_client=http_client)

    idempotency = IdempotencyStore(tmp_path / "idempotency.sqlite3")

    settlement = SettlementAdapter(
        verify=adapter.verify,
        settle=adapter.settle,
        dry_run=False,
        idempotency_store=idempotency,
    )

    return {
        "transport": transport,
        "settlement": settlement,
        "idempotency": idempotency,
    }


def test_full_sandbox_flow(sandbox_stack):
    document = "title: Report A\nauthor: Jane Doe"
    fields = ["title", "author"]

    product = extract_product(
        document=document,
        fields=fields,
        env={},
    )

    reviewed = review_product_result(
        product=product,
        document=document,
        requested_fields=fields,
    )

    receipt = sandbox_stack["settlement"].execute(
        reviewed_product=reviewed,
        request_id="sandbox-req-1",
        payment={
            "payload": "test-payment",
        },
    )

    assert receipt.status == "settled"
    assert receipt.settlement_id == "sandbox-tx-1"
    assert receipt.dry_run is False

    calls = sandbox_stack["transport"].calls
    assert len(calls) == 2
    assert calls[0]["url"].endswith("/v2/x402/verify")
    assert calls[1]["url"].endswith("/v2/x402/settle")

    output = fulfill_after_settlement(
        receipt=receipt,
        fulfill=lambda: "fulfilled-output",
    )

    assert output == "fulfilled-output"


def test_replay_is_rejected_in_sandbox(sandbox_stack):
    document = "title: Report A"
    fields = ["title"]

    product = extract_product(
        document=document,
        fields=fields,
        env={},
    )

    reviewed = review_product_result(
        product=product,
        document=document,
        requested_fields=fields,
    )

    sandbox_stack["settlement"].execute(
        reviewed_product=reviewed,
        request_id="sandbox-req-2",
        payment={"payload": "test"},
    )

    with pytest.raises(SettlementGateError, match="replayed"):
        sandbox_stack["settlement"].execute(
            reviewed_product=reviewed,
            request_id="sandbox-req-2",
            payment={"payload": "test"},
        )


def test_network_and_scheme_are_validated(sandbox_stack):
    net = get_network("base-sepolia")
    scheme = get_scheme("exact")

    assert net.is_testnet is True
    assert scheme.id == "exact"
