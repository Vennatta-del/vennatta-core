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

# Simple test endpoint (no payment required yet)
@app.post("/api/v1/extract-document")
async def extract_document(request: Request, document: dict[str, Any]) -> JSONResponse:
    """Extract structured data from documents."""
    logger.info(f"Processing document: {document}")
    return JSONResponse({"status": "success", "data": {"extracted": "document data"}})

logger.info("✅ Vennatta production server started (no middleware)")
