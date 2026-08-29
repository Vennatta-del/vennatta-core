"""CDP configuration with network → base URL mapping and auth headers."""

import os
from dataclasses import dataclass
from typing import Dict

@dataclass
class CDPConfig:
    """CDP API configuration."""
    api_key: str
    api_secret: str
    network: str = "base-sepolia"
    
    @property
    def base_url(self) -> str:
        """Get CDP base URL."""
        if "sandbox" in self.api_key.lower() or "test" in self.network.lower():
            return "https://sandbox.cdp.coinbase.com"
        return "https://api.cdp.coinbase.com"

# Load from environment
CDP_API_KEY = os.getenv("CDP_API_KEY", "2b20d4e3-3855-445b-a3b9-9b6bd40f4dee")
CDP_API_SECRET = os.getenv("CDP_API_SECRET", "p3cNf7gLbXFjdSfj+ivsC7+OybsJXOeswx5POZiAKj+rqTq/S2Fr2FsxWJUvxkWUYA/nGMLlAqGH9IeEfv2q6w==")

# Network → Base URL mapping
NETWORK_URLS: Dict[str, str] = {
    "base-sepolia": "https://sandbox.cdp.coinbase.com",
    "base-mainnet": "https://api.cdp.coinbase.com",
}

print("✅ CDP Config loaded")
print(f"   Sandbox URL: https://sandbox.cdp.coinbase.com")
print(f"   Production URL: https://api.cdp.coinbase.com")
