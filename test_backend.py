#!/usr/bin/env python3
"""Quick backend test to verify API is working"""
import asyncio
import httpx

BASE_URL = "http://localhost:8000"

async def test_backend():
    """Test basic backend endpoints"""
    print("Testing Backend API...")
    print("=" * 60)

    async with httpx.AsyncClient(timeout=10.0) as client:
        # Test 1: Health check
        print("\n1. Testing health endpoint...")
        try:
            response = await client.get(f"{BASE_URL}/health")
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.json()}")
        except Exception as e:
            print(f"   ❌ Error: {e}")

        # Test 2: List conversations
        print("\n2. Testing conversations list...")
        try:
            response = await client.get(f"{BASE_URL}/api/conversations")
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   Found {len(data)} conversations")
            else:
                print(f"   Response: {response.text[:200]}")
        except Exception as e:
            print(f"   ❌ Error: {e}")

        # Test 3: Create a conversation
        print("\n3. Creating a new conversation...")
        try:
            response = await client.post(
                f"{BASE_URL}/api/conversations",
                json={"title": "Test Conversation"}
            )
            print(f"   Status: {response.status_code}")
            if response.status_code in [200, 201]:
                data = response.json()
                conv_id = data.get("id")
                print(f"   ✓ Created conversation ID: {conv_id}")

                # Test 4: Get memory list
                print("\n4. Testing memory endpoint...")
                try:
                    response = await client.get(f"{BASE_URL}/api/memory")
                    print(f"   Status: {response.status_code}")
                    if response.status_code == 200:
                        memories = response.json()
                        print(f"   ✓ Found {len(memories)} memories")
                    else:
                        print(f"   Response: {response.text[:200]}")
                except Exception as e:
                    print(f"   ❌ Error: {e}")
            else:
                print(f"   Response: {response.text[:200]}")
        except Exception as e:
            print(f"   ❌ Error: {e}")

    print("\n" + "=" * 60)
    print("Backend test complete!")

if __name__ == "__main__":
    asyncio.run(test_backend())
