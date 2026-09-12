from __future__ import annotations

BLOCKED_ADDRESSES: frozenset[str] = frozenset({
    "0xf111122404b8C2FC01dfF89C65D3104fbb608008".lower(),
})

def is_blocked_address(address: str | None) -> bool:
    return bool(address) and address.lower() in BLOCKED_ADDRESSES
