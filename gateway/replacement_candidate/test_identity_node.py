"""Test identity node with x402 gate integration."""

import asyncio
import httpx
from app.identity_node import identity_app, API_TOKEN

async def test_identity_node():
    """Test identity node endpoints."""
    
    # Create ASGI test client
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=identity_app),
        base_url="http://test"
    ) as client:
        
        print("=" * 70)
        print("Testing Identity Node")
        print("=" * 70)
        
        # Test 1: Health check (no auth required)
        print("\n1. Health check...")
        response = await client.get("/health")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
        
        # Test 2: Protected endpoint without auth
        print("\n2. Protected endpoint (no auth)...")
        response = await client.get("/api/v1/identity")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
        
        # Test 3: Protected endpoint with auth
        print("\n3. Protected endpoint (with auth)...")
        response = await client.get(
            "/api/v1/identity",
            headers={"Authorization": f"Bearer {API_TOKEN}"}
        )
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
        
        # Test 4: Rate limiting
        print("\n4. Rate limiting test...")
        for i in range(5):
            response = await client.get("/health")
            print(f"   Request {i+1}: {response.status_code}")
        
        print("\n" + "=" * 70)
        print("✅ Identity node tests complete")
        print("=" * 70)

if __name__ == "__main__":
    asyncio.run(test_identity_node())
