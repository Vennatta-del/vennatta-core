"""Test CDP API connectivity."""

import requests
import hmac
import hashlib
import time

from app.cdp_config import CDP_API_KEY, CDP_API_SECRET

BASE_URL = "https://sandbox.cdp.coinbase.com"

print("=" * 70)
print("CDP API Ping Test")
print("=" * 70)

# Create signature for GET request
timestamp = str(int(time.time()))
message = timestamp + "GET" + "/api/v1/user"
signature = hmac.new(
    CDP_API_SECRET.encode(),
    message.encode(),
    hashlib.sha256
).hexdigest()

headers = {
    "X-CCD-Api-Key": CDP_API_KEY,
    "X-CCD-Timestamp": timestamp,
    "X-CCD-Signature": signature,
}

# Try different endpoints
endpoints = [
    "/api/v1/user",
    "/v1/user",
    "/api/v1/wallets",
    "/v1/wallets",
    "/",
]

print(f"\nTesting endpoints on {BASE_URL}:")
for endpoint in endpoints:
    try:
        response = requests.get(
            f"{BASE_URL}{endpoint}",
            headers=headers,
            timeout=5
        )
        print(f"  {endpoint:20s} → {response.status_code} {response.reason[:50] if response.reason else ''}")
    except Exception as e:
        print(f"  {endpoint:20s} → ERROR: {str(e)[:50]}")

print(f"\n" + "=" * 70)
