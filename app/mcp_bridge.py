"""Private read-only MCP service. Run separately from the paid gateway."""
import hmac
import json
import os
from pathlib import Path

import httpx
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from .treasury_reads import ObservationError, configured_urls, register_treasury_tools

GATEWAY = "https://vennatta-core.onrender.com"
MAX_BODY = 131072
mcp = FastMCP(
    "Vennatta Private Bridge",
    stateless_http=True,
    json_response=True,
    transport_security=TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=[
            "vennatta-mcp-bridge.onrender.com",
            "vennatta-mcp-bridge.onrender.com:443",
            "127.0.0.1:*",
            "localhost:*",
        ],
        allowed_origins=[
            "https://vennatta-mcp-bridge.onrender.com",
            "https://www.perplexity.ai",
            "https://perplexity.ai",
        ],
    ),
)
register_treasury_tools(mcp)


async def gateway_read(path: str) -> dict:
    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=False) as client:
            async with client.stream("GET", GATEWAY + path) as response:
                if response.status_code != 200:
                    return {"status": "unavailable", "http_status": response.status_code}
                body = bytearray()
                async for chunk in response.aiter_bytes():
                    body.extend(chunk)
                    if len(body) > MAX_BODY:
                        return {"status": "unavailable", "reason": "response_too_large"}
                data = json.loads(body)
                if not isinstance(data, dict):
                    return {"status": "unavailable", "reason": "invalid_response"}
                return {"status": "observed", "source": GATEWAY + path, "data": data}
    except (httpx.HTTPError, ValueError):
        return {"status": "unavailable", "reason": "gateway_read_failed"}


@mcp.tool()
async def get_gateway_health() -> dict:
    """Observe gateway health now; does not establish settlement or worker health."""
    return await gateway_read("/health")


@mcp.tool()
async def get_seller_capabilities() -> dict:
    """Read gateway-reported capabilities; metadata is not a paid execution test."""
    return await gateway_read("/")


@mcp.tool()
def get_bridge_status() -> dict:
    """Report installed tools and configuration, not unobserved provider health."""
    try:
        configured_urls()
        rpc_configuration = "configured_not_live_verified"
    except ObservationError as exc:
        rpc_configuration = str(exc)
    except ValueError:
        rpc_configuration = "RPC_NOT_CONFIGURED"
    return {
        "version": "0.2.0",
        "mode": "read_only",
        "connected": ["gateway_health", "seller_capabilities"],
        "installed_adapters": ["base_treasury_snapshot", "base_usdc_payment_verification"],
        "treasury_rpc_configuration": rpc_configuration,
        "not_connected": ["authority_manifest", "vault", "opportunities",
                          "workers", "execution_receipts"],
        "can_sign": False,
        "can_trade": False,
        "can_submit_tasks": False,
    }


class ApiKeyGate:
    def __init__(self, wrapped, token: str):
        if len(token) < 32:
            raise RuntimeError("VENNATTA_MCP_API_KEY must contain at least 32 characters")
        self.wrapped = wrapped
        self.token = token.encode("utf-8")

    async def reject(self, send, status: int, error: str):
        body = json.dumps({"error": error}).encode()
        await send({"type": "http.response.start", "status": status,
                    "headers": [(b"content-type", b"application/json"),
                                (b"cache-control", b"no-store")]})
        await send({"type": "http.response.body", "body": body})

    async def __call__(self, scope, receive, send):
        if scope["type"] == "lifespan":
            return await self.wrapped(scope, receive, send)
        if scope["type"] != "http":
            await send({"type": "websocket.close", "code": 1008})
            return
        credentials = [v for k, v in scope.get("headers", [])
                       if k.lower() in (b"authorization", b"x-api-key")]
        if len(credentials) != 1:
            return await self.reject(send, 401, "unauthorized")
        credential = credentials[0]
        if credential.startswith(b"Bearer "):
            credential = credential[7:]
        if not hmac.compare_digest(credential, self.token):
            return await self.reject(send, 401, "unauthorized")
        body = bytearray()
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            body.extend(message.get("body", b""))
            if len(body) > MAX_BODY:
                return await self.reject(send, 413, "request_too_large")
            if not message.get("more_body", False):
                break
        delivered = False

        async def replay():
            nonlocal delivered
            if not delivered:
                delivered = True
                return {"type": "http.request", "body": bytes(body), "more_body": False}
            return await receive()

        return await self.wrapped(scope, replay, send)


def load_api_key() -> str:
    token = os.environ.get("VENNATTA_MCP_API_KEY", "")
    if token:
        return token
    try:
        return Path("/etc/secrets/VENNATTA_MCP_API_KEY").read_text(encoding="utf-8").rstrip("\r\n")
    except FileNotFoundError:
        return ""
    except (OSError, UnicodeError):
        raise RuntimeError("Unable to load MCP secret file") from None


def create_app():
    token = load_api_key()
    return ApiKeyGate(mcp.streamable_http_app(), token)
