#!/usr/bin/env python3
"""
CDP x402 facilitator - use SDK's HTTP client directly to bypass model deserialization.
"""
from __future__ import annotations

import asyncio
import json
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
        
        # Use the SDK's REST client directly to make the call
        print("Making raw HTTP call using SDK's authenticated client...")
        
        response_data = await api_client.rest_client.request(
            method="GET",
            url=f"{config.host}/api/x402/v1/discovery/resources",
            headers={},
        )
        
        print(f"\n✅ Status: {response_data.status}")
        print(f"✅ Headers: {dict(response_data.headers)}")
        
        # Parse the JSON
        response_text = response_data.data.decode('utf-8')
        print(f"\n✅ Raw JSON response:")
        print(response_text[:2000])
        
        # Try to parse it
        try:
            data = json.loads(response_text)
            print(f"\n✅ Parsed successfully!")
            print(f"   Keys: {list(data.keys())}")
            if 'items' in data:
                print(f"   Items count: {len(data['items'])}")
                if data['items']:
                    print(f"   First item: {json.dumps(data['items'][0], indent=2)[:500]}")
        except json.JSONDecodeError as e:
            print(f"\n❌ JSON parse error: {e}")
        
        return 0
        
    except Exception as exc:
        import traceback
        print(f"\n❌ Error: {exc}", file=sys.stderr)
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
