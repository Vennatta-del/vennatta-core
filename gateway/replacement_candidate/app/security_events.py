from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from threading import Lock


@dataclass(frozen=True)
class SecurityEvent:
    event_type: str
    source_hash: str
    route: str
    method: str
    timestamp: str


class EventCollector:
    def __init__(self) -> None:
        self._events: list[SecurityEvent] = []
        self._lock = Lock()

    def record(
        self,
        *,
        event_type: str,
        source: str,
        route: str,
        method: str,
    ) -> SecurityEvent:
        event = SecurityEvent(
            event_type=event_type,
            source_hash=sha256(source.encode("utf-8")).hexdigest(),
            route=route,
            method=method,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        with self._lock:
            self._events.append(event)
        return event

    def snapshot(self) -> list[SecurityEvent]:
        with self._lock:
            return list(self._events)
