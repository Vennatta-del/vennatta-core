"""Payment utilities for x402 protocol."""

import base64
import json
import time
from typing import Any
from eth_account import Account
from eth_account.messages import encode_typed_data
from web3 import Web3


def create_payment_header(
    private_key: str,
    recipient: str,
    token: str,
    amount: int,
    api_url: str,
    network: str = "eip155:8453",
    scheme: str = "exact",
    chain_id: int = 8453,
) -> dict[str, str]:
    """Create x402 payment header for API requests.
    
    Args:
        private_key: Private key for signing
        recipient: Payment recipient address
        token: Token contract address
        amount: Payment amount in token's smallest units
        api_url: API endpoint URL
        network: Network identifier (default: eip155:8453 for Base)
        scheme: Payment scheme (default: exact)
        chain_id: Chain ID (default: 8453 for Base)
    
    Returns:
        Dict with Content-Type and PAYMENT-SIGNATURE headers
    """
    sender = Account.from_key(private_key).address
    w3 = Web3(Web3.HTTPProvider(f"https://mainnet.base.org"))
    
    # Create authorization
    nonce = w3.to_bytes(1)
    valid_after = int(time.time()) - 60
    valid_before = int(time.time()) + 3600
    
    authorization = {
        "from": sender,
        "to": recipient,
        "value": str(amount),
        "validAfter": str(valid_after),
        "validBefore": str(valid_before),
        "nonce": "0x" + nonce.hex(),
    }
    
    # Sign
    signable = encode_typed_data(
        domain_data={"name": "USD Coin", "version": "2", "chainId": chain_id, "verifyingContract": Web3.to_checksum_address(token)},
        message_types={"TransferWithAuthorization": [
            {"name": "from", "type": "address"},
            {"name": "to", "type": "address"},
            {"name": "value", "type": "uint256"},
            {"name": "validAfter", "type": "uint256"},
            {"name": "validBefore", "type": "uint256"},
            {"name": "nonce", "type": "bytes32"},
        ]},
        message_data={
            "from": Web3.to_checksum_address(sender),
            "to": Web3.to_checksum_address(recipient),
            "value": amount,
            "validAfter": valid_after,
            "validBefore": valid_before,
            "nonce": authorization["nonce"],
        },
    )
    
    signed = Account.sign_message(signable, private_key=private_key)
    signature = "0x" + signed.signature.hex()
    
    # Create payment payload
    payment_payload = {
        "x402Version": 2,
        "payload": {
            "authorization": authorization,
            "signature": signature,
        },
        "accepted": {
            "scheme": scheme,
            "network": network,
            "asset": token,
            "amount": str(amount),
            "payTo": recipient,
            "maxTimeoutSeconds": 300,
            "extra": {"name": "USD Coin", "version": "2"},
        },
        "resource": {
            "url": api_url,
            "description": "",
            "mimeType": "",
            "serviceName": "",
        },
    }
    
    # Encode as base64
    payment_json = json.dumps(payment_payload)
    payment_b64 = base64.b64encode(payment_json.encode()).decode()
    
    return {
        "Content-Type": "application/json",
        "PAYMENT-SIGNATURE": payment_b64,
    }


# Example usage:
if __name__ == "__main__":
    import requests
    
    PRIVATE_KEY = "0x789ccac2b6367c86a59f270426ab5861b656454ff01241b45f068d2d9ab1854e"
    RECIPIENT = "0xdadeFD58681C5C5df68681735752a40CaAE5E152"
    TOKEN = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
    API_URL = "https://vennatta-core.onrender.com/api/v1/extract-document"
    
    headers = create_payment_header(
        private_key=PRIVATE_KEY,
        recipient=RECIPIENT,
        token=TOKEN,
        amount=10000,
        api_url=API_URL,
    )
    
    response = requests.post(API_URL, headers=headers, json={"document": "test"})
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
