from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


class FacilitatorContractError(RuntimeError):
    pass


@dataclass(frozen=True)
class VerificationResult:
    verified: bool
    network: str
    scheme: str
    payment_id: str | None


class FacilitatorClient:
    def __init__(
        self,
        *,
        verify_request: Callable[..., dict[str, Any]],
        expected_network: str,
        expected_scheme: str,
        live_enabled: bool = False,
    ) -> None:
        self._verify_request = verify_request
        self._expected_network = expected_network
        self._expected_scheme = expected_scheme
        self._live_enabled = live_enabled

    def verify(
        self,
        *,
        payment: dict[str, Any],
        product: dict[str, Any],
        idempotency_key: str,
    ) -> dict[str, Any]:
        if self._live_enabled is not True:
            raise FacilitatorContractError(
                "live facilitator verification is disabled"
            )

        response = self._verify_request(
            payment=payment,
            product=product,
            idempotency_key=idempotency_key,
        )

        if not isinstance(response, dict):
            raise FacilitatorContractError(
                "facilitator response must be an object"
            )

        required = {"verified", "network", "scheme"}
        if not required.issubset(response):
            raise FacilitatorContractError(
                "facilitator response schema is incomplete"
            )

        verified = response["verified"]
        network = response["network"]
        scheme = response["scheme"]

        if not isinstance(verified, bool):
            raise FacilitatorContractError(
                "facilitator verified must be boolean"
            )

        if network != self._expected_network:
            raise FacilitatorContractError(
                "facilitator network mismatch"
            )

        if scheme != self._expected_scheme:
            raise FacilitatorContractError(
                "facilitator scheme mismatch"
            )

        if verified is not True:
            raise FacilitatorContractError(
                "facilitator did not verify payment"
            )

        payment_id = response.get("payment_id")
        if payment_id is not None and not isinstance(payment_id, str):
            raise FacilitatorContractError(
                "facilitator payment_id is invalid"
            )

        return {
            "verified": True,
            "network": network,
            "scheme": scheme,
            "payment_id": payment_id,
        }
