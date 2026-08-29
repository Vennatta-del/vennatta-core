import pytest

from app.facilitator_contract import FacilitatorContractError
from app.facilitator_http import FacilitatorHttpClient


def test_http_client_is_disabled_by_default():
    client = FacilitatorHttpClient(
        request=lambda **kwargs: {},
        base_url="https://sandbox.invalid",
        expected_network="base",
        expected_scheme="exact",
    )

    with pytest.raises(FacilitatorContractError, match="disabled"):
        client.verify(
            payment_payload={"x": "y"},
            payment_requirements={
                "network": "base",
                "scheme": "exact",
            },
        )


def test_verify_uses_official_shape():
    calls = []

    def request(**kwargs):
        calls.append(kwargs)
        return {
            "isValid": True,
            "network": "base",
            "scheme": "exact",
            "paymentId": "payment-1",
        }

    client = FacilitatorHttpClient(
        request=request,
        base_url="https://sandbox.example",
        expected_network="base",
        expected_scheme="exact",
        live_enabled=True,
    )

    result = client.verify(
        payment_payload={"payload": "test"},
        payment_requirements={
            "network": "base",
            "scheme": "exact",
        },
    )

    assert result["verified"] is True
    assert result["payment_id"] == "payment-1"
    assert calls[0]["url"] == "https://sandbox.example/v2/x402/verify"
    assert "paymentPayload" in calls[0]["json"]
    assert "paymentRequirements" in calls[0]["json"]


def test_verify_rejects_invalid_payment():
    client = FacilitatorHttpClient(
        request=lambda **kwargs: {
            "isValid": False,
            "network": "base",
            "scheme": "exact",
            "invalidReason": "signature_invalid",
        },
        base_url="https://sandbox.example",
        expected_network="base",
        expected_scheme="exact",
        live_enabled=True,
    )

    with pytest.raises(FacilitatorContractError, match="signature_invalid"):
        client.verify(
            payment_payload={"payload": "test"},
            payment_requirements={
                "network": "base",
                "scheme": "exact",
            },
        )


def test_settle_uses_official_shape():
    def request(**kwargs):
        return {
            "success": True,
            "transaction": "tx-1",
        }

    client = FacilitatorHttpClient(
        request=request,
        base_url="https://sandbox.example",
        expected_network="base",
        expected_scheme="exact",
        live_enabled=True,
    )

    result = client.settle(
        payment_payload={"payload": "test"},
        payment_requirements={
            "network": "base",
            "scheme": "exact",
        },
    )

    assert result["settled"] is True
    assert result["settlement_id"] == "tx-1"


def test_settle_rejects_missing_transaction():
    client = FacilitatorHttpClient(
        request=lambda **kwargs: {"success": True},
        base_url="https://sandbox.example",
        expected_network="base",
        expected_scheme="exact",
        live_enabled=True,
    )

    with pytest.raises(
        FacilitatorContractError,
        match="transaction",
    ):
        client.settle(
            payment_payload={"payload": "test"},
            payment_requirements={
                "network": "base",
                "scheme": "exact",
            },
        )
