"""Vennatta Core API protected by the official x402 middleware."""

from __future__ import annotations

import importlib.metadata
import logging
import os
from pathlib import Path
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


def load_secret_file(path: str = "/etc/secrets/vennatta-production.env") -> None:
    secret_path = Path(path)
    if not secret_path.is_file():
        return

    for raw_line in secret_path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")

        if key and value and not os.getenv(key):
            os.environ[key] = value


def load_individual_secret_files() -> None:
    secret_names = (
        "CDP_API_KEY_ID",
        "CDP_API_KEY_SECRET",
        "USDC_ADDRESS",
    )

    for name in secret_names:
        path = Path("/etc/secrets") / name
        if path.is_file() and not os.getenv(name):
            value = path.read_text().strip()
            if value:
                os.environ[name] = value


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    force=True,
)
logging.getLogger("x402").setLevel(logging.INFO)
logging.getLogger("x402.http").setLevel(logging.INFO)
logger = logging.getLogger("vennatta")

load_secret_file()
load_individual_secret_files()
logger.info(
    "CDP runtime: id_loaded=%s secret_loaded=%s id_length=%s secret_length=%s",
    bool(os.getenv("CDP_API_KEY_ID")),
    bool(os.getenv("CDP_API_KEY_SECRET")),
    len(os.getenv("CDP_API_KEY_ID", "")),
    len(os.getenv("CDP_API_KEY_SECRET", "")),
)

settings = Settings()
settings.validate()

logger.info(
    "runtime diagnostics: python=%s x402=%s cdp_sdk=%s "
    "key_loaded=%s secret_loaded=%s secret_file=%s",
    __import__("sys").version.split()[0],
    importlib.metadata.version("x402"),
    importlib.metadata.version("cdp-sdk"),
    bool(os.getenv("CDP_API_KEY_ID")),
    bool(os.getenv("CDP_API_KEY_SECRET")),
    Path("/etc/secrets/vennatta-production.env").is_file(),
)

if settings.network != "eip155:8453":
    raise RuntimeError(
        f"First production path is Base mainnet only; got {settings.network}"
    )

cdp_api_key_id = os.getenv("CDP_API_KEY_ID")
cdp_api_key_secret = os.getenv("CDP_API_KEY_SECRET")

if not cdp_api_key_id or not cdp_api_key_secret:
    raise RuntimeError(
        "CDP_API_KEY_ID and CDP_API_KEY_SECRET are required for production"
    )

facilitator = HTTPFacilitatorClient(
    create_facilitator_config(
        api_key_id=cdp_api_key_id,
        api_key_secret=cdp_api_key_secret,
    )
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

class OuterExceptionLogger:
    def __init__(self, wrapped):
        self.wrapped = wrapped

    async def __call__(self, scope, receive, send):
        try:
            await self.wrapped(scope, receive, send)
        except Exception:
            logger.exception(
                "OUTER ASGI FAILURE method=%s path=%s",
                scope.get("method"),
                scope.get("path"),
            )
            raise


app = OuterExceptionLogger(app)

