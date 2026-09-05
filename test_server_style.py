"""Try to match server's exact encode_typed_data call."""

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

domain = {
    "name": "USD Coin",
    "version": "2",
    "chainId": CHAIN_ID,
    "verifyingContract": Web3.to_checksum_address(RECEIVER_ADDRESS),
}

message = {
    "from": Web3.to_checksum_address(account.address),
    "to": Web3.to_checksum_address(RECEIVER_ADDRESS),
    "value": AMOUNT,
    "validAfter": valid_after,
    "validBefore": valid_before,
    "nonce": nonce,
}

# Server's exact call (will fail locally but let's see the error)
print("=== Trying server's exact style ===")
try:
    encoded = encode_typed_data(
        domain_types={
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
        domain_data=domain,
        message_types={
            "TransferWithAuthorization": [
                {"name": "from", "type": "address"},
                {"name": "to", "type": "address"},
                {"name": "value", "type": "uint256"},
                {"name": "validAfter", "type": "uint256"},
                {"name": "validBefore", "type": "uint256"},
                {"name": "nonce", "type": "bytes32"},
            ],
        },
        domain=domain,
        message=message,
    )
    print(f"✅ Worked! Hash: {encoded.body.hex()}")
except TypeError as e:
    print(f"❌ TypeError: {e}")
    print("\nServer must be running older eth-account version")
    
# Let's also check what eth-account versions support domain_types
print("\n=== Checking eth_account version ===")
import eth_account
print(f"Local version: {eth_account.__version__}")
