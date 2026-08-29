"""Test signing x402 payment with private key."""

import os
from web3 import Web3
from x402.schemas.v1 import PaymentRequirementsV1

# Your wallet
WALLET_ADDRESS = "0xdadeFD58681C5C5df68681735752a40CaAE5E152"
NETWORK = "base-sepolia"
RPC_URL = "https://sepolia.base.org"

print("=" * 70)
print("x402 Payment Signing Test")
print("=" * 70)

print(f"\nWallet: {WALLET_ADDRESS}")
print(f"Network: {NETWORK}")

# Get private key from environment (SECURE!)
private_key = os.getenv("TEST_PRIVATE_KEY")

if not private_key:
    print("\n⚠️  No private key found!")
    print("\nTo export from Metamask:")
    print("  1. Metamask → Settings → Security & Privacy")
    print("  2. 'Reveal Secret Recovery Phrase'")
    print("  3. Export private key for this account")
    print("  4. Set env var: export TEST_PRIVATE_KEY='your_key_here'")
    print("\n⚠️  SECURITY WARNING:")
    print("  - NEVER share your private key")
    print("  - NEVER commit it to git")
    print("  - Only use for testnet testing")
    print("  - Use separate test wallet (which you're doing ✅)")
else:
    print("\n✅ Private key found (hidden for security)")
    
    try:
        # Connect to Web3
        w3 = Web3(Web3.HTTPProvider(RPC_URL))
        
        print(f"\n✅ Connected to: {RPC_URL}")
        print(f"   Chain ID: {w3.eth.chain_id}")
        
        # Import account
        account = w3.eth.account.from_key(private_key)
        print(f"\n✅ Account loaded: {account.address}")
        
        # Verify it matches
        if account.address.lower() == WALLET_ADDRESS.lower():
            print(f"   ✅ Address matches!")
        else:
            print(f"   ⚠️  Address mismatch!")
            print(f"   Expected: {WALLET_ADDRESS}")
            print(f"   Got: {account.address}")
        
        # Check balance
        balance = w3.eth.get_balance(account.address)
        balance_eth = w3.from_wei(balance, 'ether')
        print(f"\n💰 Balance: {balance_eth:.4f} ETH")
        
        if balance_eth > 0:
            print(f"   🎉 Ready to cook!")
        else:
            print(f"   ⚠️  No balance - get test ETH from faucet")
        
        # Create payment requirements
        print(f"\nCreating payment requirements...")
        requirements = PaymentRequirementsV1(
            maxAmountRequired="1000000000000000",  # 0.001 ETH
            asset="ETH",
            resource="test-identity-access",
            description="Test payment for identity node access",
            payTo=WALLET_ADDRESS,
            network=NETWORK,
            scheme="exact",
            maxTimeoutSeconds=300,
        )
        
        print(f"✅ Payment requirements created")
        print(f"   Amount: 0.001 ETH")
        print(f"   Pay To: {WALLET_ADDRESS}")
        
        # TODO: Sign the payment hash
        print(f"\nNext: Sign payment hash and test verify endpoint")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting:")
        print("  - Check private key format (should be 64 hex chars)")
        print("  - Check RPC URL is working")
        print("  - Make sure you're on testnet")

print("\n" + "=" * 70)
