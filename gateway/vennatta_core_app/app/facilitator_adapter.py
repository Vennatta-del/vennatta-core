from __future__ import annotations

from typing import Any

from .facilitator_contract import FacilitatorContractError
from .facilitator_http import FacilitatorHttpClient


class FacilitatorAdapterError(RuntimeError):
    pass


class FacilitatorAdapter:
    def __init__(
        self,
        *,
        http_client: FacilitatorHttpClient,
    ) -> None:
        self._http = http_client

    def verify(
        self,
        *,
        payment: dict[str, Any],
        product: dict[str, Any],
        idempotency_key: str,
    ) -> dict[str, Any]:
        try:
            result = self._http.verify(
                payment_payload=payment,
                payment_requirements={
                    "network": self._http._expected_network,
                    "scheme": self._http._expected_scheme,
                },
            )
        except FacilitatorContractError as exc:
            raise FacilitatorAdapterError(str(exc)) from exc

        return {
            "verified": True,
            "network": result["network"],
            "scheme": result["scheme"],
            "payment_id": result["payment_id"],
        }

    def settle(
        self,
        *,
        payment: dict[str, Any],
        product: dict[str, Any],
        idempotency_key: str,
    ) -> dict[str, Any]:
        try:
            result = self._http.settle(
                payment_payload=payment,
                payment_requirements={
                    "network": self._http._expected_network,
                    "scheme": self._http._expected_scheme,
                },
            )
        except FacilitatorContractError as exc:
            raise FacilitatorAdapterError(str(exc)) from exc

        return {
            "settled": True,
            "settlement_id": result["settlement_id"],
        }
