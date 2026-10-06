"""Optional Solana BGP checkout; disabled unless explicitly configured."""

import os
from pathlib import Path


def _solana_setting(name: str, default: str = "") -> str:
    value = os.getenv(name)
    if value is not None:
        return value.strip()

    try:
        value = (Path("/etc/secrets") / name).read_text(
            encoding="utf-8"
        ).strip()
    except FileNotFoundError:
        return default

    prefix = name + "="
    if value.startswith(prefix):
        value = value[len(prefix):].strip()

    if (
        len(value) >= 2
        and value[0] == value[-1]
        and value[0] in ("'", '"')
    ):
        value = value[1:-1].strip()

    if not value or "\n" in value or "\r" in value:
        raise RuntimeError(f"{name} secret file must contain one nonempty value")

    return value


def configure_bgp_solana(server, route):
    enabled = _solana_setting("VENNATTA_SOLANA_ENABLED", "false").lower()
    if enabled not in {"true", "false"}:
        raise RuntimeError("VENNATTA_SOLANA_ENABLED must be true or false")
    if enabled == "false":
        return False

    from solders.pubkey import Pubkey
    from x402.http import PaymentOption
    from x402.mechanisms.svm.constants import SOLANA_MAINNET_CAIP2
    from x402.mechanisms.svm.exact import ExactSvmServerScheme

    recipient = _solana_setting("VENNATTA_SOLANA_PAY_TO")
    if not recipient:
        raise RuntimeError("Enabled Solana requires VENNATTA_SOLANA_PAY_TO")
    try:
        Pubkey.from_string(recipient)
    except ValueError as exc:
        raise RuntimeError("Invalid Solana receiving address") from exc

    option = PaymentOption(
        scheme="exact",
        price="$0.05",
        network=SOLANA_MAINNET_CAIP2,
        pay_to=recipient,
    )
    server.register(SOLANA_MAINNET_CAIP2, ExactSvmServerScheme())
    route.accepts.append(option)
    return True
