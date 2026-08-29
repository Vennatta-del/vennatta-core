#!/usr/bin/env python3
"""
x402 facilitator using CDP SDK's authentication + x402 package for parsing.
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

import httpx
from cdp import CdpClient

async def list_x402_resources() -> Dict[str, Any]:
    """List x402 discovery resources using CDP authentication."""
    api_key_name = os.environ.get("CDP_API_KEY_NAME", "").strip()
    api_key_secret = os.environ.get("CDP_API_KEY_SECRET", "").strip()
    
    if not api_key_name or not api_key_secret:
        raise ValueError("CDP_API_KEY_NAME and CDP_API_KEY_SECRET required")
    
    # Create CDP client to get authenticated session
    cdp_client = CdpClient(
        api_key_id=api_key_name,
        api_key_secret=api_key_secret,
    )
    
    # The CDP client handles HMAC authentication internally
    # We'll use its HTTP client to make the x402 request
    async with httpx.AsyncClient() as client:
        # Make request to x402 facilitator endpoint
        response = await client.get(
            "https://api.cdp.coinbase.com/platform/api/x402/v1/discovery/resources",
            headers={
                # CDP uses API key ID in the request
                "X-CDP-API-KEY-ID": api_key_name,
                # And signs the request with HMAC using the secret
                # For now, let's try with just the secret as bearer
                "Authorization": f"Bearer {api_key_secret}",
            },
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
        print("Fetching x402 discovery resources...")
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
