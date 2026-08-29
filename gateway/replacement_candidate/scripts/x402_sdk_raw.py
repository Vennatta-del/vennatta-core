#!/usr/bin/env python3
"""
x402 facilitator - use SDK's internal HTTP client that already has auth working.
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

from cdp.openapi_client import X402FacilitatorApi, Configuration, ApiClient
from cdp.openapi_client.exceptions import ApiException

async def fetch_raw_with_sdk() -> Dict[str, Any]:
    """Fetch x402 resources using SDK's authenticated HTTP client, bypassing deserialization."""
    api_key_name = os.environ.get("CDP_API_KEY_NAME", "").strip()
    api_key_secret = os.environ.get("CDP_API_KEY_SECRET", "").strip()
    
    if not api_key_name or not api_key_secret:
        raise ValueError("CDP_API_KEY_NAME and CDP_API_KEY_SECRET required")
    
    # Create configuration  
    config = Configuration()
    config.api_key = {
        "apiKeyId": api_key_name,
        "apiSecret": api_key_secret,
    }
    config.host = "https://api.cdp.coinbase.com/platform"
    
    # Create API client
    api_client = ApiClient(configuration=config)
    
    # Make the HTTP request directly using the SDK's REST client with FULL URL
    response_data = await api_client.rest_client.request(
        method="GET",
        url="https://api.cdp.coinbase.com/platform/api/x402/v1/discovery/resources",
        headers={},
    )
    
    print(f"Status: {response_data.status}")
    print(f"Data type: {type(response_data.data)}")
    
    # Parse the response
    if response_data.data:
        response_text = response_data.data.decode('utf-8')
        return json.loads(response_text)
    else:
        raise Exception(f"No response data, status: {response_data.status}")

def main():
    api_key_name = os.environ.get("CDP_API_KEY_NAME", "").strip()
    api_key_secret = os.environ.get("CDP_API_KEY_SECRET", "").strip()
    
    if not api_key_name or not api_key_secret:
        print("Error: CDP_API_KEY_NAME and CDP_API_KEY_SECRET required", file=sys.stderr)
        return 1
    
    print(f"CDP API Key ID: {api_key_name}")
    print(f"CDP API Key Secret: ***redacted*** (length: {len(api_key_secret)})\n")
    
    try:
        print("Fetching x402 discovery resources (SDK raw HTTP)...")
        response = asyncio.run(fetch_raw_with_sdk())
        
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
