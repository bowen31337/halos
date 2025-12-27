#!/usr/bin/env python3
"""Test conversation branching feature."""

import urllib.request
import urllib.parse
import json
import time


def test_conversation_branching_feature():
    """Test the conversation branching API end-to-end."""
    base_url = "http://localhost:8000/api"

    print("=" * 60)
    print("CONVERSATION BRANCHING TEST")
    print("=" * 60)

    # Step 1: Create a conversation
    print("\n1. Creating a conversation...")
    conversation_data = {
        "title": "Test Conversation for Branching",
        "model": "claude-sonnet-4-5-20250929"
    }

    try:
        data = json.dumps(conversation_data).encode('utf-8')
        req = urllib.request.Request(
            f"{base_url}/conversations",
            data=data,
            headers={'Content-Type': 'application/json'}
        )

        with urllib.request.urlopen(req, timeout=10) as response:
            conversation = json.loads(response.read().decode())
            conversation_id = conversation["id"]
            print(f"   ✓ Created conversation: {conversation_id}")
    except Exception as e:
        print(f"   ✗ Failed to create conversation: {e}")
        return False

    # Step 2: Add messages to the conversation
    print("\n2. Adding messages to the conversation...")
    messages_data = [
        {"role": "user", "content": "Hello, how are you?"},
        {"role": "assistant", "content": "I'm doing well, thank you! How can I help you today?"},
        {"role": "user", "content": "Can you help me with a coding problem?"},
        {"role": "assistant", "content": "Of course! What coding problem are you working on?"},
    ]

    message_ids = []
    for i, msg_data in enumerate(messages_data):
        try:
            data = json.dumps(msg_data).encode('utf-8')
            req = urllib.request.Request(
                f"{base_url}/conversations/{conversation_id}/messages",
                data=data,
                headers={'Content-Type': 'application/json'}
            )

            with urllib.request.urlopen(req, timeout=10) as response:
                message = json.loads(response.read().decode())
                message_ids.append(message["id"])
                print(f"   ✓ Added message {i+1}: {message['id']}")
        except Exception as e:
            print(f"   ✗ Failed to add message {i+1}: {e}")
            return False

    # Step 3: List messages to verify
    print("\n3. Listing messages...")
    try:
        with urllib.request.urlopen(f"{base_url}/conversations/{conversation_id}/messages", timeout=5) as response:
            messages = json.loads(response.read().decode())
            print(f"   ✓ Found {len(messages)} messages")
            if len(messages) != 4:
                print(f"   ✗ Expected 4 messages, got {len(messages)}")
                return False
    except Exception as e:
        print(f"   ✗ Failed to list messages: {e}")
        return False

    # Step 4: Create a branch from the second message (assistant response)
    print("\n4. Creating a branch from the conversation...")
    branch_point_message_id = message_ids[1]  # Assistant's first response
    branch_data = {
        "branch_name": "Alternative Response",
        "branch_color": "blue",
        "message_id": branch_point_message_id
    }

    try:
        data = json.dumps(branch_data).encode('utf-8')
        req = urllib.request.Request(
            f"{base_url}/conversations/{conversation_id}/branch",
            data=data,
            headers={'Content-Type': 'application/json'}
        )

        with urllib.request.urlopen(req, timeout=10) as response:
            branch = json.loads(response.read().decode())
            branch_id = branch["id"]
            print(f"   ✓ Created branch: {branch_id}")
            print(f"   ✓ Branch name: {branch['branch_name']}")
            print(f"   ✓ Parent conversation: {branch['parent_conversation_id']}")
            print(f"   ✓ Branch point message: {branch['branch_point_message_id']}")
            print(f"   ✓ Message count: {branch['message_count']}")
    except Exception as e:
        print(f"   ✗ Failed to create branch: {e}")
        return False

    # Step 5: Verify branch has correct messages
    print("\n5. Verifying branch messages...")
    try:
        with urllib.request.urlopen(f"{base_url}/conversations/{branch_id}/messages", timeout=5) as response:
            branch_messages = json.loads(response.read().decode())
            print(f"   ✓ Branch has {len(branch_messages)} messages")

            if len(branch_messages) != 2:
                print(f"   ✗ Expected 2 messages in branch, got {len(branch_messages)}")
                return False

            # Verify the content matches the original messages
            if branch_messages[0]["content"] != messages_data[0]["content"]:
                print(f"   ✗ First message content mismatch")
                return False
            if branch_messages[1]["content"] != messages_data[1]["content"]:
                print(f"   ✗ Second message content mismatch")
                return False

            print("   ✓ Branch messages match original content")
    except Exception as e:
        print(f"   ✗ Failed to verify branch messages: {e}")
        return False

    # Step 6: List branches for the conversation
    print("\n6. Listing branches...")
    try:
        with urllib.request.urlopen(f"{base_url}/conversations/{conversation_id}/branches", timeout=5) as response:
            branches = json.loads(response.read().decode())
            print(f"   ✓ Found {len(branches)} branch(es)")

            if len(branches) != 1:
                print(f"   ✗ Expected 1 branch, got {len(branches)}")
                return False

            branch = branches[0]
            if branch["branch_name"] != "Alternative Response":
                print(f"   ✗ Branch name mismatch")
                return False
            if branch["id"] != branch_id:
                print(f"   ✗ Branch ID mismatch")
                return False

            print("   ✓ Branch listing verified")
    except Exception as e:
        print(f"   ✗ Failed to list branches: {e}")
        return False

    # Step 7: Get branch tree
    print("\n7. Getting branch tree...")
    try:
        with urllib.request.urlopen(f"{base_url}/conversations/{conversation_id}/branch-tree", timeout=5) as response:
            tree = json.loads(response.read().decode())
            print("   ✓ Retrieved branch tree")

            if "root" not in tree:
                print(f"   ✗ Missing root in tree")
                return False
            if "branches" not in tree:
                print(f"   ✗ Missing branches in tree")
                return False
            if "current_conversation" not in tree:
                print(f"   ✗ Missing current_conversation in tree")
                return False

            if len(tree["branches"]) != 1:
                print(f"   ✗ Expected 1 branch in tree, got {len(tree['branches'])}")
                return False

            if tree["root"]["id"] != conversation_id:
                print(f"   ✗ Root ID mismatch")
                return False
            if tree["current_conversation"]["id"] != conversation_id:
                print(f"   ✗ Current conversation ID mismatch")
                return False

            print("   ✓ Branch tree verified")
    except Exception as e:
        print(f"   ✗ Failed to get branch tree: {e}")
        return False

    # Step 8: Create another branch from a different message
    print("\n8. Creating another branch from a different message...")
    branch_point_message_id2 = message_ids[3]  # Assistant's second response
    branch_data2 = {
        "branch_name": "Different Path",
        "branch_color": "green",
        "message_id": branch_point_message_id2
    }

    try:
        data = json.dumps(branch_data2).encode('utf-8')
        req = urllib.request.Request(
            f"{base_url}/conversations/{conversation_id}/branch",
            data=data,
            headers={'Content-Type': 'application/json'}
        )

        with urllib.request.urlopen(req, timeout=10) as response:
            branch2 = json.loads(response.read().decode())
            branch2_id = branch2["id"]
            print(f"   ✓ Created second branch: {branch2_id}")
            print(f"   ✓ Branch point message: {branch2['branch_point_message_id']}")
            print(f"   ✓ Message count: {branch2['message_count']}")
    except Exception as e:
        print(f"   ✗ Failed to create second branch: {e}")
        return False

    # Step 9: Verify multiple branches
    print("\n9. Verifying multiple branches...")
    try:
        with urllib.request.urlopen(f"{base_url}/conversations/{conversation_id}/branches", timeout=5) as response:
            branches = json.loads(response.read().decode())
            print(f"   ✓ Found {len(branches)} branch(es)")

            if len(branches) != 2:
                print(f"   ✗ Expected 2 branches, got {len(branches)}")
                return False

            branch_names = [b["branch_name"] for b in branches]
            if "Alternative Response" not in branch_names:
                print(f"   ✗ Missing 'Alternative Response' branch")
                return False
            if "Different Path" not in branch_names:
                print(f"   ✗ Missing 'Different Path' branch")
                return False

            print("   ✓ Multiple branches verified")
    except Exception as e:
        print(f"   ✗ Failed to verify multiple branches: {e}")
        return False

    # Step 10: Test error cases
    print("\n10. Testing error cases...")

    # Test creating branch from non-existent conversation
    print("   Testing branch from non-existent conversation...")
    try:
        data = json.dumps(branch_data).encode('utf-8')
        req = urllib.request.Request(
            f"{base_url}/conversations/non-existent-id/branch",
            data=data,
            headers={'Content-Type': 'application/json'}
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            print(f"   ✗ Should have failed but got response: {response.read().decode()}")
            return False
    except Exception as e:
        if "404" in str(e) or "not found" in str(e).lower():
            print("   ✓ Correctly rejected non-existent conversation")
        else:
            print(f"   ✗ Unexpected error: {e}")
            return False

    # Test creating branch from non-existent message
    print("   Testing branch from non-existent message...")
    try:
        branch_data_invalid = {
            "branch_name": "Invalid Branch",
            "message_id": "non-existent-message-id"
        }
        data = json.dumps(branch_data_invalid).encode('utf-8')
        req = urllib.request.Request(
            f"{base_url}/conversations/{conversation_id}/branch",
            data=data,
            headers={'Content-Type': 'application/json'}
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            print(f"   ✗ Should have failed but got response: {response.read().decode()}")
            return False
    except Exception as e:
        if "404" in str(e) or "not found" in str(e).lower():
            print("   ✓ Correctly rejected non-existent message")
        else:
            print(f"   ✗ Unexpected error: {e}")
            return False

    print("\n" + "=" * 60)
    print("✓ ALL CONVERSATION BRANCHING TESTS PASSED!")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = test_conversation_branching_feature()
    exit(0 if success else 1)