#!/usr/bin/env python3
"""
x402 facilitator using CDP's authentication headers.
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import urlparse

import httpx
from cdp.auth.utils.http import GetAuthHeadersOptions, get_auth_headers

async def list_x402_resources() -> Dict[str, Any]:
    """List x402 discovery resources using CDP authentication."""
    api_key_name = os.environ.get("CDP_API_KEY_NAME", "").strip()
    api_key_secret = os.environ.get("CDP_API_KEY_SECRET", "").strip()
    
    if not api_key_name or not api_key_secret:
        raise ValueError("CDP_API_KEY_NAME and CDP_API_KEY_SECRET required")
    
    # Build the URL
    url = "https://api.cdp.coinbase.com/platform/api/x402/v1/discovery/resources"
    parsed_url = urlparse(url)
    
    # Get auth headers using CDP's function
    auth_headers = get_auth_headers(
        GetAuthHeadersOptions(
            api_key_id=api_key_name,
            api_key_secret=api_key_secret,
            request_method="GET",
            request_host=parsed_url.netloc,
            request_path=parsed_url.path,
            request_body=None,
            wallet_secret=None,
            source="cdp-sdk",
            source_version="1.0.0",
        )
    )
    
    print(f"Auth headers generated: {list(auth_headers.keys())}")
    
    # Make request with proper auth headers
    async with httpx.AsyncClient() as client:
        response = await client.get(
            url,
            headers=auth_headers,
            timeout=10,
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"HTTP {response.status_code}: {response.text}")

def main():
    api_key_name = os.environ.get("CDP_API_KEY_NAME", "").strip()
    api_key_secret = os.environ.get("CDP_API_KEY_SECRET", "").strip()
    
    if not api_key_name or not api_key_secret:
        print("Error: CDP_API_KEY_NAME and CDP_API_KEY_SECRET required", file=sys.stderr)
        return 1
    
    print(f"CDP API Key ID: {api_key_name}")
    print(f"CDP API Key Secret: ***redacted*** (length: {len(api_key_secret)})\n")
    
    try:
        print("Fetching x402 discovery resources with CDP auth...")
        response = asyncio.run(list_x402_resources())
        
        print(f"\n✅ SUCCESS!")
        print(f"\nResponse:")
        print(json.dumps(response, indent=2, default=str)[:2000])
        
        return 0
        
    except Exception as exc:
        import traceback
        print(f"\n❌ Error: {exc}")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
