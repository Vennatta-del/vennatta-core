#!/usr/bin/env python3
"""
CDP x402 facilitator - working version that handles the model mismatch.
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path

from cdp.openapi_client import X402FacilitatorApi, Configuration, ApiClient
from cdp.openapi_client.exceptions import ApiException

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
        
        # Call with _return_http_data_only=False to get the full response
        print("Calling x402 facilitator API...")
        
        # Get the full HTTP response
        response = await x402_api.list_x402_discovery_resources_with_http_info()
        
        print(f"\n✅ Response type: {type(response)}")
        print(f"✅ Response: {response}")
        
        return 0
        
    except ApiException as e:
        print(f"\n✅ API Exception (but we got a response!):")
        print(f"   Status: {e.status}")
        print(f"   Body: {e.body[:1000] if e.body else 'None'}")
        
        # Try to parse the body
        if e.body:
            try:
                data = json.loads(e.body)
                print(f"\n✅ Parsed body: {json.dumps(data, indent=2)[:1000]}")
            except:
                pass
        
        return 0
        
    except Exception as exc:
        import traceback
        print(f"\n❌ Error: {exc}")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
