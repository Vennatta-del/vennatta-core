"""Optional Solana BGP checkout; disabled unless explicitly configured."""

import os


def configure_bgp_solana(server, route):
    enabled = os.getenv("VENNATTA_SOLANA_ENABLED", "false").strip().lower()
    if enabled not in {"true", "false"}:
        raise RuntimeError("VENNATTA_SOLANA_ENABLED must be true or false")
    if enabled == "false":
        return False

    from solders.pubkey import Pubkey
    from x402.http import PaymentOption
    from x402.mechanisms.svm.constants import SOLANA_MAINNET_CAIP2
    from x402.mechanisms.svm.exact import ExactSvmServerScheme

    recipient = os.getenv("VENNATTA_SOLANA_PAY_TO", "").strip()
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
