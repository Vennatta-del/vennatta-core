from __future__ import annotations

from typing import Any
import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from x402 import x402ResourceServer
from x402.extensions.payment_identifier import (
    declare_payment_identifier_extension,
    payment_identifier_resource_server_extension,
)
from x402.http import FacilitatorConfig, HTTPFacilitatorClient
from x402.http.middleware.fastapi import PaymentMiddlewareASGI
from x402.mechanisms.evm.exact import ExactEvmServerScheme

from .config import Settings
from .security_events import EventCollector
from .production_settlement import settlement

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = Settings()
settings.validate()

events = EventCollector()

# Production facilitator for Base mainnet
facilitator = HTTPFacilitatorClient(
    FacilitatorConfig(url="https://x402.org/facilitator")
)

server = x402ResourceServer(facilitator)
server.register(settings.network, ExactEvmServerScheme())
server.register_extension(payment_identifier_resource_server_extension)

# Define monetized routes
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

app = FastAPI(title="Vennatta x402 - Production")


@app.get("/health")
async def health() -> dict[str, Any]:
    """Health check endpoint."""
    return {
        "status": "production",
        "environment": settings.environment,
        "real_settlement": settings.allow_real_settlement,
        "network": settings.network,
        "wallet": settings.pay_to,
    }


@app.get("/__canary__/status")
async def canary(request: Request) -> JSONResponse:
    """Canary endpoint for monitoring."""
    events.record(
        event_type="canary_access",
        source=request.client.host if request.client else "unknown",
        route=request.url.path,
        method=request.method,
    )
    return JSONResponse({"status": "ok"})



# Import and add extraction endpoints
from .extract_document import router as extract_router
from .extract_obsidian import router as obsidian_router

app.include_router(extract_router)
app.include_router(obsidian_router)

# Add x402 payment middleware
app.add_middleware(
    PaymentMiddlewareASGI,
    routes=routes,
    server=server,
)

logger.info("✅ Vennatta x402 production server started")

# Test endpoint without middleware
@app.post("/api/v1/test-payment")
async def test_payment():
    """Simple test endpoint."""
    return {"status": "payment test", "cost": "0.01 USDC"}
