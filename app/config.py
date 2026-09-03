from __future__ import annotations

import os
from dataclasses import dataclass


PLACEHOLDER_PAY_TO = "0xdadeFD58681C5C5df68681735752a40CaAE5E152"


@dataclass(frozen=True)
class Settings:
    environment: str = "production"
    allow_real_settlement: bool = True
    facilitator_url: str = os.getenv("VENNATTA_FACILITATOR_URL", "")
    network: str = os.getenv("VENNATTA_NETWORK", "eip155:8453")
    pay_to: str = os.getenv("VENNATTA_PAY_TO", PLACEHOLDER_PAY_TO)
    placeholder_price: str = os.getenv(
        "VENNATTA_PLACEHOLDER_PRICE", "0.01 USDC"
    )

    def validate(self) -> None:
        if self.environment not in {"local", "testnet", "production"}:
            raise RuntimeError("Unsupported candidate environment")

        if not self.network.startswith("eip155:"):
            raise RuntimeError("Candidate currently permits EVM networks only")

        if self.environment == "local":
            if self.allow_real_settlement:
                raise RuntimeError(
                    "Local mode cannot enable real settlement"
                )
            return

        if not self.facilitator_url:
            raise RuntimeError(
                "Non-local mode requires an explicit facilitator URL"
            )

        if not self.allow_real_settlement:
            raise RuntimeError(
                "Non-local mode requires explicit settlement approval"
            )

        if self.pay_to.lower() == PLACEHOLDER_PAY_TO.lower():
            raise RuntimeError(
                "Real settlement cannot use the placeholder payTo address"
            )
