"""Test with debug output."""

import os, sys, time, json, httpx
from eth_account import Account
from eth_account.messages import encode_typed_data
from web3 import Web3

SENDER_PRIVATE_KEY = os.getenv("SENDER_PRIVATE_KEY")
RECEIVER_ADDRESS = "0xdadeFD58681C5C5df68681735752a40CaAE5E152"
USDC_ADDRESS = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
CHAIN_ID = 8453
AMOUNT = 10000
API_URL = "https://vennatta-core.onrender.com/api/v1/extract-document"

if not SENDER_PRIVATE_KEY:
    print("❌ SENDER_PRIVATE_KEY not set!")
    sys.exit(1)

w3 = Web3(Web3.HTTPProvider("https://mainnet.base.org"))
account = Account.from_key(SENDER_PRIVATE_KEY)

nonce = w3.to_hex(w3.keccak(text=f"{time.time()}-{os.urandom(8).hex()}"))
current_time = int(time.time())
valid_after = current_time - 60
valid_before = current_time + 300

full_message = {
    "types": {
        "EIP712Domain": [{"name": "name", "type": "string"}, {"name": "version", "type": "string"}, {"name": "chainId", "type": "uint256"}, {"name": "verifyingContract", "type": "address"}],
        "TransferWithAuthorization": [{"name": "from", "type": "address"}, {"name": "to", "type": "address"}, {"name": "value", "type": "uint256"}, {"name": "validAfter", "type": "uint256"}, {"name": "validBefore", "type": "uint256"}, {"name": "nonce", "type": "bytes32"}],
    },
    "primaryType": "TransferWithAuthorization",
    "domain": {"name": "USD Coin", "version": "2", "chainId": CHAIN_ID, "verifyingContract": Web3.to_checksum_address(RECEIVER_ADDRESS)},
    "message": {"from": Web3.to_checksum_address(account.address), "to": Web3.to_checksum_address(RECEIVER_ADDRESS), "value": AMOUNT, "validAfter": valid_after, "validBefore": valid_before, "nonce": nonce},
}

signable = encode_typed_data(full_message=full_message)
signed = Account.sign_message(signable, SENDER_PRIVATE_KEY)
signature_hex = signed.signature.hex()

payment_payload = {
    "x402Version": 2,
    "payload": {
        "authorization": {"from": account.address, "to": RECEIVER_ADDRESS, "value": str(AMOUNT), "validAfter": str(valid_after), "validBefore": str(valid_before), "nonce": nonce},
        "signature": "0x" + signature_hex,
    },
    "accepted": {"scheme": "exact", "network": "eip155:8453", "asset": USDC_ADDRESS, "amount": str(AMOUNT), "payTo": RECEIVER_ADDRESS, "maxTimeoutSeconds": 300, "extra": {"name": "USD Coin", "version": "2"}},
}

print("📦 Full payload:")
print(json.dumps(payment_payload, indent=2))

# Try without the document body first
print("\n=== Test 1: Empty body ===")
response = httpx.post(API_URL, json={}, headers={"Content-Type": "application/json", "X-Payment-Payload": json.dumps(payment_payload)}, timeout=120)
print(f"Status: {response.status_code}, Body: {response.text[:500]}")

# Try with document
print("\n=== Test 2: With document ===")
response = httpx.post(API_URL, json={"document": "Test"}, headers={"Content-Type": "application/json", "X-Payment-Payload": json.dumps(payment_payload)}, timeout=120)
print(f"Status: {response.status_code}, Body: {response.text[:500]}")
