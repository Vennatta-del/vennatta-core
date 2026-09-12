from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class CDPConfig:
    api_key: str
    api_secret: str
    network: str = "eip155:8453"

    def validate(self) -> None:
        if not self.api_key or not self.api_secret:
            raise RuntimeError(
                "CDP credentials must be supplied through the runtime secret store"
            )
        if self.network.startswith("test") or "sandbox" in self.network.lower():
            raise RuntimeError("Sandbox configuration cannot run in production")


CDP_API_KEY = os.getenv("CDP_API_KEY_ID", "")
CDP_API_SECRET = os.getenv("CDP_API_KEY_SECRET", "")

config = CDPConfig(
    api_key=CDP_API_KEY,
    api_secret=CDP_API_SECRET,
    network=os.getenv("VENNATTA_NETWORK", "eip155:8453"),
)
