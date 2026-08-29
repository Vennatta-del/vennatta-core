"""Test full x402 verify → settle flow on Base mainnet with USDC."""

import os
import json
from web3 import Web3
from x402.http import HTTPFacilitatorClientSync, FacilitatorConfig
from x402.schemas.v1 import PaymentRequirementsV1, PaymentPayloadV1

# Your wallet
WALLET_ADDRESS = "0xdadeFD58681C5C5df68681735752a40CaAE5E152"
NETWORK = "base"
CHAIN_ID = 8453
USDC_ADDRESS = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"

print("=" * 70)
print("x402 Full Flow Test: Verify → Settle")
print("=" * 70)

# Connect to facilitator
print(f"\n1. Connecting to x402 facilitator...")
client = HTTPFacilitatorClientSync(
    FacilitatorConfig(url="https://x402.org/facilitator")
)
print(f"   ✅ Connected: {client.url}")

# Get private key
private_key = os.getenv("TEST_PRIVATE_KEY")
if not private_key:
    print(f"\n❌ Set TEST_PRIVATE_KEY env var")
    print(f"   export TEST_PRIVATE_KEY='your_key'")
    exit(1)

# Connect to Web3
w3 = Web3(Web3.HTTPProvider("https://mainnet.base.org"))
account = w3.eth.account.from_key(private_key)

print(f"\n2. Wallet: {account.address}")
print(f"   Network: Base mainnet (Chain ID: {w3.eth.chain_id})")

# Check USDC balance
usdc_contract = w3.eth.contract(
    address=USDC_ADDRESS,
    abi=[{"constant": True, "inputs": [{"name": "_owner", "type": "address"}],
          "name": "balanceOf", "outputs": [{"name": "balance", "type": "uint256"}],
          "type": "function"}]
)
balance = usdc_contract.functions.balanceOf(account.address).call()
balance_usdc = balance / 1e6
print(f"   💰 USDC Balance: ${balance_usdc:.2f}")

# Create payment requirements
print(f"\n3. Creating payment requirements...")
requirements = PaymentRequirementsV1(
    maxAmountRequired="1000",  # $0.001 USDC
    asset="USDC",
    resource="test-identity-access",
    description="Test payment for identity node access",
    payTo=WALLET_ADDRESS,
    network=NETWORK,
    scheme="exact",
    maxTimeoutSeconds=300,
)
print(f"   ✅ Amount: $0.001 USDC")
print(f"   ✅ Pay To: {WALLET_ADDRESS}")

# TODO: Create and sign payment payload
print(f"\n4. Creating signed payment payload...")
print(f"   (This requires signing the payment hash)")

# TODO: Test verify endpoint
print(f"\n5. Testing /verify endpoint...")
print(f"   (Send signed payload to facilitator)")

# TODO: Test settle endpoint
print(f"\n6. Testing /settle endpoint...")
print(f"   (Execute the payment)")

print(f"\n" + "=" * 70)
print(f"🔥 NEXT: Implement payment signing and test verify/settle")
print(f"=" * 70)
