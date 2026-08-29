"""Test x402 /verify endpoint with signed payload."""

import os
import json
import time
from web3 import Web3
from eth_account.messages import encode_defunct
import hashlib
from x402.http import HTTPFacilitatorClientSync, FacilitatorConfig
from x402.schemas.v1 import PaymentRequirementsV1, PaymentPayloadV1

# Your wallet
WALLET_ADDRESS = "0xdadeFD58681C5C5df68681735752a40CaAE5E152"
PRIVATE_KEY = os.getenv("TEST_PRIVATE_KEY")

if not PRIVATE_KEY:
    print("❌ Set TEST_PRIVATE_KEY env var")
    exit(1)

print("=" * 70)
print("x402 /verify Endpoint Test")
print("=" * 70)

# Connect to facilitator
print(f"\n1. Connecting to facilitator...")
client = HTTPFacilitatorClientSync(
    FacilitatorConfig(url="https://x402.org/facilitator")
)
print(f"   ✅ {client.url}")

# Create Web3 account
w3 = Web3()
account = w3.eth.account.from_key(PRIVATE_KEY)

# Create payment requirements
print(f"\n2. Creating payment requirements...")
requirements = PaymentRequirementsV1(
    maxAmountRequired="1000",
    asset="USDC",
    resource="test-identity-access",
    description="Test payment for identity node access",
    payTo=WALLET_ADDRESS,
    network="base",
    scheme="exact",
    maxTimeoutSeconds=300,
)
print(f"   ✅ Amount: $0.001 USDC")

# Create and sign payment payload
print(f"\n3. Creating signed payment payload...")
payment_data = {
    "payTo": WALLET_ADDRESS,
    "amount": "1000",
    "asset": "USDC",
    "resource": "test-identity-access",
    "description": "Test payment for identity node access",
    "nonce": w3.to_hex(int(time.time() * 1000)),
}

payload_json = json.dumps(payment_data, sort_keys=True)
payload_hash = hashlib.sha256(payload_json.encode()).hexdigest()

message = encode_defunct(hexstr=payload_hash)
signature = account.sign_message(message)

# Add signature to payload
payment_data["signature"] = signature.signature.hex()
payment_data["signer"] = account.address

# Create payment payload object
payment_payload = PaymentPayloadV1(
    scheme="exact",
    network="base",
    payload=payment_data,
)

print(f"   ✅ Payload signed")
print(f"   Signer: {account.address}")

# Test verify endpoint
print(f"\n4. Testing /verify endpoint...")
try:
    verify_result = client.verify(payment_payload, requirements)
    print(f"   ✅ VERIFY SUCCESS!")
    print(f"   Valid: {verify_result.is_valid if hasattr(verify_result, 'is_valid') else 'unknown'}")
except Exception as e:
    print(f"   ⚠️  Verify result: {type(e).__name__}")
    print(f"   {str(e)[:200]}")

print(f"\n" + "=" * 70)
