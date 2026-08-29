"""Testnet settlement tests with disposable wallets."""

import asyncio
from decimal import Decimal
from app.cdp_config import CDPConfig, CDP_API_KEY, CDP_API_SECRET
from app.treasury_policy import PILOT_POLICY

async def test_cdp_connection():
    """Test CDP API connection."""
    print("=" * 70)
    print("Testing CDP Connection")
    print("=" * 70)
    
    config = CDPConfig(api_key=CDP_API_KEY, api_secret=CDP_API_SECRET)
    print(f"\nCDP Config:")
    print(f"   API Key: {config.api_key[:8]}...")
    print(f"   Base URL: {config.base_url}")
    print(f"   Facilitator: {config.facilitator_url}")
    
    # Note: Full CDP client integration would go here
    # For now, just verify config is loaded
    print("\n✅ CDP configuration loaded successfully")
    print("   Next: Integrate CDP client for wallet/transfer operations")

async def test_treasury_policy():
    """Test treasury policy enforcement."""
    print("\n" + "=" * 70)
    print("Testing Treasury Policy")
    print("=" * 70)
    
    policy = PILOT_POLICY
    
    print(f"\nPolicy Configuration:")
    print(f"   Allowed Assets: {', '.join(policy.allowed_assets)}")
    print(f"   Allowed Networks: {', '.join(policy.allowed_networks)}")
    print(f"   Daily Limit: ${policy.max_exposure_per_day}")
    print(f"   Per-Tx Limit: ${policy.max_exposure_per_transaction}")
    print(f"   Total Exposure: ${policy.max_exposure_total}")
    print(f"   Paper Trading: {policy.paper_trading_mode}")
    
    # Test exposure checks
    print(f"\nExposure Checks:")
    
    test_cases = [
        (Decimal("50"), Decimal("0"), Decimal("0")),    # OK
        (Decimal("150"), Decimal("0"), Decimal("0")),   # Exceeds per-tx
        (Decimal("50"), Decimal("960"), Decimal("0")),  # Exceeds daily
        (Decimal("50"), Decimal("0"), Decimal("4960")), # Exceeds total
    ]
    
    for amount, daily, total in test_cases:
        allowed, message = policy.check_exposure(amount, daily, total)
        status = "✅" if allowed else "❌"
        print(f"   {status} ${amount} (daily=${daily}, total=${total}): {message}")

async def main():
    """Run all testnet tests."""
    await test_cdp_connection()
    await test_treasury_policy()
    
    print("\n" + "=" * 70)
    print("✅ Testnet configuration tests complete")
    print("=" * 70)
    print("\nNext steps:")
    print("  1. Integrate CDP client for wallet operations")
    print("  2. Create disposable wallets on Base Sepolia / Polygon Amoy / Solana Devnet")
    print("  3. Test x402 settlement flow with real payloads")
    print("  4. Monitor for 1 week, then enable autohedge")

if __name__ == "__main__":
    asyncio.run(main())
