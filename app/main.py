"""Vennatta Core API protected by the official x402 middleware."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.staticfiles import StaticFiles

from x402 import x402ResourceServer
from x402.extensions.payment_identifier import (
    payment_identifier_resource_server_extension,
)
from x402.http import HTTPFacilitatorClient, PaymentOption
from cdp.x402 import create_facilitator_config
from x402.http.middleware.fastapi import PaymentMiddlewareASGI
from x402.http.types import RouteConfig
from x402.mechanisms.evm.exact import ExactEvmServerScheme

from .config import Settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("vennatta")

settings = Settings()
settings.validate()

if settings.network != "eip155:8453":
    raise RuntimeError(
        f"First production path is Base mainnet only; got {settings.network}"
    )

facilitator = HTTPFacilitatorClient(
    create_facilitator_config()
)

server = x402ResourceServer(facilitator)
server.register(settings.network, ExactEvmServerScheme())
server.register_extension(payment_identifier_resource_server_extension)

class ExceptionLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except Exception:
            logger.exception(
                "Unhandled request error method=%s path=%s",
                request.method,
                request.url.path,
            )
            raise


app = FastAPI(
    title="Vennatta Core API",
    description="Paid document and knowledge-extraction API using x402.",
    version="2.0.0",
)

app.mount(
    "/.well-known",
    StaticFiles(directory="app/static/.well-known"),
    name="well-known",
)

routes: dict[str, RouteConfig] = {
    "POST /api/v1/extract-document": RouteConfig(
        accepts=[
            PaymentOption(
                scheme="exact",
                price="$0.01",
                network=settings.network,
                pay_to=settings.pay_to,
            )
        ],
        mime_type="application/json",
        description="Extract structured data from a document payload.",
    ),
    "POST /api/v1/extract-obsidian": RouteConfig(
        accepts=[
            PaymentOption(
                scheme="exact",
                price="$0.01",
                network=settings.network,
                pay_to=settings.pay_to,
            )
        ],
        mime_type="application/json",
        description="Extract structured data from an Obsidian vault payload.",
    ),
}

@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "healthy"}

@app.get("/")
async def root() -> dict[str, Any]:
    return {
        "status": "ok",
        "service": "vennatta-core",
        "chains": ["Base"],
        "payment_protocol": "x402",
    }

@app.post("/api/v1/extract-document")
async def extract_document(
    request: Request,
    document: dict[str, Any],
) -> JSONResponse:
    logger.info("Processing document request")
    return JSONResponse(
        {"status": "success", "data": {"extracted": "document data"}}
    )

@app.post("/api/v1/extract-obsidian")
async def extract_obsidian(
    request: Request,
    vault: dict[str, Any],
) -> JSONResponse:
    logger.info("Processing Obsidian request")
    return JSONResponse(
        {"status": "success", "data": {"extracted": "obsidian data"}}
    )

app.add_middleware(
    PaymentMiddlewareASGI,
    routes=routes,
    server=server,
)
