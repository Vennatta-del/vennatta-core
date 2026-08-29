#!/usr/bin/env python3
"""
CDP x402 facilitator test using the official CDP SDK.
"""
from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

from cdp.openapi_client import X402FacilitatorApi, Configuration, ApiClient

async def main():
    api_key_name = os.environ.get("CDP_API_KEY_NAME", "").strip()
    api_key_secret = os.environ.get("CDP_API_KEY_SECRET", "").strip()
    
    if not api_key_name or not api_key_secret:
        print("Error: CDP_API_KEY_NAME and CDP_API_KEY_SECRET required", file=sys.stderr)
        return 1
    
    print(f"CDP API Key ID: {api_key_name}")
    print(f"CDP API Key Secret: ***redacted*** (length: {len(api_key_secret)})")
    
    try:
        # Create configuration
        config = Configuration()
        config.api_key = {
            "apiKeyId": api_key_name,
            "apiSecret": api_key_secret,
        }
        
        print(f"\nConfiguration created")
        print(f"API Key settings: {config.api_key}")
        
        # Create API client
        api_client = ApiClient(configuration=config)
        print(f"API Client created")
        
        # Create x402 facilitator API
        x402_api = X402FacilitatorApi(api_client=api_client)
        print(f"X402FacilitatorApi created")
        
        # Try to list discovery resources
        print("\nTrying to list x402 discovery resources...")
        response = await x402_api.list_x402_discovery_resources()
        print(f"Success! Response type: {type(response)}")
        print(f"Response: {response}")
        
        return 0
        
    except Exception as exc:
        import traceback
        print(f"\nError: {exc}", file=sys.stderr)
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
