"""Test x402 flow with your Sepolia wallet."""

import asyncio
from x402.http import HTTPFacilitatorClientSync, FacilitatorConfig
from x402.schemas.v1 import PaymentRequirementsV1

# Your wallet with test ETH
WALLET_ADDRESS = "0xdadeFD58681C5C5df68681735752a40CaAE5E152"
NETWORK = "base-sepolia"
CHAIN_ID = 84532

async def test_facilitator_connection():
    """Test connection to x402 facilitator."""
    print("=" * 70)
    print("x402 Facilitator Connection Test")
    print("=" * 70)
    
    print(f"\nWallet: {WALLET_ADDRESS}")
    print(f"Network: {NETWORK} (Chain ID: {CHAIN_ID})")
    
    # Connect to facilitator
    client = HTTPFacilitatorClientSync(
        FacilitatorConfig(url="https://x402.org/facilitator")
    )
    
    print(f"\n✅ Connected to: {client.url}")
    
    # Get supported schemes
    supported = client.get_supported()
    print(f"\nSupported schemes on Base Sepolia:")
    
    for kind in supported.kinds:
        if "84532" in str(kind.network) or "base-sepolia" in str(kind.network).lower():
            print(f"  ✅ {kind.scheme} (v{kind.x402_version})")
            if kind.extra:
                for k, v in kind.extra.items():
                    print(f"     {k}: {v}")
    
    return client

async def test_create_payment_requirements(client):
    """Create payment requirements for test."""
    print("\n" + "=" * 70)
    print("Creating Payment Requirements")
    print("=" * 70)
    
    # Create payment requirements for 0.001 ETH (~$0.003)
    requirements = PaymentRequirementsV1(
        maxAmountRequired="1000000000000000",  # 0.001 ETH in wei
        asset="ETH",
        resource="test-identity-access",
        description="Test payment for identity node access",
        payTo=WALLET_ADDRESS,
        network=NETWORK,
        scheme="exact",
        maxTimeoutSeconds=300,  # 5 minute timeout
    )
    
    print(f"\nPayment Requirements:")
    print(f"  Amount: 0.001 ETH (~$0.003)")
    print(f"  Asset: ETH")
    print(f"  Pay To: {WALLET_ADDRESS}")
    print(f"  Network: {NETWORK}")
    print(f"  Scheme: exact")
    print(f"  Timeout: 300 seconds")
    
    return requirements

async def main():
    """Run all tests."""
    client = await test_facilitator_connection()
    requirements = await test_create_payment_requirements(client)
    
    print("\n" + "=" * 70)
    print("✅ x402 Connection Test COMPLETE!")
    print("=" * 70)
    print("\n🎉 You're ready to cook!")
    print("\nNext steps:")
    print("  1. Export private key from Metamask")
    print("  2. Sign payment payload")
    print("  3. Test verify endpoint")
    print("  4. Test settle endpoint")

if __name__ == "__main__":
    asyncio.run(main())
