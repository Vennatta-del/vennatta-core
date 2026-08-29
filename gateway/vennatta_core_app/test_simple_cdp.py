"""Simple CDP test - just verify SDK loads."""

print("=" * 70)
print("CDP SDK Test")
print("=" * 70)

try:
    import cdp
    print(f"✅ CDP SDK loaded: {cdp}")
    print(f"   Module: {cdp.__file__}")
    print(f"   Available: {[x for x in dir(cdp) if not x.startswith('_')][:15]}")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "=" * 70)
print("Next: Get test ETH on Base Sepolia")
print("=" * 70)
print("\nFaucets:")
print("  1. Base Sepolia ETH: https://www.alchemy.com/faucets/base-sepolia")
print("  2. Coinbase Faucet: https://faucet.coinbase.com/")
print("  3. QuickNode: https://faucet.quicknode.com/base/sepolia")
print("\nYour wallet: 0xE7d7BdF214E23A8fD1ED22e476BF742862a70212")
print("\nGet ~0.01-0.1 test ETH for gas (it's free!)")
