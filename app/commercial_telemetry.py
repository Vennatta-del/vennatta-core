import logging
import time
import uuid
from collections.abc import Mapping
from typing import Any

logger = logging.getLogger("vennatta.commercial")

def request_id() -> str:
    return uuid.uuid4().hex

def start_timer() -> float:
    return time.perf_counter()

def elapsed_ms(started: float) -> int:
    return round((time.perf_counter() - started) * 1000)

def log_request(
    *,
    request_id: str,
    route: str,
    status: int,
    elapsed_ms: int,
    buyer: str | None = None,
    transaction: str | None = None,
    extra: Mapping[str, Any] | None = None,
) -> None:
    fields = {
        "event": "commercial_request",
        "request_id": request_id,
        "route": route,
        "status": status,
        "elapsed_ms": elapsed_ms,
        "buyer": buyer,
        "transaction": transaction,
    }
    if extra:
        fields.update(extra)
    logger.info("%s", fields)
