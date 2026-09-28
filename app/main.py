"""Vennatta Core API protected by the official x402 middleware."""

from __future__ import annotations

import importlib.metadata
import logging
import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, HttpUrl
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
from .security_middleware import ContentSizeLimitMiddleware


class DocumentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_url: HttpUrl | None = None
    document_text: str | None = Field(
        default=None,
        max_length=2_000_000,
    )
    extraction_mode: str = Field(
        default="full",
        pattern="^(full|summary|metadata)$",
    )


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


def log_render_secret_file_metadata() -> None:
    secret_dir = Path("/etc/secrets")
    names = (
        "CDP_API_KEY_ID",
        "CDP_API_KEY_SECRET",
        "USDC_ADDRESS",
    )

    if not secret_dir.is_dir():
        logger.info(
            "Render secret directory: path=%s exists=False",
            secret_dir,
        )
        return

    metadata = {}
    for name in names:
        path = secret_dir / name
        metadata[name] = {
            "exists": path.is_file(),
            "size": path.stat().st_size if path.is_file() else 0,
        }

    logger.info("Render secret files: %s", metadata)


def load_individual_secret_files() -> None:
    secret_names = (
        "CDP_API_KEY_ID",
        "CDP_API_KEY_SECRET",
        "USDC_ADDRESS",
    )

    for name in secret_names:
        path = Path("/etc/secrets") / name
        if path.is_file():
            value = path.read_text(encoding="utf-8").strip()
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
settings = Settings()
settings.validate()

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
        description="Paid bounded document extraction for autonomous agents from public HTTP(S) documents or supplied text.",
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
    document: DocumentRequest,
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

app.add_middleware(
    ContentSizeLimitMiddleware,
    max_bytes=2_500_000,
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

