from __future__ import annotations

import asyncio
import base64
import json
import os

from eth_account import Account
from x402.client import x402Client
from x402.http import PAYMENT_REQUIRED_HEADER, PAYMENT_RESPONSE_HEADER
from x402.http.clients.httpx import x402HttpxClient
from x402.mechanisms.evm.exact import ExactEvmScheme


ENDPOINT = "http://127.0.0.1:8000/api/v1/extract-document"
EXPECTED_NETWORK = "eip155:8453"
EXPECTED_ASSET = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
EXPECTED_AMOUNT = "10000"
EXPECTED_PAY_TO = "0x98807Ecce0D4F555d0447F79E7BdD9AA2aF0b767"
EXPECTED_PAYER = "0x16864a8d99A66F3e9D3230FB9256753E7Fa640B4"


def decode_header(value: str) -> dict:
    raw = base64.b64decode(value + "=" * (-len(value) % 4))
    return json.loads(raw)


async def main() -> None:
    key = os.getenv("VENNATTA_AGENT_PRIVATE_KEY")
    if not key:
        raise SystemExit("VENNATTA_AGENT_PRIVATE_KEY is not loaded")

    account = Account.from_key(key)
    print("payer:", account.address)

    if account.address.lower() != EXPECTED_PAYER.lower():
        raise SystemExit("Payer address mismatch")

    client = x402Client()
    client.register(EXPECTED_NETWORK, ExactEvmScheme(account))

    async with x402HttpxClient(client) as http:
        response = await http.post(
            ENDPOINT,
            json={"test": "first real x402 payment"},
        )

        print("payment HTTP status:", response.status_code)
        print("response:", response.text[:500])

        payment_response = response.headers.get(PAYMENT_RESPONSE_HEADER)
        print("payment response received:", "yes" if payment_response else "no")

        if response.status_code != 200:
            raise SystemExit("Payment request did not succeed")


if __name__ == "__main__":
    asyncio.run(main())
