from __future__ import annotations

import hashlib
import json
from typing import Any


def canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def request_fingerprint(
    *,
    method: str,
    route: str,
    body: Any,
    network: str,
    asset: str,
    amount: str,
    pay_to: str,
    payment_id: str,
) -> str:
    material = {
        "method": method.upper(),
        "route": route,
        "body": body,
        "network": network,
        "asset": asset,
        "amount": amount,
        "pay_to": pay_to.lower(),
        "payment_id": payment_id,
    }
    return hashlib.sha256(canonical_json(material)).hexdigest()
