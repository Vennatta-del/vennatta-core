#!/usr/bin/env python3
"""
CDP sandbox verification-only test.
Does NOT settle, does NOT enable live fulfillment.
Requires: CDP_API_KEY_NAME, CDP_API_KEY_SECRET, CDP_BASE_URL, X402_NETWORKS
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# Add project root to path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.cdp_config import load_cdp_config
from app.cdp_facilitator_transport import CDPFacilitatorTransport
from app.facilitator_http import FacilitatorHttpClient


def http_request(*, method: str, url: str, json_body: dict, headers: dict):
    import urllib.request
    import urllib.error

    data = json.dumps(json_body).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={**headers, "user-agent": "vennatta-cdp-verify/0.1"},
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read().decode("utf-8")
            return json.loads(body)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8")
        print("HTTP error:", exc.code, body, file=sys.stderr)
        raise


def main():
    cfg = load_cdp_config()

    print("CDP config loaded:")
    print("  base_url:", cfg.base_url)
    print("  networks:", cfg.networks)
    print("  api_key_name:", cfg.api_key_name)
    print("  api_key_secret: ***redacted***")

    def wrapped_request(*, method: str, url: str, json: dict, headers: dict):
        return http_request(
            method=method,
            url=url,
            json_body=json,
            headers=headers,
        )

    transport = CDPFacilitatorTransport(
        config=cfg,
        http_request=wrapped_request,
    )

    client = FacilitatorHttpClient(
        request=transport.request,
        base_url=cfg.base_url,
        expected_network=cfg.networks[0],
        expected_scheme="exact",
        live_enabled=True,  # verify only; settlement remains disabled elsewhere
    )

    payment_payload = {
        "payload": "0x00",
        "scheme": "exact",
        "network": cfg.networks[0],
    }
    payment_requirements = {
        "asset": {
            "network": cfg.networks[0],
            "symbol": "USDC",
        },
        "scheme": "exact",
        "maxAmount": "1000000",  # 1 USDC in smallest units
    }

    print(f"\nCalling {cfg.base_url}/platform/v2/x402/verify ...")
    try:
        result = client.verify(
            payment_payload=payment_payload,
            payment_requirements=payment_requirements,
        )
        print("Verify succeeded:")
        print(json.dumps(result, indent=2, sort_keys=True))
    except Exception as exc:
        print("Verify failed:", exc, file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
