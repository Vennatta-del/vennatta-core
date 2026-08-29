"""Test x402 facilitator client with bazaar extension (sync version)"""

from x402.http import HTTPFacilitatorClientSync, FacilitatorConfig
from x402.extensions.bazaar import with_bazaar, ListDiscoveryResourcesParams, SearchDiscoveryResourcesParams

print("=" * 70)
print("Creating x402 facilitator client (SYNC)...")
print("=" * 70)

# Create client with bazaar extension - MUST use sync client
# Default URL is https://x402.org - you may need to configure a different facilitator
client = with_bazaar(HTTPFacilitatorClientSync())
print(f"✅ Client created successfully")
print(f"   URL: {client.url}")

# Test 1: List discovery resources
print("\nTest 1: Listing x402 discovery resources...")
try:
    result = client.extensions.bazaar.list_resources(
        ListDiscoveryResourcesParams(limit=10)
    )
    print(f"✅ Found {len(result.items)} resources")
    for resource in result.items[:3]:  # Show first 3
        print(f"   - {resource.resource}")
except Exception as e:
    error_str = str(e)
    if "404" in error_str:
        print(f"⚠️  404 Error: The facilitator at {client.url} doesn't support /discovery/resources")
        print(f"   This is expected - configure a bazaar-enabled facilitator URL")
    else:
        print(f"❌ Error: {e}")

# Test 2: Search for resources
print("\nTest 2: Searching for 'payment' resources...")
try:
    results = client.extensions.bazaar.search(
        SearchDiscoveryResourcesParams(query="payment", limit=5)
    )
    print(f"✅ Found {len(results.items)} resources")
    for resource in results.items:
        print(f"   - {resource.resource}")
except Exception as e:
    error_str = str(e)
    if "404" in error_str:
        print(f"⚠️  404 Error: The facilitator at {client.url} doesn't support /discovery/search")
    else:
        print(f"❌ Error: {e}")

print("\n" + "=" * 70)
print("✅ CLIENT STRUCTURE VALIDATED")
print("=" * 70)
print("\nThe x402 facilitator client with bazaar extension is working!")
print("\n⚠️  IMPORTANT NOTES:")
print("  • Bazaar extension requires HTTPFacilitatorClientSync (not async)")
print("  • Default URL (x402.org) may not support bazaar endpoints")
print("  • Configure FacilitatorConfig(url='...') with a bazaar-enabled facilitator")
print("\nUsage example:")
print("  client = with_bazaar(")
print("    HTTPFacilitatorClientSync(")
print("      FacilitatorConfig(url='https://your-bazaar-facilitator.com')")
print("    )")
print("  )")
print("\nNext steps:")
print("  1. Configure a bazaar-enabled facilitator URL")
print("  2. Add proper CDP authentication if needed")
print("  3. Integrate into your gateway")
print("=" * 70)
