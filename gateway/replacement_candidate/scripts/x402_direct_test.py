#!/usr/bin/env python3
"""
Test x402 facilitator using the standalone x402 package.
"""
from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

# Import from the standalone x402 package
from x402.http import HTTPFacilitatorClient, FacilitatorConfig

async def main():
    api_key_name = os.environ.get("CDP_API_KEY_NAME", "").strip()
    api_key_secret = os.environ.get("CDP_API_KEY_SECRET", "").strip()
    
    if not api_key_name or not api_key_secret:
        print("Error: CDP_API_KEY_NAME and CDP_API_KEY_SECRET required", file=sys.stderr)
        return 1
    
    print(f"CDP API Key ID: {api_key_name}")
    print(f"CDP API Key Secret: ***redacted*** (length: {len(api_key_secret)})\n")
    
    try:
        # Create facilitator client
        config = FacilitatorConfig(
            base_url="https://api.cdp.coinbase.com/platform",
            api_key_id=api_key_name,
            api_key_secret=api_key_secret,
        )
        
        client = HTTPFacilitatorClient(config=config)
        
        print("Created x402 HTTPFacilitatorClient")
        print(f"Base URL: {config.base_url}")
        
        # Try to list discovery resources
        print("\nListing x402 discovery resources...")
        response = await client.list_x402_discovery_resources()
        
        print(f"\n✅ SUCCESS!")
        print(f"Response type: {type(response)}")
        print(f"Response: {response}")
        
        return 0
        
    except Exception as exc:
        import traceback
        print(f"\n❌ Error: {exc}")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
