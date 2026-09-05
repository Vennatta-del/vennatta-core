"""Debug: print the exact hash being signed."""

import os, time
from eth_account import Account
from eth_account.messages import encode_typed_data
from web3 import Web3

SENDER_PRIVATE_KEY = os.getenv("SENDER_PRIVATE_KEY")
RECEIVER_ADDRESS = "0xdadeFD58681C5C5df68681735752a40CaAE5E152"
CHAIN_ID = 8453
AMOUNT = 10000

account = Account.from_key(SENDER_PRIVATE_KEY)
nonce = Web3.to_hex(Web3.keccak(text=f"{time.time()}-{os.urandom(8).hex()}"))
current_time = int(time.time())
valid_after = current_time - 60
valid_before = current_time + 300

domain_data = {
    "name": "USD Coin",
    "version": "2",
    "chainId": CHAIN_ID,
    "verifyingContract": Web3.to_checksum_address(RECEIVER_ADDRESS),
}

message_types = {
    "TransferWithAuthorization": [
        {"name": "from", "type": "address"},
        {"name": "to", "type": "address"},
        {"name": "value", "type": "uint256"},
        {"name": "validAfter", "type": "uint256"},
        {"name": "validBefore", "type": "uint256"},
        {"name": "nonce", "type": "bytes32"},
    ],
}

message_data = {
    "from": Web3.to_checksum_address(account.address),
    "to": Web3.to_checksum_address(RECEIVER_ADDRESS),
    "value": AMOUNT,
    "validAfter": valid_after,
    "validBefore": valid_before,
    "nonce": nonce,
}

signable = encode_typed_data(
    domain_data=domain_data,
    message_types=message_types,
    message_data=message_data,
)

print(f"📦 Domain: {domain_data}")
print(f"📦 Message: {message_data}")
print(f"\n🔐 Signable hash: {signable.body.hex()}")

signed = Account.sign_message(signable, SENDER_PRIVATE_KEY)
print(f"\n✍️ Signature: 0x{signed.signature.hex()}")

# Verify recovery
recovered = Account.recover_message(signable, signature=signed.signature)
print(f"\n✅ Recovered: {recovered}")
print(f"✅ Expected:  {account.address}")
print(f"✅ Match: {recovered.lower() == account.address.lower()}")
