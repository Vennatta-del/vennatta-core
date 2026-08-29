import pytest

from app.x402_config import (
    ConfigError,
    get_network,
    get_scheme,
    NETWORKS,
    SCHEMES,
)


def test_base_network_is_configured():
    net = get_network("base")

    assert net.name == "Base"
    assert net.asset == "USDC"
    assert net.asset_decimals == 6
    assert net.is_testnet is False


def test_base_sepolia_is_testnet():
    net = get_network("base-sepolia")

    assert net.is_testnet is True


def test_solana_network_is_configured():
    net = get_network("solana")

    assert net.name == "Solana"
    assert net.asset == "USDC"
    assert net.asset_decimals == 6
    assert net.is_testnet is False


def test_solana_devnet_is_testnet():
    net = get_network("solana-devnet")

    assert net.is_testnet is True


def test_exact_scheme_is_configured():
    scheme = get_scheme("exact")

    assert scheme.id == "exact"
    assert "Fixed-price" in scheme.description


def test_upto_scheme_is_configured():
    scheme = get_scheme("upto")

    assert scheme.id == "upto"
    assert "Maximum" in scheme.description


def test_unknown_network_fails_closed():
    with pytest.raises(ConfigError, match="unsupported network"):
        get_network("unknown")


def test_unknown_scheme_fails_closed():
    with pytest.raises(ConfigError, match="unsupported scheme"):
        get_scheme("unknown")
