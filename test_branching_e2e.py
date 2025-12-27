#!/usr/bin/env python3
"""End-to-end test for conversation branching feature."""

import requests
import json
import time
import sys


def test_conversation_branching_e2e():
    """Complete end-to-end test for conversation branching."""
    base_url = "http://localhost:8000/api"

    print("=" * 80)
    print("CONVERSATION BRANCHING - END-TO-END TEST")
    print("=" * 80)

    # Step 1: Test health check
    print("\n1. Health check...")
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print("   ✓ Backend is healthy")
        else:
            print(f"   ✗ Backend returned {response.status_code}")
            return False
    except Exception as e:
        print(f"   ✗ Failed to connect to backend: {e}")
        return False

    # Step 2: Create a conversation
    print("\n2. Creating a conversation...")
    conversation_data = {
        "title": "E2E Test Conversation",
        "model": "claude-sonnet-4-5-20250929"
    }

    try:
        response = requests.post(f"{base_url}/conversations", json=conversation_data, timeout=10)
        if response.status_code == 201:
            conversation = response.json()
            conversation_id = conversation["id"]
            print(f"   ✓ Created conversation: {conversation_id}")
        else:
            print(f"   ✗ Failed to create conversation: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ✗ Failed to create conversation: {e}")
        return False

    # Step 3: Add messages to the conversation
    print("\n3. Adding messages to the conversation...")
    messages_data = [
        {"role": "user", "content": "Hello, how are you?"},
        {"role": "assistant", "content": "I'm doing well, thank you! How can I help you today?"},
        {"role": "user", "content": "Can you help me with a coding problem?"},
        {"role": "assistant", "content": "Of course! What coding problem are you working on?"},
        {"role": "user", "content": "I need to implement a binary search algorithm."},
    ]

    message_ids = []
    for i, msg_data in enumerate(messages_data):
        try:
            response = requests.post(f"{base_url}/conversations/{conversation_id}/messages", json=msg_data, timeout=10)
            if response.status_code == 200:
                message = response.json()
                message_ids.append(message["id"])
                print(f"   ✓ Added message {i+1}: {message['id']}")
            else:
                print(f"   ✗ Failed to add message {i+1}: {response.status_code}")
                return False
        except Exception as e:
            print(f"   ✗ Failed to add message {i+1}: {e}")
            return False

    # Step 4: Verify messages were added
    print("\n4. Verifying messages...")
    try:
        response = requests.get(f"{base_url}/conversations/{conversation_id}/messages", timeout=5)
        if response.status_code == 200:
            messages = response.json()
            if len(messages) == 5:
                print(f"   ✓ Found {len(messages)} messages")
            else:
                print(f"   ✗ Expected 5 messages, got {len(messages)}")
                return False
        else:
            print(f"   ✗ Failed to list messages: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ✗ Failed to list messages: {e}")
        return False

    # Step 5: Create a branch from the third message (user's coding request)
    print("\n5. Creating a branch...")
    branch_point_message_id = message_ids[2]  # "Can you help me with a coding problem?"
    branch_data = {
        "branch_name": "Alternative Response",
        "branch_color": "blue",
        "message_id": branch_point_message_id
    }

    try:
        response = requests.post(f"{base_url}/conversations/{conversation_id}/branch", json=branch_data, timeout=10)
        if response.status_code == 200:
            branch = response.json()
            branch_id = branch["id"]
            print(f"   ✓ Created branch: {branch_id}")
            print(f"   ✓ Branch name: {branch['branch_name']}")
            print(f"   ✓ Parent conversation: {branch['parent_conversation_id']}")
            print(f"   ✓ Branch point message: {branch['branch_point_message_id']}")
            print(f"   ✓ Message count: {branch['message_count']}")
        else:
            print(f"   ✗ Failed to create branch: {response.status_code}")
            print(f"   ✗ Response: {response.text}")
            return False
    except Exception as e:
        print(f"   ✗ Failed to create branch: {e}")
        return False

    # Step 6: Verify branch has correct messages
    print("\n6. Verifying branch messages...")
    try:
        response = requests.get(f"{base_url}/conversations/{branch_id}/messages", timeout=5)
        if response.status_code == 200:
            branch_messages = response.json()
            expected_count = 3  # Messages 0, 1, 2 from original
            if len(branch_messages) == expected_count:
                print(f"   ✓ Branch has {len(branch_messages)} messages (expected {expected_count})")

                # Verify content matches
                if (branch_messages[0]["content"] == messages_data[0]["content"] and
                    branch_messages[1]["content"] == messages_data[1]["content"] and
                    branch_messages[2]["content"] == messages_data[2]["content"]):
                    print("   ✓ Branch messages match original content")
                else:
                    print("   ✗ Branch message content mismatch")
                    return False
            else:
                print(f"   ✗ Expected {expected_count} messages in branch, got {len(branch_messages)}")
                return False
        else:
            print(f"   ✗ Failed to get branch messages: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ✗ Failed to verify branch messages: {e}")
        return False

    # Step 7: List branches
    print("\n7. Listing branches...")
    try:
        response = requests.get(f"{base_url}/conversations/{conversation_id}/branches", timeout=5)
        if response.status_code == 200:
            branches = response.json()
            if len(branches) == 1:
                print(f"   ✓ Found {len(branches)} branch")
                branch = branches[0]
                if (branch["branch_name"] == "Alternative Response" and
                    branch["id"] == branch_id):
                    print("   ✓ Branch details verified")
                else:
                    print("   ✗ Branch details mismatch")
                    return False
            else:
                print(f"   ✗ Expected 1 branch, got {len(branches)}")
                return False
        else:
            print(f"   ✗ Failed to list branches: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ✗ Failed to list branches: {e}")
        return False

    # Step 8: Get branch tree
    print("\n8. Getting branch tree...")
    try:
        response = requests.get(f"{base_url}/conversations/{conversation_id}/branch-tree", timeout=5)
        if response.status_code == 200:
            tree = response.json()
            print("   ✓ Retrieved branch tree")

            if ("root" in tree and "branches" in tree and "current_conversation" in tree):
                print("   ✓ Tree structure verified")

                if len(tree["branches"]) == 1:
                    print("   ✓ Tree has correct number of branches")
                else:
                    print(f"   ✗ Expected 1 branch in tree, got {len(tree['branches'])}")
                    return False

                if tree["root"]["id"] == conversation_id:
                    print("   ✓ Root conversation ID verified")
                else:
                    print("   ✗ Root conversation ID mismatch")
                    return False

                if tree["current_conversation"]["id"] == conversation_id:
                    print("   ✓ Current conversation ID verified")
                else:
                    print("   ✗ Current conversation ID mismatch")
                    return False
            else:
                print("   ✗ Tree structure incomplete")
                return False
        else:
            print(f"   ✗ Failed to get branch tree: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ✗ Failed to get branch tree: {e}")
        return False

    # Step 9: Create another branch from a different message
    print("\n9. Creating another branch...")
    branch_point_message_id2 = message_ids[4]  # "I need to implement a binary search algorithm."
    branch_data2 = {
        "branch_name": "Different Path",
        "branch_color": "green",
        "message_id": branch_point_message_id2
    }

    try:
        response = requests.post(f"{base_url}/conversations/{conversation_id}/branch", json=branch_data2, timeout=10)
        if response.status_code == 200:
            branch2 = response.json()
            branch2_id = branch2["id"]
            print(f"   ✓ Created second branch: {branch2_id}")
            print(f"   ✓ Branch point message: {branch2['branch_point_message_id']}")
            print(f"   ✓ Message count: {branch2['message_count']}")
        else:
            print(f"   ✗ Failed to create second branch: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ✗ Failed to create second branch: {e}")
        return False

    # Step 10: Verify multiple branches
    print("\n10. Verifying multiple branches...")
    try:
        response = requests.get(f"{base_url}/conversations/{conversation_id}/branches", timeout=5)
        if response.status_code == 200:
            branches = response.json()
            if len(branches) == 2:
                print(f"   ✓ Found {len(branches)} branches")

                branch_names = [b["branch_name"] for b in branches]
                if "Alternative Response" in branch_names and "Different Path" in branch_names:
                    print("   ✓ All branch names verified")
                else:
                    print("   ✗ Missing expected branches")
                    return False
            else:
                print(f"   ✗ Expected 2 branches, got {len(branches)}")
                return False
        else:
            print(f"   ✗ Failed to verify multiple branches: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ✗ Failed to verify multiple branches: {e}")
        return False

    # Step 11: Test error cases
    print("\n11. Testing error cases...")

    # Test creating branch from non-existent conversation
    print("   Testing branch from non-existent conversation...")
    try:
        response = requests.post(f"{base_url}/conversations/non-existent-id/branch", json=branch_data, timeout=5)
        if response.status_code == 404:
            print("   ✓ Correctly rejected non-existent conversation")
        else:
            print(f"   ✗ Expected 404, got {response.status_code}")
            return False
    except Exception as e:
        print(f"   ✗ Unexpected error: {e}")
        return False

    # Test creating branch from non-existent message
    print("   Testing branch from non-existent message...")
    try:
        branch_data_invalid = {
            "branch_name": "Invalid Branch",
            "message_id": "non-existent-message-id"
        }
        response = requests.post(f"{base_url}/conversations/{conversation_id}/branch", json=branch_data_invalid, timeout=5)
        if response.status_code == 404:
            print("   ✓ Correctly rejected non-existent message")
        else:
            print(f"   ✗ Expected 404, got {response.status_code}")
            return False
    except Exception as e:
        print(f"   ✗ Unexpected error: {e}")
        return False

    print("\n" + "=" * 80)
    print("✓ ALL CONVERSATION BRANCHING END-TO-END TESTS PASSED!")
    print("=" * 80)
    return True


if __name__ == "__main__":
    success = test_conversation_branching_e2e()
    sys.exit(0 if success else 1)