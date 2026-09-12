from __future__ import annotations

from typing import Any, Callable

from .facilitator_contract import FacilitatorContractError


class FacilitatorHttpClient:
    def __init__(
        self,
        *,
        request: Callable[..., dict[str, Any]],
        base_url: str,
        expected_network: str,
        expected_scheme: str,
        live_enabled: bool = False,
    ) -> None:
        self._request = request
        self._base_url = base_url.rstrip("/")
        self._expected_network = expected_network
        self._expected_scheme = expected_scheme
        self._live_enabled = live_enabled

    def _post(
        self,
        *,
        path: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        if self._live_enabled is not True:
            raise FacilitatorContractError(
                "live facilitator HTTP calls are disabled"
            )

        response = self._request(
            method="POST",
            url=f"{self._base_url}{path}",
            json=payload,
            headers={"content-type": "application/json"},
        )

        if not isinstance(response, dict):
            raise FacilitatorContractError(
                "facilitator HTTP response must be an object"
            )

        return response

    def verify(
        self,
        *,
        payment_payload: dict[str, Any],
        payment_requirements: dict[str, Any],
    ) -> dict[str, Any]:
        response = self._post(
            path="/v2/x402/verify",
            payload={
                "paymentPayload": payment_payload,
                "paymentRequirements": payment_requirements,
            },
        )

        verified = response.get("isValid")
        if not isinstance(verified, bool):
            raise FacilitatorContractError(
                "verify response lacks isValid"
            )

        network = response.get("network")
        scheme = response.get("scheme")

        if network != self._expected_network:
            raise FacilitatorContractError("verify network mismatch")

        if scheme != self._expected_scheme:
            raise FacilitatorContractError("verify scheme mismatch")

        if verified is not True:
            reason = (
                response.get("invalidReason")
                or response.get("errorReason")
                or "payment was not verified"
            )
            raise FacilitatorContractError(str(reason))

        return {
            "verified": True,
            "network": network,
            "scheme": scheme,
            "payment_id": response.get("paymentId"),
            "raw": response,
        }

    def settle(
        self,
        *,
        payment_payload: dict[str, Any],
        payment_requirements: dict[str, Any],
    ) -> dict[str, Any]:
        response = self._post(
            path="/v2/x402/settle",
            payload={
                "paymentPayload": payment_payload,
                "paymentRequirements": payment_requirements,
            },
        )

        settled = response.get("success")
        if not isinstance(settled, bool):
            raise FacilitatorContractError(
                "settle response lacks success"
            )

        if settled is not True:
            reason = (
                response.get("errorReason")
                or response.get("invalidReason")
                or "settlement was not confirmed"
            )
            raise FacilitatorContractError(str(reason))

        settlement_id = response.get("transaction")
        if not isinstance(settlement_id, str) or not settlement_id:
            raise FacilitatorContractError(
                "settlement response lacks transaction"
            )

        return {
            "settled": True,
            "settlement_id": settlement_id,
            "raw": response,
        }
