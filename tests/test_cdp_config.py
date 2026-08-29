import os
import pytest

from app.cdp_config import CDPConfig, load_cdp_config


def test_load_cdp_config_requires_keys(monkeypatch):
    monkeypatch.delenv("CDP_API_KEY_NAME", raising=False)
    monkeypatch.delenv("CDP_API_KEY_SECRET", raising=False)

    with pytest.raises(ValueError, match="CDP_API_KEY_NAME"):
        load_cdp_config()


def test_load_cdp_config_defaults(monkeypatch):
    monkeypatch.setenv("CDP_API_KEY_NAME", "test-key")
    monkeypatch.setenv("CDP_API_KEY_SECRET", "test-secret")
    monkeypatch.delenv("CDP_BASE_URL", raising=False)
    monkeypatch.delenv("X402_NETWORKS", raising=False)

    cfg = load_cdp_config()

    assert cfg.api_key_name == "test-key"
    assert cfg.api_key_secret == "test-secret"
    assert cfg.base_url == "https://sandbox.cdp.coinbase.com"
    assert cfg.networks == (
        "base-sepolia",
        "polygon-amoy",
        "solana-devnet",
    )


def test_load_cdp_config_rejects_unknown_network(monkeypatch):
    monkeypatch.setenv("CDP_API_KEY_NAME", "test-key")
    monkeypatch.setenv("CDP_API_KEY_SECRET", "test-secret")
    monkeypatch.setenv("X402_NETWORKS", "unknown-network")

    with pytest.raises(ValueError, match="unsupported CDP network"):
        load_cdp_config()
