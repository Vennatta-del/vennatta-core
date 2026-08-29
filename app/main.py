from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from x402 import x402ResourceServer
from x402.extensions.payment_identifier import (
    declare_payment_identifier_extension,
    payment_identifier_resource_server_extension,
)
from x402.http import FacilitatorConfig, HTTPFacilitatorClient

from .test_facilitator import SyntheticFacilitator
from x402.http.middleware.fastapi import PaymentMiddlewareASGI
from x402.mechanisms.evm.exact import ExactEvmServerScheme

from .config import Settings
from .security_events import EventCollector
from .production_settlement import settlement

settings = Settings()
settings.validate()

events = EventCollector()

# Production mode - real settlement
if False and settings.environment == "local":  # Disabled for production
    facilitator = SyntheticFacilitator()
else:
    facilitator = HTTPFacilitatorClient(
        FacilitatorConfig(url=settings.facilitator_url)
    )

server = x402ResourceServer(facilitator)
server.register(settings.network, ExactEvmServerScheme())
server.register_extension(payment_identifier_resource_server_extension)

routes = {
    "POST /api/v1/extract-document": {
        "accepts": {
            "scheme": "exact",
            "network": settings.network,
            "payTo": settings.pay_to,
            "price": "0.01 USDC",
        },
        "extensions": {
            payment_identifier_resource_server_extension.key:
                declare_payment_identifier_extension(required=True)
        },
    },
    "POST /api/v1/extract-obsidian": {
        "accepts": {
            "scheme": "exact",
            "network": settings.network,
            "payTo": settings.pay_to,
            "price": "0.01 USDC",
        },
        "extensions": {
            payment_identifier_resource_server_extension.key:
                declare_payment_identifier_extension(required=True)
        },
    },
    "POST /v2/paid-resource": {
        "accepts": {
            "scheme": "exact",
            "network": settings.network,
            "payTo": settings.pay_to,
            "price": settings.placeholder_price,
        },
        "extensions": {
            payment_identifier_resource_server_extension.key:
                declare_payment_identifier_extension(required=True)
        },
    }
}

app = FastAPI(title="Vennatta x402 Replacement Candidate")


@app.get("/health")
async def health() -> dict[str, Any]:
    return {
        "status": "candidate",
        "environment": settings.environment,
        "real_settlement": settings.allow_real_settlement,
        "network": settings.network,
    }


@app.get("/__canary__/status")
async def canary(request: Request) -> JSONResponse:
    events.record(
        event_type="canary_access",
        source=request.client.host if request.client else "unknown",
        route=request.url.path,
        method=request.method,
    )
    return JSONResponse({"status": "ok"})


# Settlement handler is ready
# TODO: Integrate settlement.verify_and_settle() with x402 middleware

app.add_middleware(
    PaymentMiddlewareASGI,
    routes=routes,
    server=server,
)

# Import and add extract-document endpoint
from .extract_document import router as extract_router
app.include_router(extract_router)

# Import and add obsidian-extract endpoint
from .extract_obsidian import router as obsidian_router
app.include_router(obsidian_router)

# Add logging for payment verification
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("x402")
