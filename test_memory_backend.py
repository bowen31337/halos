#!/usr/bin/env python3
"""Test memory management backend endpoints."""
import asyncio
import httpx

BASE_URL = "http://localhost:8000"

async def test_memory_crud():
    """Test memory CRUD operations."""
    print("Testing Memory Management Backend...")
    print("=" * 60)

    async with httpx.AsyncClient(timeout=10.0) as client:
        # Test 1: List memories
        print("\n1. Listing memories...")
        try:
            response = await client.get(f"{BASE_URL}/api/memory")
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                memories = response.json()
                print(f"   ✓ Found {len(memories)} memories")
                if memories:
                    print(f"   Sample: {memories[0].get('content', '')[:50]}...")
        except Exception as e:
            print(f"   ❌ Error: {e}")

        # Test 2: Create a memory
        print("\n2. Creating a new memory...")
        try:
            response = await client.post(
                f"{BASE_URL}/api/memory",
                json={
                    "content": "Test memory: User prefers dark mode",
                    "category": "preference",
                    "conversation_id": None
                }
            )
            print(f"   Status: {response.status_code}")
            if response.status_code in [200, 201]:
                memory = response.json()
                memory_id = memory.get("id")
                print(f"   ✓ Created memory ID: {memory_id}")
                print(f"   Content: {memory.get('content')}")

                # Test 3: Get specific memory
                print("\n3. Getting specific memory...")
                try:
                    response = await client.get(f"{BASE_URL}/api/memory/{memory_id}")
                    print(f"   Status: {response.status_code}")
                    if response.status_code == 200:
                        memory = response.json()
                        print(f"   ✓ Retrieved: {memory.get('content')}")
                except Exception as e:
                    print(f"   ❌ Error: {e}")

                # Test 4: Update memory
                print("\n4. Updating memory...")
                try:
                    response = await client.put(
                        f"{BASE_URL}/api/memory/{memory_id}",
                        json={
                            "content": "Updated: User prefers dark mode with blue accent",
                            "category": "preference"
                        }
                    )
                    print(f"   Status: {response.status_code}")
                    if response.status_code == 200:
                        memory = response.json()
                        print(f"   ✓ Updated: {memory.get('content')}")
                except Exception as e:
                    print(f"   ❌ Error: {e}")

                # Test 5: Search memories
                print("\n5. Searching memories...")
                try:
                    response = await client.get(
                        f"{BASE_URL}/api/memory/search",
                        params={"query": "dark mode"}
                    )
                    print(f"   Status: {response.status_code}")
                    if response.status_code == 200:
                        results = response.json()
                        print(f"   ✓ Found {len(results)} results")
                except Exception as e:
                    print(f"   ❌ Error: {e}")

                # Test 6: Delete memory
                print("\n6. Deleting memory...")
                try:
                    response = await client.delete(f"{BASE_URL}/api/memory/{memory_id}")
                    print(f"   Status: {response.status_code}")
                    if response.status_code in [200, 204]:
                        print(f"   ✓ Memory deleted")
                except Exception as e:
                    print(f"   ❌ Error: {e}")
        except Exception as e:
            print(f"   ❌ Error: {e}")

    print("\n" + "=" * 60)
    print("Memory backend test complete!")

if __name__ == "__main__":
    asyncio.run(test_memory_crud())
