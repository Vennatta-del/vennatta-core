"""Sign x402 payment payload."""

import os
import time
from web3 import Web3
from eth_account.messages import encode_defunct
import hashlib
import json

# Your wallet
WALLET_ADDRESS = "0xdadeFD58681C5C5df68681735752a40CaAE5E152"
PRIVATE_KEY = os.getenv("TEST_PRIVATE_KEY")

if not PRIVATE_KEY:
    print("❌ Set TEST_PRIVATE_KEY env var")
    exit(1)

w3 = Web3()
account = w3.eth.account.from_key(PRIVATE_KEY)

print("=" * 70)
print("Signing x402 Payment Payload")
print("=" * 70)

# Create payment payload (what we need to sign)
payment_data = {
    "version": 1,
    "scheme": "exact",
    "network": "base",
    "payTo": WALLET_ADDRESS,
    "amount": "1000",  # $0.001 USDC
    "asset": "USDC",
    "resource": "test-identity-access",
    "description": "Test payment for identity node access",
    "nonce": w3.to_hex(int(time.time() * 1000)),  # Timestamp-based nonce
}

print(f"\nPayment Data:")
for k, v in payment_data.items():
    print(f"  {k}: {v}")

# Create hash to sign
payload_json = json.dumps(payment_data, sort_keys=True)
payload_hash = hashlib.sha256(payload_json.encode()).hexdigest()

print(f"\nPayload Hash: {payload_hash}")

# Sign the hash
message = encode_defunct(hexstr=payload_hash)
signature = account.sign_message(message)

print(f"\n✅ Signature created:")
print(f"   r: {signature.r}")
print(f"   s: {signature.s}")
print(f"   v: {signature.v}")

# Full signature (hex)
full_sig = signature.signature.hex()
print(f"\nFull Signature: {full_sig[:64]}...")

# Create complete payment payload
complete_payload = {
    **payment_data,
    "signature": full_sig,
    "signer": account.address,
}

print(f"\n✅ Complete Payment Payload:")
print(json.dumps(complete_payload, indent=2))

print(f"\n" + "=" * 70)
print(f"Next: Send this to facilitator /verify endpoint")
print(f"=" * 70)
