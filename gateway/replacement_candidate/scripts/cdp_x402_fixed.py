#!/usr/bin/env python3
"""
CDP x402 facilitator - patched to handle new response format.
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path

from cdp.openapi_client import X402FacilitatorApi, Configuration, ApiClient
from cdp.openapi_client.models.x402_discovery_resources_response import X402DiscoveryResourcesResponse

async def main():
    api_key_name = os.environ.get("CDP_API_KEY_NAME", "").strip()
    api_key_secret = os.environ.get("CDP_API_KEY_SECRET", "").strip()
    
    if not api_key_name or not api_key_secret:
        print("Error: CDP_API_KEY_NAME and CDP_API_KEY_SECRET required", file=sys.stderr)
        return 1
    
    print(f"CDP API Key ID: {api_key_name}")
    print(f"CDP API Key Secret: ***redacted*** (length: {len(api_key_secret)})\n")
    
    try:
        # Create configuration
        config = Configuration()
        config.api_key = {
            "apiKeyId": api_key_name,
            "apiSecret": api_key_secret,
        }
        
        # Create API client
        api_client = ApiClient(configuration=config)
        
        # Create x402 facilitator API
        x402_api = X402FacilitatorApi(api_client=api_client)
        
        # Try to list discovery resources
        print("Fetching x402 discovery resources...")
        response = await x402_api.list_x402_discovery_resources()
        
        print(f"✅ Success!")
        print(f"Response type: {type(response)}")
        print(f"Response: {response}")
        
        return 0
        
    except Exception as exc:
        # If it's a deserialization error, try to get the raw response
        if "No match found when deserializing" in str(exc):
            print(f"\n⚠️  SDK model mismatch (expected - new x402 format)")
            print(f"   The facilitator is working, just need to parse raw JSON")
            
            # Make raw HTTP call instead
            import httpx
            async with httpx.AsyncClient() as client:
                raw_response = await client.get(
                    f"{config.host}/api/x402/v1/discovery/resources",
                    headers={
                        "Authorization": f"Bearer {api_key_secret}",
                    },
                    timeout=10,
                )
            
            print(f"\nRaw response status: {raw_response.status_code}")
            print(f"Raw response: {raw_response.text[:1000]}")
            
        else:
            import traceback
            print(f"\n❌ Error: {exc}", file=sys.stderr)
            traceback.print_exc()
        
        return 1

if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
