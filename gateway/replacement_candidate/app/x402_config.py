from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class NetworkConfig:
    id: str
    name: str
    asset: str
    asset_decimals: int
    is_testnet: bool


@dataclass(frozen=True)
class SchemeConfig:
    id: Literal["exact", "upto"]
    description: str


NETWORKS: dict[str, NetworkConfig] = {
    "base": NetworkConfig(
        id="base",
        name="Base",
        asset="USDC",
        asset_decimals=6,
        is_testnet=False,
    ),
    "base-sepolia": NetworkConfig(
        id="base-sepolia",
        name="Base Sepolia",
        asset="USDC",
        asset_decimals=6,
        is_testnet=True,
    ),
    "polygon": NetworkConfig(
        id="polygon",
        name="Polygon",
        asset="USDC",
        asset_decimals=6,
        is_testnet=False,
    ),
    "polygon-amoy": NetworkConfig(
        id="polygon-amoy",
        name="Polygon Amoy",
        asset="USDC",
        asset_decimals=6,
        is_testnet=True,
    ),
    "solana": NetworkConfig(
        id="solana",
        name="Solana",
        asset="USDC",
        asset_decimals=6,
        is_testnet=False,
    ),
    "solana-devnet": NetworkConfig(
        id="solana-devnet",
        name="Solana Devnet",
        asset="USDC",
        asset_decimals=6,
        is_testnet=True,
    ),
}


SCHEMES: dict[str, SchemeConfig] = {
    "exact": SchemeConfig(
        id="exact",
        description="Fixed-price payment known upfront",
    ),
    "upto": SchemeConfig(
        id="upto",
        description="Maximum authorized amount; actual settled ≤ max",
    ),
}


class ConfigError(RuntimeError):
    pass


def get_network(network_id: str) -> NetworkConfig:
    try:
        return NETWORKS[network_id]
    except KeyError:
        raise ConfigError(f"unsupported network: {network_id}")


def get_scheme(scheme_id: str) -> SchemeConfig:
    try:
        return SCHEMES[scheme_id]
    except KeyError:
        raise ConfigError(f"unsupported scheme: {scheme_id}")
