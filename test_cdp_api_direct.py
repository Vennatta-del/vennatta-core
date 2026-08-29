"""Test CDP API directly to create Base Sepolia wallet."""

import os
import requests
import hmac
import hashlib
import time
import json

from app.cdp_config import CDP_API_KEY, CDP_API_SECRET

print("=" * 70)
print("CDP API Direct Test")
print("=" * 70)

print(f"\nAPI Key: {CDP_API_KEY[:8]}...")

# CDP API base URL (CORRECTED)
BASE_URL = "https://sandbox.cdp.coinbase.com"
print(f"API URL: {BASE_URL}")

# Create signature
def create_signature(method, path, body=""):
    timestamp = str(int(time.time()))
    message = timestamp + method + path + (body if body else "")
    signature = hmac.new(
        CDP_API_SECRET.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()
    return signature, timestamp

# Test: Create wallet
print(f"\n1. Creating wallet on Base Sepolia...")

path = "/api/v1/wallets"
method = "POST"
body = json.dumps({"network_id": "base-sepolia"})

signature, timestamp = create_signature(method, path, body)

headers = {
    "Content-Type": "application/json",
    "X-CCD-Api-Key": CDP_API_KEY,
    "X-CCD-Timestamp": timestamp,
    "X-CCD-Signature": signature,
}

try:
    response = requests.post(
        f"{BASE_URL}{path}",
        headers=headers,
        data=body,
        timeout=10
    )
    
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Wallet created!")
        print(f"   ID: {data.get('wallet_id', 'unknown')}")
        print(f"   Network: {data.get('network_id', 'unknown')}")
    else:
        print(f"   Response: {response.text[:300]}")
        
except Exception as e:
    print(f"   ❌ Error: {e}")

print(f"\n" + "=" * 70)
