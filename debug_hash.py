"""Debug: show exact hash being signed."""

import os, time
from eth_account import Account
from eth_utils import keccak
from web3 import Web3

SENDER_PRIVATE_KEY = os.getenv("SENDER_PRIVATE_KEY")
RECEIVER_ADDRESS = "0xdadeFD58681C5C5df68681735752a40CaAE5E152"
USDC_ADDRESS = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
CHAIN_ID = 8453
AMOUNT = 10000

w3 = Web3(Web3.HTTPProvider("https://mainnet.base.org"))
account = Account.from_key(SENDER_PRIVATE_KEY)

nonce = w3.to_hex(w3.keccak(text=f"{time.time()}-{os.urandom(8).hex()}"))
current_time = int(time.time())
valid_after = current_time - 60
valid_before = current_time + 300

# Client-side hash
from eth_account.messages import encode_typed_data
full_message = {
    "types": {
        "EIP712Domain": [{"name": "name", "type": "string"}, {"name": "version", "type": "string"}, {"name": "chainId", "type": "uint256"}, {"name": "verifyingContract", "type": "address"}],
        "TransferWithAuthorization": [{"name": "from", "type": "address"}, {"name": "to", "type": "address"}, {"name": "value", "type": "uint256"}, {"name": "validAfter", "type": "uint256"}, {"name": "validBefore", "type": "uint256"}, {"name": "nonce", "type": "bytes32"}],
    },
    "primaryType": "TransferWithAuthorization",
    "domain": {"name": "USD Coin", "version": "2", "chainId": CHAIN_ID, "verifyingContract": Web3.to_checksum_address(USDC_ADDRESS)},
    "message": {"from": Web3.to_checksum_address(account.address), "to": Web3.to_checksum_address(RECEIVER_ADDRESS), "value": AMOUNT, "validAfter": valid_after, "validBefore": valid_before, "nonce": nonce},
}
client_signable = encode_typed_data(full_message=full_message)
print(f"📦 Client hash: {client_signable.body.hex()}")

# Server-side hash
DOMAIN_TYPE_HASH = keccak(text="EIP712Domain(string name,string version,uint256 chainId,address verifyingContract)")
domain_hash = keccak(w3.eth.codec.encode(["bytes32","bytes32","bytes32","uint256","address"], [DOMAIN_TYPE_HASH, keccak(text="USD Coin"), keccak(text="2"), CHAIN_ID, Web3.to_checksum_address(USDC_ADDRESS)]))

TYPE_HASH = keccak(text="TransferWithAuthorization(address from,address to,uint256 value,uint256 validAfter,uint256 validBefore,bytes32 nonce)")
message_hash = keccak(w3.eth.codec.encode(["bytes32","address","address","uint256","uint256","uint256","bytes32"], [TYPE_HASH, Web3.to_checksum_address(account.address), Web3.to_checksum_address(RECEIVER_ADDRESS), AMOUNT, valid_after, valid_before, w3.to_bytes(hexstr=nonce)]))

server_signable = keccak(w3.to_bytes(hexstr="0x1901") + domain_hash + message_hash)
print(f"📦 Server hash: {server_signable.hex()}")
print(f"\n✅ Match: {client_signable.body.hex() == server_signable.hex()}")
