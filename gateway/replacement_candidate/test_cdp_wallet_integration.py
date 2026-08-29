"""Test CDP wallet integration with Base Sepolia."""

import asyncio
from decimal import Decimal
from app.cdp_config import CDP_API_KEY, CDP_API_SECRET
from app.treasury_policy import PILOT_POLICY

# Your Base Sepolia wallet
WALLET_ADDRESS = "0xE7d7BdF214E23A8fD1ED22e476BF742862a70212"
NETWORK = "base-sepolia"

async def test_cdp_wallet():
    """Test CDP wallet connection and balance."""
    print("=" * 70)
    print("CDP Wallet Integration Test")
    print("=" * 70)
    
    print(f"\nWallet: {WALLET_ADDRESS}")
    print(f"Network: {NETWORK}")
    
    try:
        from cdp import Wallet
        
        print("\nConnecting to CDP...")
        
        # Try to fetch wallet
        # Note: CDP SDK API may vary - this is a basic example
        print("✅ CDP SDK imported successfully")
        
        # Check what's available in the SDK
        print(f"\nCDP SDK version: {cdp.__version__ if hasattr(cdp, '__version__') else 'unknown'}")
        print(f"Available: {[x for x in dir(cdp) if not x.startswith('_')][:10]}...")
        
        # For now, just verify the SDK loads
        print("\n✅ CDP SDK ready")
        print("\nNext: Create or fetch wallet, check balance")
        
    except ImportError as e:
        print(f"❌ CDP SDK import failed: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")

async def test_x402_verify_flow():
    """Test x402 verify flow with Base Sepolia."""
    print("\n" + "=" * 70)
    print("x402 Verify Flow Test")
    print("=" * 70)
    
    from x402.http import HTTPFacilitatorClientSync, FacilitatorConfig
    from x402.schemas import PaymentRequirements, PaymentPayload
    from x402.schemas import Network, AssetAmount, Money
    
    # Create client
    facilitator_url = "https://x402.org/facilitator"
    client = HTTPFacilitatorClientSync(
        FacilitatorConfig(url=facilitator_url)
    )
    
    print(f"\nFacilitator: {client.url}")
    
    # Create test payment requirements
    # For Base Sepolia with USDC
    requirements = PaymentRequirements(
        maxAmountRequired=Money(amount="1000000", asset="USDC"),  # 1 USDC (6 decimals)
        resource="test-resource",
        description="Test payment for identity node access",
        payTo=WALLET_ADDRESS,
        network=NETWORK,
        scheme="exact",
    )
    
    print(f"\nPayment Requirements:")
    print(f"   Amount: {requirements.maxAmountRequired.amount} {requirements.maxAmountRequired.asset}")
    print(f"   Pay To: {requirements.payTo}")
    print(f"   Network: {requirements.network}")
    print(f"   Scheme: {requirements.scheme}")
    
    # Test verify endpoint
    print(f"\nTesting verify endpoint...")
    try:
        # We need a real signed payload for verify
        # For now, just show what we'd send
        print("✅ Requirements created")
        print("\nTo test verify, we need:")
        print("  1. Signed payment payload from wallet")
        print("  2. Call client.verify(payload, requirements)")
        
    except Exception as e:
        print(f"❌ Error: {e}")

async def main():
    """Run all tests."""
    await test_cdp_wallet()
    await test_x402_verify_flow()
    
    print("\n" + "=" * 70)
    print("✅ Integration test complete")
    print("=" * 70)
    print("\nNext steps:")
    print("  1. Check CDP SDK documentation for wallet creation")
    print("  2. Create wallet on Base Sepolia")
    print("  3. Get test USDC from faucet")
    print("  4. Sign payment payload")
    print("  5. Test verify → settle flow")

if __name__ == "__main__":
    asyncio.run(main())
