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
from x402.http.middleware.fastapi import PaymentMiddlewareASGI
from x402.mechanisms.evm.exact import ExactEvmServerScheme

from .config import Settings
from .security_events import EventCollector
from .production_settlement import settlement
from .facilitator import VennattaFacilitator

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = Settings()
settings.validate()

events = EventCollector()

# Custom Vennatta facilitator with real EVM validation
facilitator = VennattaFacilitator(
    rpc_url=settings.rpc_url,
    supported_networks=[settings.network],
    supported_schemes=["exact"],
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
            declare_payment_identifier_extension(
                resource="extract-document",
                description="Extract structured data from documents",
            ),
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
            declare_payment_identifier_extension(
                resource="extract-obsidian",
                description="Extract structured data from Obsidian vaults",
            ),
        },
    },
    "POST /v2/paid-resource": {
        "accepts": {
            "scheme": "exact",
            "network": settings.network,
            "payTo": settings.pay_to,
            "price": "0.01 USDC",
        },
        "resource": {
            "url": "/v2/paid-resource",
            "description": "Example paid resource endpoint",
        },
    },
}

# Create FastAPI app
app = FastAPI(
    title="Vennatta Core API",
    description="Production API with x402 payment protection",
    version="2.0.0",
)

# Register routes
@app.post("/api/v1/extract-document")
async def extract_document(request: Request, document: dict[str, Any]) -> JSONResponse:
    """Extract structured data from documents."""
    return JSONResponse({"status": "success", "data": {"extracted": "document data"}})

@app.post("/api/v1/extract-obsidian")
async def extract_obsidian(request: Request, vault: dict[str, Any]) -> JSONResponse:
    """Extract structured data from Obsidian vaults."""
    return JSONResponse({"status": "success", "data": {"extracted": "obsidian data"}})

@app.post("/v2/paid-resource")
async def paid_resource(request: Request) -> JSONResponse:
    """Example paid resource endpoint."""
    return JSONResponse({"status": "success", "data": {"resource": "paid content"}})

# Add x402 payment middleware AFTER routers are registered
app.add_middleware(
    PaymentMiddlewareASGI,
    server=server,
    routes=routes,
)

# Register settlement handler
settlement.register(server)

logger.info("✅ Vennatta production server started")
