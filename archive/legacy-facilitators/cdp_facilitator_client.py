from __future__ import annotations

from typing import Any

from .cdp_config import CDPConfig, load_cdp_config
from .cdp_facilitator_transport import CDPFacilitatorTransport
from .facilitator_http import FacilitatorHttpClient


def make_cdp_facilitator_http_client(
    *,
    config: CDPConfig | None = None,
    http_request: Any | None = None,
    live_enabled: bool = False,
    expected_network: str = "base-sepolia",
    expected_scheme: str = "exact",
) -> FacilitatorHttpClient:
    if config is None:
        config = load_cdp_config()

    transport = CDPFacilitatorTransport(
        config=config,
        http_request=http_request,
    )

    return FacilitatorHttpClient(
        request=transport.request,
        base_url=config.base_url,
        expected_network=expected_network,
        expected_scheme=expected_scheme,
        live_enabled=live_enabled,
    )
