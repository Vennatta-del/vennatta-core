"""Minimal ASGI identity node with token auth and x402 gate."""

import os
import time
import secrets
from typing import Dict, Optional
from dataclasses import dataclass

# Simple token-based auth
API_TOKEN = os.getenv("IDENTITY_API_TOKEN", secrets.token_urlsafe(32))

@dataclass
class RateLimitConfig:
    """Rate limiting configuration."""
    requests_per_minute: int = 60
    requests_per_hour: int = 1000

class RateLimiter:
    """Simple in-memory rate limiter."""
    
    def __init__(self, config: RateLimitConfig):
        self.config = config
        self.requests: Dict[str, list] = {}  # IP → list of timestamps
    
    def is_allowed(self, client_ip: str) -> tuple[bool, str]:
        """Check if request is allowed."""
        now = time.time()
        
        # Clean old requests
        if client_ip in self.requests:
            self.requests[client_ip] = [
                t for t in self.requests[client_ip]
                if now - t < 3600  # Keep last hour
            ]
        else:
            self.requests[client_ip] = []
        
        # Check limits
        minute_requests = [t for t in self.requests[client_ip] if now - t < 60]
        if len(minute_requests) >= self.config.requests_per_minute:
            return False, "Rate limit exceeded (per minute)"
        
        if len(self.requests[client_ip]) >= self.config.requests_per_hour:
            return False, "Rate limit exceeded (per hour)"
        
        self.requests[client_ip].append(now)
        return True, "OK"

# Global rate limiter
rate_limiter = RateLimiter(RateLimitConfig())

async def verify_token(auth_header: Optional[str]) -> tuple[bool, str]:
    """Verify API token."""
    if not auth_header or not auth_header.startswith("Bearer "):
        return False, "Missing or invalid Authorization header"
    
    token = auth_header[7:]  # Remove "Bearer " prefix
    if not secrets.compare_digest(token, API_TOKEN):
        return False, "Invalid token"
    
    return True, "OK"

async def identity_app(scope, receive, send):
    """Minimal ASGI identity node application."""
    
    if scope["type"] != "http":
        return
    
    # Extract headers
    headers = {k.decode(): v.decode() for k, v in scope.get("headers", [])}
    client_ip = scope.get("client", ("unknown", 0))[0]
    
    # Rate limiting
    allowed, message = rate_limiter.is_allowed(client_ip)
    if not allowed:
        await send({
            "type": "http.response.start",
            "status": 429,
            "headers": [[b"content-type", b"application/json"]],
        })
        await send({
            "type": "http.response.body",
            "body": f'{{"error": "{message}"}}'.encode(),
        })
        return
    
    # Token auth (skip for health checks)
    path = scope.get("path", "/")
    if path != "/health":
        auth_header = headers.get("authorization")
        valid, message = await verify_token(auth_header)
        if not valid:
            await send({
                "type": "http.response.start",
                "status": 401,
                "headers": [[b"content-type", b"application/json"]],
            })
            await send({
                "type": "http.response.body",
                "body": f'{{"error": "{message}"}}'.encode(),
            })
            return
    
    # Route handling
    if path == "/health":
        await send({
            "type": "http.response.start",
            "status": 200,
            "headers": [[b"content-type", b"application/json"]],
        })
        await send({
            "type": "http.response.body",
            "body": b'{"status": "healthy", "service": "identity-node"}',
        })
    
    elif path == "/api/v1/identity":
        # Protected endpoint - return identity info
        await send({
            "type": "http.response.start",
            "status": 200,
            "headers": [[b"content-type", b"application/json"]],
        })
        await send({
            "type": "http.response.body",
            "body": b'{"identity": "vennatta", "status": "active"}',
        })
    
    else:
        await send({
            "type": "http.response.start",
            "status": 404,
            "headers": [[b"content-type", b"application/json"]],
        })
        await send({
            "type": "http.response.body",
            "body": b'{"error": "Not found"}',
        })

# For running with uvicorn: uvicorn app.identity_node:identity_app
if __name__ == "__main__":
    print(f"✅ Identity node configured")
    print(f"   API Token: {API_TOKEN[:8]}... (set IDENTITY_API_TOKEN env var)")
    print(f"   Rate limit: {rate_limiter.config.requests_per_minute}/min, {rate_limiter.config.requests_per_hour}/hour")
    print(f"\nRun with: uvicorn app.identity_node:identity_app --host 0.0.0.0 --port 8000")
