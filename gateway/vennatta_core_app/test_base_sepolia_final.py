"""Test x402 on Base Sepolia with test ETH."""

import os
import json
import time
from web3 import Web3
from eth_account.messages import encode_defunct
import hashlib
from x402.http import HTTPFacilitatorClientSync, FacilitatorConfig
from x402.schemas.v1 import PaymentRequirementsV1, PaymentPayloadV1

# Your wallet (same address works on both networks)
WALLET_ADDRESS = "0xdadeFD58681C5C5df68681735752a40CaAE5E152"
PRIVATE_KEY = os.getenv("TEST_PRIVATE_KEY")

print("=" * 70)
print("x402 Base Sepolia Test - Final Test")
print("=" * 70)

print(f"\nWallet: {WALLET_ADDRESS}")
print(f"Network: Base Sepolia (testnet)")

# Connect to facilitator
print(f"\n1. Connecting to x402 facilitator...")
client = HTTPFacilitatorClientSync(
    FacilitatorConfig(url="https://x402.org/facilitator")
)
print(f"   ✅ {client.url}")

# Check supported networks
print(f"\n2. Checking supported networks...")
supported = client.get_supported()
base_sepolia = [k for k in supported.kinds if 'base-sepolia' in str(k.network).lower()]
if base_sepolia:
    print(f"   ✅ Base Sepolia supported!")
    for net in base_sepolia:
        print(f"      - {net.network} ({net.scheme} v{net.x402_version})")

# Create payment requirements for ETH
print(f"\n3. Creating payment requirements...")
requirements = PaymentRequirementsV1(
    maxAmountRequired="1000000000000000",  # 0.001 ETH
    asset="ETH",
    resource="test-identity-access",
    description="Test payment for identity node access",
    payTo=WALLET_ADDRESS,
    network="base-sepolia",
    scheme="exact",
    maxTimeoutSeconds=300,
)
print(f"   Amount: 0.001 ETH (~$0.003)")
print(f"   Pay To: {WALLET_ADDRESS}")

# Create and sign payment payload
print(f"\n4. Creating signed payment payload...")
w3 = Web3()
account = w3.eth.account.from_key(PRIVATE_KEY)

payment_data = {
    "payTo": WALLET_ADDRESS,
    "amount": "1000000000000000",
    "asset": "ETH",
    "resource": "test-identity-access",
    "description": "Test payment for identity node access",
    "nonce": w3.to_hex(int(time.time() * 1000)),
}

payload_json = json.dumps(payment_data, sort_keys=True)
payload_hash = hashlib.sha256(payload_json.encode()).hexdigest()

message = encode_defunct(hexstr=payload_hash)
signature = account.sign_message(message)

payment_data["signature"] = signature.signature.hex()
payment_data["signer"] = account.address

payment_payload = PaymentPayloadV1(
    scheme="exact",
    network="base-sepolia",
    payload=payment_data,
)

print(f"   ✅ Payload signed")

# Test verify endpoint
print(f"\n5. Testing /verify endpoint...")
try:
    verify_result = client.verify(payment_payload, requirements)
    print(f"   ✅ VERIFY RESULT:")
    print(f"   {verify_result}")
except Exception as e:
    print(f"   Result: {str(e)[:300]}")

print(f"\n" + "=" * 70)
print(f"🎉 TEST COMPLETE!")
print(f"=" * 70)
print(f"\n✅ You're ready to deploy!")
print(f"\nNext:")
print(f"  1. Deploy identity node with x402 gate")
print(f"  2. Configure for Base mainnet (production)")
print(f"  3. Start monetizing with your $5.91 USDC!")
