import os
import sys
import json
import requests
from x402_buyer_client import PolicyValidator, ProductionSigner, X402Buyer

RESOURCE = "https://agentcitadel.dev/api/v1/extract-document"
EXPECTED_NETWORK = "eip155:8453"
EXPECTED_ASSET = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
EXPECTED_AMOUNT = "10000"
EXPECTED_PAYTO = os.environ.get("EXPECTED_PAYTO", "0x80347776d27fA7f98e6E5703F4D2c7ffBB1977dc")
BUYER_ADDRESS = "0xdadeFD58681C5C5df68681735752a40CaAE5E152"
MAX_CALLS = int(os.environ.get("MAX_CALLS", "1"))
MAX_SPEND_ATOMIC = int(os.environ.get("MAX_SPEND_ATOMIC", "10000"))
LIVE_CONFIRM = os.environ.get("X402_LIVE_CONFIRM", "")

if LIVE_CONFIRM != "I_UNDERSTAND_ONE_REAL_PAYMENT":
    print("ERROR: X402_LIVE_CONFIRM environment variable not set to required safety string.")
    sys.exit(1)

if int(EXPECTED_AMOUNT) > MAX_SPEND_ATOMIC:
    print("ERROR: Amount exceeds MAX_SPEND_ATOMIC guardrail.")
    sys.exit(1)

# Retrieve private key securely from environment/secret loader
buyer_private_key = os.environ.get("BUYER_PRIVATE_KEY")
if not buyer_private_key:
    print("ERROR: BUYER_PRIVATE_KEY environment variable is not set.")
    sys.exit(1)

payload = {
    "document": (
        "Invoice Number: INV-CANARY-001\n"
        "Supplier: Example Ltd\n"
        "Total: 1250.00 USD"
    ),
    "fields": ["invoice_number", "supplier", "total", "currency"],
    "options": {
        "include_source_spans": True,
        "strict_schema": True,
    },
}

validator = PolicyValidator(
    expected_resource=RESOURCE,
    expected_network=EXPECTED_NETWORK,
    expected_asset=EXPECTED_ASSET,
    expected_amount=EXPECTED_AMOUNT,
    expected_payto=EXPECTED_PAYTO
)

signer = ProductionSigner(
    private_key=buyer_private_key,
    buyer_address=BUYER_ADDRESS
)

buyer = X402Buyer(policy=validator, signer=signer)

print("[*] Executing single-shot canary settlement call...")
result = buyer.call(RESOURCE, payload)

print(json.dumps({
    "status": result.get("status"),
    "request_id": result.get("request_id"),
    "result_hash": result.get("result_hash"),
}, indent=2))
