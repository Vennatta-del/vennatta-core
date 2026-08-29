import pytest

from app.cdp_config import CDPConfig
from app.cdp_facilitator_transport import CDPFacilitatorTransport


def test_transport_requires_http_request():
    cfg = CDPConfig(
        api_key_name="test",
        api_key_secret="secret",
        base_url="https://sandbox.example",
        networks=("base-sepolia",),
    )
    transport = CDPFacilitatorTransport(config=cfg)

    with pytest.raises(RuntimeError, match="http_request callable"):
        transport.request(
            method="POST",
            url="https://sandbox.example/v2/x402/verify",
            json={},
            headers={},
        )


def test_transport_calls_http_request_with_auth():
    calls = []

    def http_request(**kwargs):
        calls.append(kwargs)
        return {"isValid": True, "network": "base-sepolia", "scheme": "exact"}

    cfg = CDPConfig(
        api_key_name="test",
        api_key_secret="secret",
        base_url="https://sandbox.example",
        networks=("base-sepolia",),
    )
    transport = CDPFacilitatorTransport(config=cfg, http_request=http_request)

    result = transport.request(
        method="POST",
        url="https://sandbox.example/v2/x402/verify",
        json={"paymentPayload": {}, "paymentRequirements": {}},
        headers={},
    )

    assert result["isValid"] is True
    assert calls[0]["method"] == "POST"
    assert "authorization" in calls[0]["headers"]
    assert calls[0]["headers"]["content-type"] == "application/json"
