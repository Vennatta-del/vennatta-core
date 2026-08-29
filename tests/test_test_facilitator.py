import pytest

from app.test_facilitator import (
    SYNTHETIC_TRANSACTION,
    TEST_MARKER,
    SyntheticFacilitator,
)
from x402.schemas import PaymentPayload, PaymentRequirements


def requirements() -> PaymentRequirements:
    return PaymentRequirements(
        scheme="exact",
        network="eip155:8453",
        asset="placeholder",
        amount="0",
        payTo="0x0000000000000000000000000000000000000001",
        maxTimeoutSeconds=300,
    )


def payload(marker: str | None) -> PaymentPayload:
    data = {} if marker is None else {"testMarker": marker}
    return PaymentPayload(
        payload=data,
        accepted=requirements(),
    )


def test_supported_response_is_local_exact_evm():
    supported = SyntheticFacilitator().get_supported()

    assert len(supported.kinds) == 1
    assert supported.kinds[0].x402_version == 2
    assert supported.kinds[0].scheme == "exact"
    assert supported.kinds[0].network == "eip155:8453"


@pytest.mark.asyncio
async def test_unmarked_fixture_is_rejected():
    result = await SyntheticFacilitator().verify(payload(None), requirements())

    assert result.is_valid is False


@pytest.mark.asyncio
async def test_marked_fixture_is_accepted_and_settled():
    facilitator = SyntheticFacilitator()
    result = await facilitator.verify(
        payload(TEST_MARKER),
        requirements(),
    )
    settlement = await facilitator.settle(
        payload(TEST_MARKER),
        requirements(),
    )

    assert result.is_valid is True
    assert settlement.success is True
    assert settlement.transaction == SYNTHETIC_TRANSACTION
    assert settlement.extra == {"synthetic": True}
