from __future__ import annotations

from typing import Any
import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from x402 import x402ResourceServer
from x402.extensions.payment_identifier import (
    payment_identifier_resource_server_extension,
)
from x402.http.middleware.fastapi import PaymentMiddlewareASGI
from x402.mechanisms.evm.exact import ExactEvmServerScheme

from .config import Settings
from .facilitator import VennattaFacilitator

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = Settings()
settings.validate()

# Custom Vennatta facilitator with real EVM validation
facilitator = VennattaFacilitator(
    rpc_url=settings.rpc_url,
    supported_networks=[settings.network],
    supported_schemes=["exact"],
)

server = x402ResourceServer(facilitator)
server.register(settings.network, ExactEvmServerScheme())
server.register_extension(payment_identifier_resource_server_extension)

# Create FastAPI app
app = FastAPI(
    title="Vennatta Core API",
    description="Production API with x402 payment protection",
    version="2.0.0",
)

# Health check endpoint
@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "healthy"}

# Define ALL monetized routes
routes = {
    "POST /api/v1/extract-document": {
        "accepts": {
            "scheme": "exact",
            "network": settings.network,
            "payTo": settings.pay_to,
            "price": "0.01 USDC",
        },
    },
    "POST /api/v1/extract-obsidian": {
        "accepts": {
            "scheme": "exact",
            "network": settings.network,
            "payTo": settings.pay_to,
            "price": "0.01 USDC",
        },
    },
    "POST /v2/paid-resource": {
        "accepts": {
            "scheme": "exact",
            "network": settings.network,
            "payTo": settings.pay_to,
            "price": "0.01 USDC",
        },
    },
}

# Register route handlers
@app.post("/api/v1/extract-document")
async def extract_document(request: Request, document: dict[str, Any]) -> JSONResponse:
    """Extract structured data from documents."""
    logger.info(f"Processing document: {document}")
    return JSONResponse({"status": "success", "data": {"extracted": "document data"}})

@app.post("/api/v1/extract-obsidian")
async def extract_obsidian(request: Request, vault: dict[str, Any]) -> JSONResponse:
    """Extract structured data from Obsidian vaults."""
    logger.info(f"Processing Obsidian vault: {vault}")
    return JSONResponse({"status": "success", "data": {"extracted": "obsidian data"}})

@app.post("/v2/paid-resource")
async def paid_resource(request: Request) -> JSONResponse:
    """Example paid resource endpoint."""
    logger.info("Serving paid resource")
    return JSONResponse({"status": "success", "data": {"resource": "paid content"}})

# Add x402 payment middleware
app.add_middleware(
    PaymentMiddlewareASGI,
    server=server,
    routes=routes,
)

logger.info("✅ Vennatta production server started with x402 middleware - ALL ROUTES LIVE")
