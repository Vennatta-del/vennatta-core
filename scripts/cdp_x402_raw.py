#!/usr/bin/env python3
"""
CDP x402 facilitator test - raw HTTP to bypass SDK deserialization issues.
"""
from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

import httpx

async def main():
    api_key_name = os.environ.get("CDP_API_KEY_NAME", "").strip()
    api_key_secret = os.environ.get("CDP_API_KEY_SECRET", "").strip()
    
    if not api_key_name or not api_key_secret:
        print("Error: CDP_API_KEY_NAME and CDP_API_KEY_SECRET required", file=sys.stderr)
        return 1
    
    print(f"CDP API Key ID: {api_key_name}")
    print(f"CDP API Key Secret: ***redacted*** (length: {len(api_key_secret)})")
    
    try:
        # Make direct HTTP request to CDP x402 facilitator
        print("\nMaking direct HTTP request to CDP x402 facilitator...")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.cdp.coinbase.com/api/x402/v1/discovery/resources",
                headers={
                    "Authorization": f"Bearer {api_key_secret}",
                },
                timeout=10,
            )
        
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:500]}")
        
        return 0
        
    except Exception as exc:
        import traceback
        print(f"\nError: {exc}", file=sys.stderr)
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
