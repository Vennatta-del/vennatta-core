from __future__ import annotations

from dataclasses import dataclass
from threading import RLock
from typing import Any


class LedgerConflict(Exception):
    """Raised when a payment ID is reused for a different request."""


@dataclass(frozen=True)
class LedgerEntry:
    payment_id: str
    fingerprint: str
    status: str
    response: dict[str, Any] | None = None
    transaction_hash: str | None = None


class InMemoryLedger:
    def __init__(self) -> None:
        self._entries: dict[str, LedgerEntry] = {}
        self._lock = RLock()

    def begin(self, payment_id: str, fingerprint: str) -> LedgerEntry:
        with self._lock:
            existing = self._entries.get(payment_id)

            if existing is not None:
                if existing.fingerprint != fingerprint:
                    raise LedgerConflict(
                        "payment identifier fingerprint mismatch"
                    )
                return existing

            entry = LedgerEntry(
                payment_id=payment_id,
                fingerprint=fingerprint,
                status="pending",
            )
            self._entries[payment_id] = entry
            return entry

    def fulfill(
        self,
        payment_id: str,
        response: dict[str, Any],
        transaction_hash: str,
    ) -> LedgerEntry:
        with self._lock:
            existing = self._entries[payment_id]

            updated = LedgerEntry(
                payment_id=existing.payment_id,
                fingerprint=existing.fingerprint,
                status="fulfilled",
                response=response,
                transaction_hash=transaction_hash,
            )
            self._entries[payment_id] = updated
            return updated

    def get(self, payment_id: str) -> LedgerEntry | None:
        with self._lock:
            return self._entries.get(payment_id)
