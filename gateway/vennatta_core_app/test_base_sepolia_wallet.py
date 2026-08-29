"""Test Base Sepolia wallet with x402 settlement flow."""

import asyncio
from decimal import Decimal
from app.cdp_config import CDP_API_KEY, CDP_API_SECRET
from app.treasury_policy import PILOT_POLICY

# Your Base Sepolia wallet
WALLET_ADDRESS = "0xE7d7BdF214E23A8fD1ED22e476BF742862a70212"
NETWORK = "base-sepolia"

async def test_wallet_connection():
    """Test wallet connection and balance check."""
    print("=" * 70)
    print("Base Sepolia Wallet Test")
    print("=" * 70)
    
    print(f"\nWallet: {WALLET_ADDRESS}")
    print(f"Network: {NETWORK}")
    
    print(f"\nCDP Config:")
    print(f"   API Key: {CDP_API_KEY[:8]}...")
    print(f"   Network: {NETWORK}")
    
    # Treasury Policy
    policy = PILOT_POLICY
    print(f"\nTreasury Policy:")
    print(f"   Allowed: {', '.join(policy.allowed_networks)}")
    print(f"   In Policy: {policy.is_network_allowed(NETWORK)}")
    
    print("\n✅ Wallet configuration ready")

async def test_cdp_wallet_balance():
    """Test CDP wallet balance check."""
    print("\n" + "=" * 70)
    print("CDP Wallet Balance Check")
    print("=" * 70)
    
    try:
        from cdp import Wallet
        
        # Try to fetch existing wallet by ID (if you have one)
        # Or create new wallet
        print("\nAttempting to connect to CDP...")
        print(f"Wallet Address: {WALLET_ADDRESS}")
        
        # For now, just verify CDP SDK is available
        print("✅ CDP SDK available")
        print("\nTo check balance:")
        print("  from cdp import Wallet")
        print(f"  wallet = Wallet.fetch('{WALLET_ADDRESS}')")
        print("  print(wallet.balance('USDC'))")
        
    except ImportError:
        print("❌ CDP SDK not installed")
        print("\nInstall with: pip install cdp")

async def test_x402_basic():
    """Test basic x402 client (without bazaar)."""
    print("\n" + "=" * 70)
    print("x402 Basic Client Test")
    print("=" * 70)
    
    from x402.http import HTTPFacilitatorClientSync, FacilitatorConfig
    
    # Use default x402.org facilitator for now
    facilitator_url = "https://x402.org/facilitator"
    print(f"\nConnecting to: {facilitator_url}")
    
    try:
        client = HTTPFacilitatorClientSync(
            FacilitatorConfig(url=facilitator_url)
        )
        print(f"✅ Client created successfully")
        print(f"   URL: {client.url}")
        
        # Test supported endpoint
        print(f"\nTesting supported endpoint...")
        try:
            result = client.get_supported()
            print(f"✅ Supported: {result}")
        except Exception as e:
            print(f"⚠️  get_supported: {e}")
        
    except Exception as e:
        print(f"❌ Failed: {e}")

async def main():
    """Run all tests."""
    await test_wallet_connection()
    await test_cdp_wallet_balance()
    await test_x402_basic()
    
    print("\n" + "=" * 70)
    print("✅ Test complete")
    print("=" * 70)
    print("\nNext steps:")
    print("  1. Check if CDP SDK is installed: pip list | grep cdp")
    print("  2. If not: pip install cdp")
    print("  3. Create/fetch wallet on Base Sepolia")
    print("  4. Check USDC balance")
    print("  5. Test x402 verify/settle flow")

if __name__ == "__main__":
    asyncio.run(main())
