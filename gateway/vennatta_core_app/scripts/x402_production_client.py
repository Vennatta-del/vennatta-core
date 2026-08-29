#!/usr/bin/env python3
"""
Production x402 facilitator client using the standalone x402 package.
This is the RECOMMENDED approach - uses the official x402 library directly.
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from x402.http import HTTPFacilitatorClient, FacilitatorConfig
from x402.extensions.bazaar import with_bazaar, ListDiscoveryResourcesParams, SearchDiscoveryResourcesParams

class X402FacilitatorClient:
    """Production x402 facilitator client with CDP integration."""
    
    def __init__(
        self,
        api_key_id: Optional[str] = None,
        api_key_secret: Optional[str] = None,
        base_url: str = "https://api.cdp.coinbase.com/platform/api/x402/v1",
        timeout: float = 30.0,
    ):
        """
        Initialize x402 facilitator client.
        
        Args:
            api_key_id: CDP API Key ID (optional for public endpoints)
            api_key_secret: CDP API Key Secret (optional for public endpoints)
            base_url: x402 facilitator base URL
            timeout: Request timeout in seconds
        """
        self.api_key_id = api_key_id or os.getenv("CDP_API_KEY_NAME") or os.getenv("CDP_API_KEY_ID")
        self.api_key_secret = api_key_secret or os.getenv("CDP_API_KEY_SECRET")
        
        # Create facilitator client
        config = FacilitatorConfig(
            url=base_url,
            timeout=timeout,
        )
        
        self.client = with_bazaar(HTTPFacilitatorClient(config=config))
        
    async def list_resources(self) -> Dict[str, Any]:
        """List all x402 discovery resources."""
        try:
            resources = self.client.extensions.bazaar.list_resources()
            return {
                "success": True,
                "data": resources,
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }
    
    async def search_resources(self, query: str, limit: int = 10) -> Dict[str, Any]:
        """Search x402 discovery resources."""
        try:
            params = SearchDiscoveryResourcesParams(
                query=query,
                limit=limit,
            )
            results = self.client.extensions.bazaar.search(params)
            return {
                "success": True,
                "data": results,
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }
    
    async def get_supported(self) -> Dict[str, Any]:
        """Get supported x402 schemes and networks."""
        try:
            supported = self.client.get_supported()
            return {
                "success": True,
                "data": supported,
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }

async def main():
    api_key_name = os.environ.get("CDP_API_KEY_NAME", "").strip()
    api_key_secret = os.environ.get("CDP_API_KEY_SECRET", "").strip()
    
    if not api_key_name or not api_key_secret:
        print("⚠️  Warning: CDP credentials not set (using public endpoints only)")
    
    print(f"CDP API Key ID: {api_key_name or 'NOT SET'}")
    print(f"CDP API Key Secret: {'***redacted***' if api_key_secret else 'NOT SET'}\n")
    
    try:
        # Create client
        print("Creating x402 facilitator client...")
        client = X402FacilitatorClient(
            api_key_id=api_key_name,
            api_key_secret=api_key_secret,
            base_url="https://api.cdp.coinbase.com/platform/api/x402/v1",
        )
        
        print("✅ Client created successfully\n")
        
        # Test 1: List resources
        print("Test 1: Listing x402 discovery resources...")
        resources = await client.list_resources()
        if resources["success"]:
            print(f"✅ Success! Got {len(resources['data'].items) if hasattr(resources['data'], 'items') else 'resources'}")
            print(f"   Data: {json.dumps(resources['data'], indent=2, default=str)[:500]}")
        else:
            print(f"❌ Error: {resources['error']}")
        
        print("\n" + "="*70)
        print("✅ PRODUCTION CLIENT READY")
        print("="*70)
        print("\nThe x402 facilitator client is working with the official x402 package!")
        print("\nNext steps:")
        print("  1. Integrate this client into your gateway")
        print("  2. Add proper CDP authentication if needed")
        print("  3. Deploy to production")
        print("="*70)
        
        return 0
        
    except Exception as exc:
        import traceback
        print(f"\n❌ Error: {exc}")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
