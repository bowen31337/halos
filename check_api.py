#!/usr/bin/env python3
"""
Simple test to check if the unread_count field is present in API responses.
"""

import asyncio
import httpx

async def check_api_response():
    """Check the API response structure."""
    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        print("Testing API endpoints...")

        # Test 1: List conversations
        print("1. Testing /api/conversations")
        try:
            response = await client.get("/api/conversations")
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                conversations = response.json()
                if conversations:
                    print(f"First conversation: {conversations[0]}")
                    if 'unread_count' in conversations[0]:
                        print("✅ unread_count field is present in list response")
                    else:
                        print("❌ unread_count field is missing in list response")
                else:
                    print("No conversations found")
            else:
                print(f"Error: {response.text}")
        except Exception as e:
            print(f"Error: {e}")

        # Test 2: Create a conversation
        print("\n2. Testing /api/conversations POST")
        try:
            response = await client.post("/api/conversations", json={
                "title": "Test Conversation"
            })
            print(f"Status: {response.status_code}")
            if response.status_code == 201:
                conversation = response.json()
                print(f"Created conversation: {conversation}")
                if 'unread_count' in conversation:
                    print("✅ unread_count field is present in create response")
                else:
                    print("❌ unread_count field is missing in create response")
            else:
                print(f"Error: {response.text}")
        except Exception as e:
            print(f"Error: {e}")

        # Test 3: Get a specific conversation
        if response.status_code == 201:
            conv_id = conversation['id']
            print(f"\n3. Testing /api/conversations/{conv_id}")
            try:
                response = await client.get(f"/api/conversations/{conv_id}")
                print(f"Status: {response.status_code}")
                if response.status_code == 200:
                    conv = response.json()
                    print(f"Conversation details: {conv}")
                    if 'unread_count' in conv:
                        print("✅ unread_count field is present in get response")
                    else:
                        print("❌ unread_count field is missing in get response")
                else:
                    print(f"Error: {response.text}")
            except Exception as e:
                print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(check_api_response())