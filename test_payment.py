"""Test x402 payment - PRODUCTION READY."""

import base64
import json
import time
import requests
from eth_account import Account
from web3 import Web3
from eth_account.messages import encode_typed_data

# Configuration
RPC_URL = "https://mainnet.base.org"
PRIVATE_KEY = "0x789ccac2b6367c86a59f270426ab5861b656454ff01241b45f068d2d9ab1854e"
SENDER = Account.from_key(PRIVATE_KEY).address
RECIPIENT = "0xdadeFD58681C5C5df68681735752a40CaAE5E152"
TOKEN = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"  # USDC on Base
CHAIN_ID = 8453
API_URL = "https://vennatta-core.onrender.com/api/v1/extract-document"

print(f"✅ Sender: {SENDER}")

w3 = Web3(Web3.HTTPProvider(RPC_URL))

# Check balance
contract = w3.eth.contract(address=TOKEN, abi=[{"constant": True, "inputs": [{"name": "_owner", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "balance", "type": "uint256"}], "type": "function"}])
balance = contract.functions.balanceOf(SENDER).call()
print(f"✅ Balance: {balance}")

if balance < 10000:
    print("❌ Insufficient balance (need at least 10000)")
    exit(1)

# Create authorization
nonce = w3.to_bytes(1)
valid_after = int(time.time()) - 60
valid_before = int(time.time()) + 3600

authorization = {
    "from": SENDER,
    "to": RECIPIENT,
    "value": "10000",
    "validAfter": str(valid_after),
    "validBefore": str(valid_before),
    "nonce": "0x" + nonce.hex(),
}

# Sign
signable = encode_typed_data(
    domain_data={"name": "USD Coin", "version": "2", "chainId": CHAIN_ID, "verifyingContract": Web3.to_checksum_address(TOKEN)},
    message_types={"TransferWithAuthorization": [{"name": "from", "type": "address"}, {"name": "to", "type": "address"}, {"name": "value", "type": "uint256"}, {"name": "validAfter", "type": "uint256"}, {"name": "validBefore", "type": "uint256"}, {"name": "nonce", "type": "bytes32"}]},
    message_data={"from": Web3.to_checksum_address(SENDER), "to": Web3.to_checksum_address(RECIPIENT), "value": 10000, "validAfter": valid_after, "validBefore": valid_before, "nonce": authorization["nonce"]},
)

signed = Account.sign_message(signable, private_key=PRIVATE_KEY)
signature = "0x" + signed.signature.hex()

# Verify locally
recovered = Account.recover_message(signable, signature=signature)
print(f"✅ Local verification: {recovered.lower() == SENDER.lower()}")

# Create payment payload (x402 V2 format)
payment_payload = {
    "x402Version": 2,
    "payload": {
        "authorization": authorization,
        "signature": signature,
    },
    "accepted": {
        "scheme": "exact",
        "network": "eip155:8453",
        "asset": TOKEN,
        "amount": "10000",
        "payTo": RECIPIENT,
        "maxTimeoutSeconds": 300,
        "extra": {"name": "USD Coin", "version": "2"},
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

# Send with correct x402 header
headers = {
    "Content-Type": "application/json",
    "PAYMENT-SIGNATURE": payment_b64,
}

print(f"\n🚀 Sending to {API_URL}...")

response = requests.post(API_URL, headers=headers, json={"document": "test"})
print(f"\n📊 Status: {response.status_code}")
print(f"📊 Body: {response.text}")

if response.status_code == 200:
    print("\n✅✅✅ SUCCESS! PAYMENT WORKS! ✅✅✅")
    print(f"Response: {response.json()}")
elif response.status_code == 402:
    print("\n⚠️ 402 Payment Required")
    print(f"Response headers: {dict(response.headers)}")
else:
    print(f"\n❌ {response.status_code}")
