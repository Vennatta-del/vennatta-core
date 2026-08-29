from __future__ import annotations

from typing import Any


def fulfill_inert_contract(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": "candidate-only",
        "product": "temporary-inert-resource",
        "accepted_input_keys": sorted(payload.keys()),
        "fulfillment_enabled": False,
    }
