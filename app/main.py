"""Vennatta Core API with x402 payment protection."""

from __future__ import annotations

from typing import Any
import logging
import traceback

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from x402 import x402ResourceServer
from x402.extensions.payment_identifier import (
    payment_identifier_resource_server_extension,
)
from x402.http.middleware.fastapi import PaymentMiddlewareASGI
from x402.mechanisms.evm.exact import ExactEvmServerScheme

from .config import Settings
from .facilitator_multichain import VennattaFacilitator

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

settings = Settings()
settings.validate()

# Custom Vennatta facilitator with real EVM validation
facilitator = VennattaFacilitator(
    rpc_url=settings.rpc_url,
    supported_networks=[settings.network],
    supported_schemes=["exact"],
)

# Create server with our facilitator
server = x402ResourceServer(facilitator)
# Register the exact scheme for parsing/metadata (NOT for verification)
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

@app.post("/debug/verify")
async def debug_verify(request: Request) -> JSONResponse:
    """Debug endpoint to test signature verification."""
    try:
        data = await request.json()
        authorization = data.get("authorization")
        signature = data.get("signature")
        
        if not authorization or not signature:
            return JSONResponse({"error": "Missing authorization or signature"}, status_code=400)
        
        from x402.schemas import PaymentPayload, PaymentRequirements, ResourceInfo
        
        requirements = PaymentRequirements(
            scheme="exact",
            network="eip155:8453",
            asset="0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
            amount="10000",
            payTo="0xdadeFD58681C5C5df68681735752a40CaAE5E152",
            maxTimeoutSeconds=300,
            extra={"name": "USD Coin", "version": "2"},
        )
        
        payload = PaymentPayload(
            payload={"authorization": authorization, "signature": signature},
            accepted=requirements,
            resource=ResourceInfo(url="https://vennatta-core.onrender.com/api/v1/extract-document"),
        )
        
        result = await facilitator.verify(payload, requirements)
        return JSONResponse({"verify_result": result.model_dump()})
    except Exception as e:
        import traceback
        return JSONResponse({"error": str(e), "traceback": traceback.format_exc()}, status_code=500)

# Add exception handler to see actual errors
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception: {exc}")
    logger.error(traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc), "traceback": traceback.format_exc()}
    )

# Add x402 payment middleware
try:
    app.add_middleware(
        PaymentMiddlewareASGI,
        server=server,
        routes=routes,
    )
    logger.info("✅ Middleware added successfully")
except Exception as e:
    logger.error(f"❌ Middleware setup failed: {e}")
    logger.error(traceback.format_exc())
    raise

logger.info("✅ Vennatta production server started with x402 middleware - ALL ROUTES LIVE")
