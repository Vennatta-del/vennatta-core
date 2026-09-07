"""Vennatta Core - Multi-chain x402 payment server."""

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
from x402.schemas import Network

from .config import Settings
from .facilitator_multichain import VennattaFacilitator

# Setup logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load settings
settings = Settings()
settings.validate()

# Create FastAPI app
app = FastAPI(title="Vennatta Core", description="Multi-chain x402 payment facilitator")

# Custom Vennatta facilitator with MULTI-CHAIN support
facilitator = VennattaFacilitator(
    rpc_url=settings.rpc_url,
    supported_networks=[
        Network(id="eip155:8453", name="Base"),  # Base (EVM)
        Network(id="solana:mainnet", name="Solana"),  # Solana
    ],
    supported_schemes=["exact"],
)

# Create server with our facilitator
server = x402ResourceServer(facilitator)

# Register the exact scheme for EVM (Base)
server.register(Network(id="eip155:8453", name="Base"), ExactEvmServerScheme())
server.register_extension(payment_identifier_resource_server_extension)

# Add payment middleware
app.add_middleware(PaymentMiddlewareASGI, server=server, resource_url="/api/v1/extract-document")


@app.get("/")
async def root() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok", "service": "vennatta-core", "chains": ["Base", "Solana"]}


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check for Render."""
    return {"status": "healthy"}


@app.post("/api/v1/extract-document")
async def extract_document() -> dict[str, str]:
    """Extract structured data from documents."""
    return {"status": "ok", "message": "Payment required for this resource"}


@app.post("/api/v1/extract-obsidian")
async def extract_obsidian() -> dict[str, str]:
    """Extract structured data from Obsidian vaults."""
    return {"status": "ok", "message": "Payment required for this resource"}


@app.post("/debug/verify")
async def debug_verify(payload: dict[str, Any]) -> dict[str, Any]:
    """Debug endpoint to test payment verification."""
    try:
        from x402.schemas import PaymentPayload, PaymentRequirements, ResourceInfo

        pp = PaymentPayload.model_validate(payload)
        requirements = PaymentRequirements(
            resource=ResourceInfo(url="https://vennatta-core.onrender.com/api/v1/extract-document", description="", mime_type=""),
            network=Network(id="eip155:8453", name="Base"),
            asset="0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
            amount="10000",
            pay_to="0xdadeFD58681C5C5df68681735752a40CaAE5E152",
            max_timeout_seconds=300,
        )
        result = await facilitator.verify(pp, requirements)
        return JSONResponse({"verify_result": result.model_dump()})
    except Exception as e:
        import traceback
        return JSONResponse({"error": str(e), "traceback": traceback.format_exc()}, status_code=500)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8081)
