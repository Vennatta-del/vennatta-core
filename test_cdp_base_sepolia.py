"""Test x402 on Base Sepolia using CDP SDK."""

import os
from cdp import Cdp, Wallet
from app.cdp_config import CDP_API_KEY, CDP_API_SECRET

print("=" * 70)
print("CDP Base Sepolia Test")
print("=" * 70)

print(f"\nAPI Key: {CDP_API_KEY[:8]}...")

try:
    # Configure CDP
    Cdp.configure(CDP_API_KEY, CDP_API_SECRET)
    print(f"✅ CDP configured")
    
    # Create wallet on Base Sepolia
    print(f"\nCreating wallet on Base Sepolia...")
    wallet = Wallet.create(network_id="base-sepolia")
    
    print(f"✅ Wallet created!")
    print(f"   Address: {wallet.default_address.address_id}")
    print(f"   Network: {wallet.network_id}")
    
    # Check balance
    print(f"\nChecking balances...")
    balances = wallet.balances()
    for asset, amount in balances.items():
        print(f"   {asset}: {amount}")
    
    # Get faucet funds
    print(f"\n💡 To get test ETH:")
    print(f"   1. Go to: https://faucet.quicknode.com/base/sepolia")
    print(f"   2. Paste: {wallet.default_address.address_id}")
    print(f"   3. Get free test ETH")
    
    # Save wallet info
    print(f"\n💾 Wallet seed (save this!):")
    print(f"   {wallet.export_data()['seed']}")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    print(f"\nTroubleshooting:")
    print(f"  - Check CDP API credentials")
    print(f"  - Check CDP SDK version: pip show cdp")

print(f"\n" + "=" * 70)
