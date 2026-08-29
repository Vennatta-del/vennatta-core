from __future__ import annotations

import hashlib
import json
import secrets
from dataclasses import dataclass
from typing import Any, Callable

from .idempotency_store import IdempotencyStore


class SettlementGateError(RuntimeError):
    pass


@dataclass(frozen=True)
class SettlementReceipt:
    status: str
    idempotency_key: str
    settlement_id: str | None
    dry_run: bool


class SettlementAdapter:
    def __init__(
        self,
        *,
        verify: Callable[..., dict[str, Any]],
        settle: Callable[..., dict[str, Any]] | None = None,
        dry_run: bool = True,
        idempotency_store: IdempotencyStore | None = None,
    ) -> None:
        self._verify = verify
        self._settle = settle
        self._dry_run = dry_run
        self._store = idempotency_store or IdempotencyStore(
            ".settlement-idempotency.sqlite3"
        )

    @staticmethod
    def make_idempotency_key(
        *,
        product: dict[str, Any],
        request_id: str,
    ) -> str:
        if not request_id:
            raise SettlementGateError("request_id is required")

        canonical = json.dumps(
            {
                "request_id": request_id,
                "product_hash": product.get("result_sha256"),
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def execute(
        self,
        *,
        reviewed_product: dict[str, Any],
        request_id: str,
        payment: dict[str, Any],
    ) -> SettlementReceipt:
        if not isinstance(reviewed_product, dict):
            raise SettlementGateError("reviewed product is required")

        if reviewed_product.get("reviewed") is not True:
            raise SettlementGateError(
                "fulfillment requires an approved review"
            )

        product = reviewed_product.get("product")
        if not isinstance(product, dict):
            raise SettlementGateError("reviewed product payload is invalid")

        if product.get("review_status") not in (None,):
            raise SettlementGateError(
                "unexpected product review field"
            )

        key = self.make_idempotency_key(
            product=product,
            request_id=request_id,
        )

        if not self._store.claim(key):
            raise SettlementGateError("replayed settlement request")

        if not isinstance(payment, dict):
            raise SettlementGateError("payment proof is required")

        verification = self._verify(
            payment=payment,
            product=product,
            idempotency_key=key,
        )

        if not isinstance(verification, dict):
            raise SettlementGateError("payment verification failed")

        if verification.get("verified") is not True:
            raise SettlementGateError("payment was not verified")

        if self._dry_run:
            return SettlementReceipt(
                status="dry_run_verified",
                idempotency_key=key,
                settlement_id=None,
                dry_run=True,
            )

        if self._settle is None:
            raise SettlementGateError(
                "live settlement requires an explicit settle callable"
            )

        settlement = self._settle(
            payment=payment,
            product=product,
            idempotency_key=key,
        )

        if not isinstance(settlement, dict):
            raise SettlementGateError("settlement response is invalid")

        if settlement.get("settled") is not True:
            raise SettlementGateError("settlement was not confirmed")

        settlement_id = settlement.get("settlement_id")
        if not isinstance(settlement_id, str) or not settlement_id:
            raise SettlementGateError(
                "confirmed settlement requires settlement_id"
            )

        return SettlementReceipt(
            status="settled",
            idempotency_key=key,
            settlement_id=settlement_id,
            dry_run=False,
        )


def fulfill_after_settlement(
    *,
    receipt: SettlementReceipt,
    fulfill: Callable[[], Any],
) -> Any:
    if receipt.status not in {"dry_run_verified", "settled"}:
        raise SettlementGateError(
            "fulfillment requires verified settlement state"
        )

    if receipt.status == "dry_run_verified":
        raise SettlementGateError(
            "dry-run verification cannot authorize fulfillment"
        )

    return fulfill()
