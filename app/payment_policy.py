from __future__ import annotations

from decimal import Decimal


def deterministic_placeholder_price() -> str:
    return "$0.001"


def price_floor() -> Decimal:
    return Decimal("0.001")
