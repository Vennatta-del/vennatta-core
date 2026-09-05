"""Test Solana x402 payment."""

import base64
import json
import requests
from solders.keypair import Keypair
from solders.message import Message
from solders.transaction import VersionedTransaction
import base58

# Configuration
SOLANA_RPC = "https://api.mainnet-beta.solana.com"
API_URL = "https://vennatta-core.onrender.com/api/v1/extract-document"

# Your Solana treasury
TREASURY = "FqkfjTzc1L1MRbynY7L1yxBjGFRNHBivokhzmsNzFpg5"

print(f"🌞 Testing Solana payment to Vennatta Core")
print(f"  Treasury: {TREASURY}")
print(f"  API: {API_URL}")

# Create a mock Solana payment payload
# In production, this would be a real signed transaction
payment_payload = {
    "x402Version": 2,
    "payload": {
        "authorization": {
            "payer": "TestPayer111111111111111111111111111111111",
            "signature_type": "solana",
        },
        "signature": "5j7s6NzpDvAnfC8DAzkYRxWjHzqmoCZ...mock...signature",
    },
    "accepted": {
        "scheme": "exact",
        "network": "solana:mainnet",
        "asset": "EPjFWWD5AufqPLqeM2RcR5K2oL9E8xN3xN3xN3xN3xN3",  # USDC
        "amount": "10000",
        "payTo": TREASURY,
        "maxTimeoutSeconds": 300,
    },
    "resource": {
        "url": API_URL,
        "description": "",
        "mimeType": "",
        "serviceName": "",
    },
}

# Encode as base64
payment_json = json.dumps(payment_payload)
payment_b64 = base64.b64encode(payment_json.encode()).decode()

print(f"\n📦 Payment payload created")
print(f"  Network: solana:mainnet")
print(f"  Asset: USDC")
print(f"  Amount: 10000")

# Send with PAYMENT-SIGNATURE header
headers = {
    "Content-Type": "application/json",
    "PAYMENT-SIGNATURE": payment_b64,
}

print(f"\n🚀 Sending to {API_URL}...")

response = requests.post(API_URL, headers=headers, json={"document": "solana test"})
print(f"\n📊 Status: {response.status_code}")
print(f"📊 Body: {response.text[:500]}")

if response.status_code == 200:
    print("\n🌞🌞🌞 SUCCESS! SOLANA PAYMENT WORKS! 🌞🌞🌞")
    print(f"Response: {response.json()}")
elif response.status_code == 402:
    print("\n⚠️ 402 Payment Required - verification failed")
    print(f"Response headers: {dict(response.headers)}")
else:
    print(f"\n❌ {response.status_code}")
