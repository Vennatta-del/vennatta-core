"""Test x402 on Base mainnet with real USDC."""

import os
from web3 import Web3
from x402.http import HTTPFacilitatorClientSync, FacilitatorConfig
from x402.schemas.v1 import PaymentRequirementsV1

# Your wallet on Base mainnet
WALLET_ADDRESS = "0xdadeFD58681C5C5df68681735752a40CaAE5E152"
NETWORK = "base"  # Base mainnet
CHAIN_ID = 8453
USDC_ADDRESS = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"  # USDC on Base

print("=" * 70)
print("x402 Base Mainnet USDC Test")
print("=" * 70)

print(f"\nWallet: {WALLET_ADDRESS}")
print(f"Network: Base Mainnet (Chain ID: {CHAIN_ID})")
print(f"USDC: {USDC_ADDRESS}")

# Connect to Web3
w3 = Web3(Web3.HTTPProvider("https://mainnet.base.org"))
print(f"\n✅ Connected to Base mainnet")
print(f"   Chain ID: {w3.eth.chain_id}")

# Get private key
private_key = os.getenv("TEST_PRIVATE_KEY")

if not private_key:
    print("\n⚠️  Set TEST_PRIVATE_KEY env var to continue")
    print("export TEST_PRIVATE_KEY='your_key'")
else:
    try:
        account = w3.eth.account.from_key(private_key)
        print(f"✅ Account: {account.address}")
        
        # Check USDC balance
        print(f"\nChecking USDC balance...")
        
        # USDC contract ABI (minimal for balanceOf)
        usdc_contract = w3.eth.contract(
            address=USDC_ADDRESS,
            abi=[{
                "constant": True,
                "inputs": [{"name": "_owner", "type": "address"}],
                "name": "balanceOf",
                "outputs": [{"name": "balance", "type": "uint256"}],
                "type": "function"
            }]
        )
        
        balance = usdc_contract.functions.balanceOf(account.address).call()
        balance_usdc = balance / 1e6  # USDC has 6 decimals
        
        print(f"💰 USDC Balance: ${balance_usdc:.2f}")
        
        if balance_usdc > 0:
            print(f"   🎉 Ready to cook with real USDC!")
            
            # Create payment requirements for $0.001 USDC
            print(f"\nCreating payment requirements...")
            requirements = PaymentRequirementsV1(
                maxAmountRequired="1000",  # $0.001 USDC (6 decimals)
                asset="USDC",
                resource="test-identity-access",
                description="Test payment for identity node access",
                payTo=WALLET_ADDRESS,
                network=NETWORK,
                scheme="exact",
                maxTimeoutSeconds=300,
            )
            
            print(f"✅ Payment requirements created")
            print(f"   Amount: $0.001 USDC")
            print(f"   Pay To: {WALLET_ADDRESS}")
            print(f"   Network: {NETWORK}")
            
            print(f"\n🔥 READY TO TEST X402 VERIFY/SETTLE!")
            
        else:
            print(f"   ⚠️  No USDC balance")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")

print("\n" + "=" * 70)
