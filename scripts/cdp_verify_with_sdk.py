#!/usr/bin/env python3
"""
CDP sandbox verification using the official CDP SDK.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from cdp import CdpClient

def main():
    api_key_name = os.environ.get("CDP_API_KEY_NAME", "").strip()
    api_key_secret = os.environ.get("CDP_API_KEY_SECRET", "").strip()
    
    if not api_key_name or not api_key_secret:
        print("Error: CDP_API_KEY_NAME and CDP_API_KEY_SECRET required", file=sys.stderr)
        return 1
    
    print(f"CDP API Key ID: {api_key_name}")
    print(f"CDP API Key Secret: ***redacted*** (length: {len(api_key_secret)})")
    
    try:
        client = CdpClient(
            api_key_id=api_key_name,
            api_key_secret=api_key_secret,
        )
        
        print("\nCDP Client created successfully!")
        print("Available methods:", [m for m in dir(client) if not m.startswith("_")][:10])
        
        # Try x402 discovery if available
        if hasattr(client, "x402"):
            print("\nX402 support detected!")
        else:
            print("\nNo direct x402 attribute found on client")
        
        return 0
        
    except Exception as exc:
        print(f"\nError creating CDP client: {exc}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
