"""Test script for batch API operations."""

import asyncio
import httpx
from uuid import UUID
from datetime import datetime

# Backend URL
BASE_URL = "http://localhost:8001"


async def test_batch_operations():
    """Test batch operations API."""
    async with httpx.AsyncClient() as client:
        print("Testing Batch API Operations\n")
        print("=" * 60)

        # Test 1: Check if batch endpoint exists
        print("\n1. Checking batch API endpoint...")
        try:
            response = await client.get(f"{BASE_URL}/docs")
            if response.status_code == 200:
                print("✓ Backend is accessible")

                # Check if batch operations are documented
                if "batch" in response.text.lower():
                    print("✓ Batch operations found in API docs")
                else:
                    print("⚠ Batch operations not yet visible in docs (may need restart)")
            else:
                print(f"✗ Backend returned status {response.status_code}")
        except Exception as e:
            print(f"✗ Error accessing backend: {e}")
            return

        # Test 2: Create test conversations
        print("\n2. Creating test conversations...")
        conversation_ids = []

        for i in range(3):
            try:
                response = await client.post(
                    f"{BASE_URL}/api/conversations",
                    json={
                        "title": f"Batch Test Conversation {i+1}",
                        "model": "claude-sonnet-4-5-20250929"
                    }
                )
                if response.status_code == 200:
                    conv_data = response.json()
                    conv_id = conv_data.get("id")
                    conversation_ids.append(UUID(conv_id))
                    print(f"✓ Created conversation {i+1}: {conv_id}")
                else:
                    print(f"✗ Failed to create conversation {i+1}: {response.status_code}")
            except Exception as e:
                print(f"✗ Error creating conversation {i+1}: {e}")

        if not conversation_ids:
            print("\n✗ No conversations created, cannot proceed with batch tests")
            return

        # Test 3: Batch archive operation
        print("\n3. Testing batch archive operation...")
        try:
            response = await client.post(
                f"{BASE_URL}/api/batch/conversations",
                json={
                    "conversation_ids": [str(cid) for cid in conversation_ids[:2]],
                    "operation": "archive"
                }
            )

            if response.status_code == 200:
                result = response.json()
                print(f"✓ Batch archive completed")
                print(f"  - Total requested: {result['total_requested']}")
                print(f"  - Total processed: {result['total_processed']}")
                print(f"  - Successful: {len(result['successful'])}")
                print(f"  - Failed: {len(result['failed'])}")
                print(f"  - Processing time: {result['processing_time_seconds']:.2f}s")
            else:
                print(f"✗ Batch archive failed: {response.status_code}")
                print(f"  Response: {response.text}")
        except Exception as e:
            print(f"✗ Error during batch archive: {e}")

        # Test 4: Batch export operation
        print("\n4. Testing batch export operation...")
        try:
            response = await client.post(
                f"{BASE_URL}/api/batch/conversations/export",
                params={
                    "conversation_ids": [str(cid) for cid in conversation_ids],
                    "export_format": "json"
                }
            )

            if response.status_code == 200:
                result = response.json()
                print(f"✓ Batch export completed")
                print(f"  - Total requested: {result['total_requested']}")
                print(f"  - Total exported: {result['total_exported']}")
                print(f"  - Export format: {result['export_format']}")
                print(f"  - File URL: {result.get('file_url', 'N/A')}")
                print(f"  - Processing time: {result['processing_time_seconds']:.2f}s")
            else:
                print(f"✗ Batch export failed: {response.status_code}")
                print(f"  Response: {response.text[:200]}")
        except Exception as e:
            print(f"✗ Error during batch export: {e}")

        # Test 5: Batch delete operation (cleanup)
        print("\n5. Testing batch delete operation (cleanup)...")
        try:
            response = await client.post(
                f"{BASE_URL}/api/batch/conversations",
                json={
                    "conversation_ids": [str(cid) for cid in conversation_ids],
                    "operation": "delete"
                }
            )

            if response.status_code == 200:
                result = response.json()
                print(f"✓ Batch delete completed")
                print(f"  - Total requested: {result['total_requested']}")
                print(f"  - Successful: {len(result['successful'])}")
                print(f"  - Failed: {len(result['failed'])}")
            else:
                print(f"✗ Batch delete failed: {response.status_code}")
        except Exception as e:
            print(f"✗ Error during batch delete: {e}")

        print("\n" + "=" * 60)
        print("Batch API Tests Complete!")


if __name__ == "__main__":
    asyncio.run(test_batch_operations())
