import pytest

from app.cdp_config import CDPConfig
from app.cdp_facilitator_client import make_cdp_facilitator_http_client
from app.facilitator_contract import FacilitatorContractError


def test_cdp_client_is_disabled_by_default():
    cfg = CDPConfig(
        api_key_name="test",
        api_key_secret="secret",
        base_url="https://sandbox.cdp.coinbase.com",
        networks=("base-sepolia",),
    )

    client = make_cdp_facilitator_http_client(
        config=cfg,
        expected_network="base-sepolia",
        expected_scheme="exact",
    )

    with pytest.raises(FacilitatorContractError, match="disabled"):
        client.verify(
            payment_payload={"payload": "test"},
            payment_requirements={
                "network": "base-sepolia",
                "scheme": "exact",
            },
        )


def test_cdp_client_shape_with_mock_transport():
    calls = []

    def http_request(**kwargs):
        calls.append(kwargs)
        return {
            "isValid": True,
            "network": "base-sepolia",
            "scheme": "exact",
            "paymentId": "cdp-payment-1",
        }

    cfg = CDPConfig(
        api_key_name="test",
        api_key_secret="secret",
        base_url="https://sandbox.cdp.coinbase.com",
        networks=("base-sepolia",),
    )

    client = make_cdp_facilitator_http_client(
        config=cfg,
        http_request=http_request,
        expected_network="base-sepolia",
        expected_scheme="exact",
        live_enabled=True,
    )

    result = client.verify(
        payment_payload={"payload": "test"},
        payment_requirements={
            "network": "base-sepolia",
            "scheme": "exact",
        },
    )

    assert result["verified"] is True
    assert result["payment_id"] == "cdp-payment-1"
    assert calls[0]["url"].endswith("/v2/x402/verify")
    assert "authorization" in calls[0]["headers"]
