from __future__ import annotations

from x402.schemas import (
    PaymentPayload,
    PaymentRequirements,
    SettleResponse,
    SupportedKind,
    SupportedResponse,
    VerifyResponse,
)


SYNTHETIC_TRANSACTION = "synthetic-local-settlement-do-not-use"
TEST_MARKER = "local-test-fixture"


class SyntheticFacilitator:
    """Test-only facilitator. Never use for testnet or mainnet."""

    def get_supported(self) -> SupportedResponse:
        return SupportedResponse(
            kinds=[
                SupportedKind(
                    x402Version=2,
                    scheme="exact",
                    network="eip155:8453",
                )
            ]
        )

    async def verify(
        self,
        payload: PaymentPayload,
        requirements: PaymentRequirements,
    ) -> VerifyResponse:
        marker = payload.payload.get("testMarker")

        if marker != TEST_MARKER:
            return VerifyResponse(
                isValid=False,
                invalidReason="synthetic_test_marker_required",
                invalidMessage=(
                    "Synthetic facilitator accepts test fixtures only"
                ),
            )

        return VerifyResponse(
            isValid=True,
            payer="0x0000000000000000000000000000000000000002",
        )

    async def settle(
        self,
        payload: PaymentPayload,
        requirements: PaymentRequirements,
    ) -> SettleResponse:
        marker = payload.payload.get("testMarker")

        if marker != TEST_MARKER:
            return SettleResponse(
                success=False,
                errorReason="synthetic_test_marker_required",
                errorMessage=(
                    "Synthetic facilitator accepts test fixtures only"
                ),
                transaction=SYNTHETIC_TRANSACTION,
                network="eip155:8453",
            )

        return SettleResponse(
            success=True,
            payer="0x0000000000000000000000000000000000000002",
            transaction=SYNTHETIC_TRANSACTION,
            network="eip155:8453",
            amount="0",
            extra={"synthetic": True},
        )
