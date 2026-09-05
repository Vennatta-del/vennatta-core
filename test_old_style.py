"""Try old eth-account < 0.12 style."""

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

# Old style: full_message with types including EIP712Domain
full_message = {
    "types": {
        "EIP712Domain": [
            {"name": "name", "type": "string"},
            {"name": "version", "type": "string"},
            {"name": "chainId", "type": "uint256"},
            {"name": "verifyingContract", "type": "address"},
        ],
        "TransferWithAuthorization": [
            {"name": "from", "type": "address"},
            {"name": "to", "type": "address"},
            {"name": "value", "type": "uint256"},
            {"name": "validAfter", "type": "uint256"},
            {"name": "validBefore", "type": "uint256"},
            {"name": "nonce", "type": "bytes32"},
        ],
    },
    "primaryType": "TransferWithAuthorization",
    "domain": {
        "name": "USD Coin",
        "version": "2",
        "chainId": CHAIN_ID,
        "verifyingContract": Web3.to_checksum_address(RECEIVER_ADDRESS),
    },
    "message": {
        "from": Web3.to_checksum_address(account.address),
        "to": Web3.to_checksum_address(RECEIVER_ADDRESS),
        "value": AMOUNT,
        "validAfter": valid_after,
        "validBefore": valid_before,
        "nonce": nonce,
    },
}

print("=== Old Metamask style (full_message with types) ===")
try:
    encoded = encode_typed_data(full_message=full_message)
    print(f"✅ Hash: {encoded.body.hex()}")
    
    signed = Account.sign_message(encoded, SENDER_PRIVATE_KEY)
    recovered = Account.recover_message(encoded, signature=signed.signature)
    print(f"✅ Recovered: {recovered}")
    print(f"✅ Match: {recovered.lower() == account.address.lower()}")
except Exception as e:
    print(f"❌ Error: {e}")
