"""Vennatta Core API with x402 payment protection."""

from __future__ import annotations

from typing import Any
import logging
import traceback

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from x402 import x402ResourceServer
from x402.extensions.payment_identifier import (
    payment_identifier_resource_server_extension,
)
from x402.http.middleware.fastapi import PaymentMiddlewareASGI

from .config import Settings
from .facilitator_multichain import VennattaFacilitator

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

settings = Settings()
settings.validate()

# Custom Vennatta multi-chain facilitator
facilitator = VennattaFacilitator(
    rpc_url=settings.rpc_url,
    supported_networks=[
        "eip155:8453",  # Base
        "solana:mainnet",  # Solana
    ],
    supported_schemes=["exact"],
)

# Create server with ONLY our facilitator (no separate scheme registration)
server = x402ResourceServer(facilitator)
server.register_extension(payment_identifier_resource_server_extension)

# Create FastAPI app
app = FastAPI(
    title="Vennatta Core API",
    description="Multi-chain x402 payment facilitator",
    version="2.0.0",
)
app.mount("/.well-known", StaticFiles(directory="app/static/.well-known"), name="well-known")

# Health check endpoint
@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "healthy"}

@app.get("/")
async def root() -> dict[str, str]:
    return {"status": "ok", "service": "vennatta-core", "chains": ["Base", "Solana"]}

# Define monetized routes
routes = {
    "POST /api/v1/extract-document": {
        "accepts": {
            "scheme": "exact",
            "network": "eip155:8453",
            "payTo": settings.pay_to,
            "price": "0.01 USDC",
        },
    },
    "POST /api/v1/extract-obsidian": {
        "accepts": {
            "scheme": "exact",
            "network": "eip155:8453",
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
