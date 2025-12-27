#!/usr/bin/env python3
"""
Test script for unread message indicators feature.
This tests the backend implementation without needing the frontend.
"""

import asyncio
import json
import sys
import os
import time
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent))

async def test_unread_indicators():
    """Test the unread message indicators functionality."""
    print("🧪 Testing Unread Message Indicators Feature")
    print("=" * 50)

    # Test 1: Create a conversation
    print("1️⃣ Creating a new conversation...")
    try:
        import uvicorn
        from src.main import app
        import httpx

        async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
            # Create conversation
            response = await client.post("/api/conversations", json={
                "title": "Test Conversation for Unread Indicators"
            })

            if response.status_code != 201:
                print(f"❌ Failed to create conversation: {response.status_code}")
                return False

            conversation = response.json()
            conv_id = conversation["id"]
            print(f"✅ Created conversation: {conv_id}")

            # Test 2: Verify initial unread count is 0
            print("2️⃣ Checking initial unread count...")
            if conversation["unread_count"] != 0:
                print(f"❌ Initial unread count should be 0, got {conversation['unread_count']}")
                return False
            print("✅ Initial unread count is 0")

            # Test 3: Create a user message (should not increment unread)
            print("3️⃣ Creating user message...")
            response = await client.post(f"/api/messages/conversations/{conv_id}/messages", json={
                "role": "user",
                "content": "Hello, this is a test message"
            })

            if response.status_code != 201:
                print(f"❌ Failed to create user message: {response.status_code}")
                return False

            # Get conversation and check unread count
            response = await client.get(f"/api/conversations/{conv_id}")
            conversation = response.json()

            if conversation["unread_count"] != 0:
                print(f"❌ Unread count should still be 0 after user message, got {conversation['unread_count']}")
                return False
            print("✅ Unread count remains 0 after user message")

            # Test 4: Create an assistant message (should increment unread)
            print("4️⃣ Creating assistant message...")
            response = await client.post(f"/api/messages/conversations/{conv_id}/messages", json={
                "role": "assistant",
                "content": "Hello! This is an assistant response."
            })

            if response.status_code != 201:
                print(f"❌ Failed to create assistant message: {response.status_code}")
                return False

            # Get conversation and check unread count
            response = await client.get(f"/api/conversations/{conv_id}")
            conversation = response.json()

            if conversation["unread_count"] != 1:
                print(f"❌ Unread count should be 1 after assistant message, got {conversation['unread_count']}")
                return False
            print("✅ Unread count incremented to 1 after assistant message")

            # Test 5: Create another assistant message
            print("5️⃣ Creating another assistant message...")
            response = await client.post(f"/api/messages/conversations/{conv_id}/messages", json={
                "role": "assistant",
                "content": "This is another assistant response."
            })

            if response.status_code != 201:
                print(f"❌ Failed to create second assistant message: {response.status_code}")
                return False

            # Get conversation and check unread count
            response = await client.get(f"/api/conversations/{conv_id}")
            conversation = response.json()

            if conversation["unread_count"] != 2:
                print(f"❌ Unread count should be 2 after second assistant message, got {conversation['unread_count']}")
                return False
            print("✅ Unread count incremented to 2 after second assistant message")

            # Test 6: Mark conversation as read
            print("6️⃣ Marking conversation as read...")
            response = await client.post(f"/api/conversations/{conv_id}/mark-read")

            if response.status_code != 200:
                print(f"❌ Failed to mark conversation as read: {response.status_code}")
                return False

            # Get conversation and check unread count
            response = await client.get(f"/api/conversations/{conv_id}")
            conversation = response.json()

            if conversation["unread_count"] != 0:
                print(f"❌ Unread count should be 0 after mark read, got {conversation['unread_count']}")
                return False
            print("✅ Unread count reset to 0 after mark read")

            # Test 7: Create more messages after reading (should increment again)
            print("7️⃣ Creating messages after reading...")
            await client.post(f"/api/messages/conversations/{conv_id}/messages", json={
                "role": "assistant",
                "content": "New message after reading."
            })

            response = await client.get(f"/api/conversations/{conv_id}")
            conversation = response.json()

            if conversation["unread_count"] != 1:
                print(f"❌ Unread count should be 1 after new message, got {conversation['unread_count']}")
                return False
            print("✅ Unread count incremented to 1 after new message")

            # Test 8: List conversations with unread counts
            print("8️⃣ Testing list conversations with unread counts...")
            response = await client.get("/api/conversations")
            conversations = response.json()

            # Find our conversation
            test_conv = None
            for conv in conversations:
                if conv["id"] == conv_id:
                    test_conv = conv
                    break

            if not test_conv:
                print("❌ Test conversation not found in list")
                return False

            if test_conv["unread_count"] != 1:
                print(f"❌ Listed conversation unread count should be 1, got {test_conv['unread_count']}")
                return False
            print("✅ List conversations shows correct unread count")

            print("\n🎉 All tests passed! Unread message indicators are working correctly.")
            return True

    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure the backend is properly set up and dependencies are installed.")
        return False
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False

async def main():
    """Main test function."""
    success = await test_unread_indicators()
    if success:
        print("\n✅ UNREAD MESSAGE INDICATORS FEATURE: IMPLEMENTATION COMPLETE")
        print("The feature #154 'Unread message indicators show on conversations' is ready for QA testing!")
        sys.exit(0)
    else:
        print("\n❌ UNREAD MESSAGE INDICATORS FEATURE: IMPLEMENTATION FAILED")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())