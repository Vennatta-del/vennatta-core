from eth_account.messages import encode_typed_data
from web3 import Web3

RECEIVER_ADDRESS = "0xdadeFD58681C5C5df68681735752a40CaAE5E152"
CHAIN_ID = 8453
SENDER = "0xE7d7BdF214E23A8fD1ED22e476BF742862a70212"
nonce = "0x" + "aa" * 32
value = 10000
valid_after = 1788546001
valid_before = 1788546361

# Try full_message style
print("=== full_message style ===")
try:
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
            "from": Web3.to_checksum_address(SENDER),
            "to": Web3.to_checksum_address(RECEIVER_ADDRESS),
            "value": value,
            "validAfter": valid_after,
            "validBefore": valid_before,
            "nonce": nonce,
        },
    }
    signable = encode_typed_data(full_message=full_message)
    print(f"✅ Success! Hash: {signable.body.hex()}")
except Exception as e:
    print(f"❌ Error: {e}")
