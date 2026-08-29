import pytest

from app.facilitator_adapter import (
    FacilitatorAdapter,
    FacilitatorAdapterError,
)
from app.facilitator_http import FacilitatorHttpClient


def test_adapter_is_disabled_by_default():
    http = FacilitatorHttpClient(
        request=lambda **kwargs: {},
        base_url="https://sandbox.example",
        expected_network="base",
        expected_scheme="exact",
    )
    adapter = FacilitatorAdapter(http_client=http)

    with pytest.raises(FacilitatorAdapterError, match="disabled"):
        adapter.verify(
            payment={"payload": "test"},
            product={"result_sha256": "hash"},
            idempotency_key="key",
        )


def test_adapter_normalizes_verify_response():
    http = FacilitatorHttpClient(
        request=lambda **kwargs: {
            "isValid": True,
            "network": "base",
            "scheme": "exact",
            "paymentId": "payment-1",
        },
        base_url="https://sandbox.example",
        expected_network="base",
        expected_scheme="exact",
        live_enabled=True,
    )
    adapter = FacilitatorAdapter(http_client=http)

    result = adapter.verify(
        payment={"payload": "test"},
        product={"result_sha256": "hash"},
        idempotency_key="key",
    )

    assert result["verified"] is True
    assert result["network"] == "base"
    assert result["scheme"] == "exact"
    assert result["payment_id"] == "payment-1"


def test_adapter_normalizes_settle_response():
    http = FacilitatorHttpClient(
        request=lambda **kwargs: {
            "success": True,
            "transaction": "tx-1",
        },
        base_url="https://sandbox.example",
        expected_network="base",
        expected_scheme="exact",
        live_enabled=True,
    )
    adapter = FacilitatorAdapter(http_client=http)

    result = adapter.settle(
        payment={"payload": "test"},
        product={"result_sha256": "hash"},
        idempotency_key="key",
    )

    assert result["settled"] is True
    assert result["settlement_id"] == "tx-1"
