import pytest

from app.facilitator_contract import (
    FacilitatorClient,
    FacilitatorContractError,
)


def request_ok(**kwargs):
    return {
        "verified": True,
        "network": "sandbox",
        "scheme": "test-scheme",
        "payment_id": "payment-1",
    }


def test_live_facilitator_is_disabled_by_default():
    client = FacilitatorClient(
        verify_request=request_ok,
        expected_network="sandbox",
        expected_scheme="test-scheme",
    )

    with pytest.raises(FacilitatorContractError, match="disabled"):
        client.verify(
            payment={"proof": "test"},
            product={"result_sha256": "hash"},
            idempotency_key="key",
        )


def test_expected_response_schema_is_accepted():
    client = FacilitatorClient(
        verify_request=request_ok,
        expected_network="sandbox",
        expected_scheme="test-scheme",
        live_enabled=True,
    )

    result = client.verify(
        payment={"proof": "test"},
        product={"result_sha256": "hash"},
        idempotency_key="key",
    )

    assert result["verified"] is True
    assert result["payment_id"] == "payment-1"


def test_network_mismatch_fails_closed():
    client = FacilitatorClient(
        verify_request=lambda **kwargs: {
            "verified": True,
            "network": "wrong-network",
            "scheme": "test-scheme",
        },
        expected_network="sandbox",
        expected_scheme="test-scheme",
        live_enabled=True,
    )

    with pytest.raises(FacilitatorContractError, match="network mismatch"):
        client.verify(
            payment={"proof": "test"},
            product={"result_sha256": "hash"},
            idempotency_key="key",
        )


def test_incomplete_response_fails_closed():
    client = FacilitatorClient(
        verify_request=lambda **kwargs: {"verified": True},
        expected_network="sandbox",
        expected_scheme="test-scheme",
        live_enabled=True,
    )

    with pytest.raises(FacilitatorContractError, match="incomplete"):
        client.verify(
            payment={"proof": "test"},
            product={"result_sha256": "hash"},
            idempotency_key="key",
        )
