import pytest

from app.config import PLACEHOLDER_PAY_TO, Settings


def test_local_mode_is_safe_by_default():
    settings = Settings()
    settings.validate()

    assert settings.environment == "local"
    assert settings.allow_real_settlement is False


def test_local_mode_rejects_real_settlement():
    settings = Settings(
        environment="local",
        allow_real_settlement=True,
    )

    with pytest.raises(RuntimeError, match="Local mode"):
        settings.validate()


def test_non_local_mode_requires_facilitator():
    settings = Settings(
        environment="testnet",
        allow_real_settlement=True,
        facilitator_url="",
        pay_to="0x0000000000000000000000000000000000000002",
    )

    with pytest.raises(RuntimeError, match="facilitator"):
        settings.validate()


def test_non_local_mode_rejects_placeholder_recipient():
    settings = Settings(
        environment="production",
        allow_real_settlement=True,
        facilitator_url="https://facilitator.invalid",
        pay_to=PLACEHOLDER_PAY_TO,
    )

    with pytest.raises(RuntimeError, match="placeholder"):
        settings.validate()


def test_non_local_approved_configuration_validates():
    settings = Settings(
        environment="testnet",
        allow_real_settlement=True,
        facilitator_url="https://facilitator.invalid",
        pay_to="0x0000000000000000000000000000000000000002",
    )

    settings.validate()
