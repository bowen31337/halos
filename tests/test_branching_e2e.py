"""End-to-end tests for conversation branching feature.

This test suite verifies Feature #48: Conversation branching creates alternative paths from any message.
"""

import json
import uuid
from urllib.request import Request, urlopen

# Configuration
BACKEND_URL = "http://localhost:8000"


def test_backend_health():
    """Test 1: Verify backend is running."""
    print("\n1. Testing backend health...")
    try:
        req = Request(f"{BACKEND_URL}/health")
        response = urlopen(req, timeout=5)
        data = json.loads(response.read().decode())
        assert data["status"] == "healthy", "Backend not healthy"
        print("   ✓ Backend is healthy")
        return True
    except Exception as e:
        print(f"   ✗ Backend health check failed: {e}")
        return False


def test_create_conversation():
    """Test 2: Create a test conversation with messages."""
    print("\n2. Creating test conversation with messages...")
    try:
        # Create conversation
        req = Request(
            f"{BACKEND_URL}/api/conversations",
            data=json.dumps({"title": "Branching Test Conversation"}).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        response = urlopen(req, timeout=5)
        data = json.loads(response.read().decode())
        assert "id" in data, "No conversation ID returned"
        conversation_id = data["id"]
        print(f"   ✓ Conversation created: {conversation_id}")

        # Add messages
        messages = [
            {"role": "user", "content": "First message"},
            {"role": "assistant", "content": "First response"},
            {"role": "user", "content": "Second message"},
            {"role": "assistant", "content": "Second response"},
        ]

        message_ids = []
        for msg in messages:
            req = Request(
                f"{BACKEND_URL}/api/messages/conversations/{conversation_id}/messages",
                data=json.dumps(msg).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            response = urlopen(req, timeout=5)
            msg_data = json.loads(response.read().decode())
            message_ids.append(msg_data["id"])

        print(f"   ✓ Created {len(messages)} messages")
        return conversation_id, message_ids
    except Exception as e:
        print(f"   ✗ Failed to create conversation: {e}")
        return None, None


def test_create_branch(conversation_id: str, message_ids: list):
    """Test 3: Create a branch from a message."""
    print("\n3. Creating branch from message...")
    try:
        # Branch from the second message (first assistant response)
        branch_point_id = message_ids[1]

        branch_data = {
            "branch_point_message_id": branch_point_id,
            "branch_name": "Alternative Path",
            "branch_color": "#ff6b6b"
        }

        req = Request(
            f"{BACKEND_URL}/api/conversations/{conversation_id}/branch",
            data=json.dumps(branch_data).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        response = urlopen(req, timeout=5)
        branch_result = json.loads(response.read().decode())

        assert "conversation" in branch_result, "No conversation in branch result"
        branch_id = branch_result["conversation"]["id"]
        assert branch_result["conversation"]["parent_conversation_id"] == conversation_id
        assert branch_result["conversation"]["branch_name"] == "Alternative Path"

        print(f"   ✓ Branch created: {branch_id}")
        print(f"   ✓ Branch name: {branch_result['conversation']['branch_name']}")
        print(f"   ✓ Parent ID: {branch_result['conversation']['parent_conversation_id']}")
        return branch_id
    except Exception as e:
        print(f"   ✗ Failed to create branch: {e}")
        return None


def test_branch_messages(branch_id: str, original_message_count: int):
    """Test 4: Verify branch has messages up to branch point."""
    print("\n4. Verifying branch messages...")
    try:
        req = Request(
            f"{BACKEND_URL}/api/messages/conversations/{branch_id}/messages",
            headers={"Content-Type": "application/json"},
            method="GET",
        )
        response = urlopen(req, timeout=5)
        messages = json.loads(response.read().decode())

        # Branch should have 2 messages (first user + first assistant up to branch point)
        assert len(messages) == 2, f"Expected 2 messages, got {len(messages)}"
        print(f"   ✓ Branch has {len(messages)} messages (correct)")
        return True
    except Exception as e:
        print(f"   ✗ Failed to verify branch messages: {e}")
        return False


def test_branch_independence(conversation_id: str, branch_id: str):
    """Test 5: Verify branches are independent."""
    print("\n5. Testing branch independence...")
    try:
        # Add different message to original conversation
        req = Request(
            f"{BACKEND_URL}/api/messages/conversations/{conversation_id}/messages",
            data=json.dumps({"role": "user", "content": "Original continuation"}).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        urlopen(req, timeout=5)

        # Add different message to branch
        req = Request(
            f"{BACKEND_URL}/api/messages/conversations/{branch_id}/messages",
            data=json.dumps({"role": "user", "content": "Branch continuation"}).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        urlopen(req, timeout=5)

        # Check original conversation
        req = Request(
            f"{BACKEND_URL}/api/messages/conversations/{conversation_id}/messages",
            method="GET",
        )
        response = urlopen(req, timeout=5)
        original_msgs = json.loads(response.read().decode())

        # Check branch conversation
        req = Request(
            f"{BACKEND_URL}/api/messages/conversations/{branch_id}/messages",
            method="GET",
        )
        response = urlopen(req, timeout=5)
        branch_msgs = json.loads(response.read().decode())

        # Both should have 3 messages now
        assert len(original_msgs) == 3, f"Original should have 3 messages, got {len(original_msgs)}"
        assert len(branch_msgs) == 3, f"Branch should have 3 messages, got {len(branch_msgs)}"

        # Last messages should be different
        assert original_msgs[-1]["content"] == "Original continuation"
        assert branch_msgs[-1]["content"] == "Branch continuation"

        print(f"   ✓ Original has {len(original_msgs)} messages")
        print(f"   ✓ Branch has {len(branch_msgs)} messages")
        print(f"   ✓ Last messages are different (independence verified)")
        return True
    except Exception as e:
        print(f"   ✗ Branch independence test failed: {e}")
        return False


def test_list_branches(conversation_id: str):
    """Test 6: List all branches of a conversation."""
    print("\n6. Testing list branches...")
    try:
        req = Request(
            f"{BACKEND_URL}/api/conversations/{conversation_id}/branches",
            method="GET",
        )
        response = urlopen(req, timeout=5)
        result = json.loads(response.read().decode())

        assert "branches" in result, "No branches in response"
        assert "count" in result, "No count in response"
        assert result["count"] >= 1, "Should have at least 1 branch"

        print(f"   ✓ Found {result['count']} branch(es)")
        for branch in result["branches"]:
            print(f"      - {branch.get('branch_name', branch.get('title', 'Unnamed'))}")
        return True
    except Exception as e:
        print(f"   ✗ List branches test failed: {e}")
        return False


def test_branch_path(branch_id: str):
    """Test 7: Get branch path from root to current."""
    print("\n7. Testing branch path...")
    try:
        req = Request(
            f"{BACKEND_URL}/api/conversations/{branch_id}/branch-path",
            method="GET",
        )
        response = urlopen(req, timeout=5)
        result = json.loads(response.read().decode())

        assert "branch_path" in result, "No branch_path in response"
        assert "is_branch" in result, "No is_branch in response"
        assert result["is_branch"] == True, "Should be marked as a branch"

        path_length = len(result["branch_path"])
        print(f"   ✓ Branch path length: {path_length}")
        print(f"   ✓ Path from root to branch:")
        for i, node in enumerate(result["branch_path"]):
            print(f"      {i+1}. {node.get('title', 'Unnamed')}")

        return True
    except Exception as e:
        print(f"   ✗ Branch path test failed: {e}")
        return False


def test_multiple_branches_from_same_point(conversation_id: str, message_ids: list):
    """Test 8: Create multiple branches from the same message."""
    print("\n8. Testing multiple branches from same point...")
    try:
        branch_point_id = message_ids[1]

        # Create second branch from same point
        branch_data = {
            "branch_point_message_id": branch_point_id,
            "branch_name": "Second Alternative",
            "branch_color": "#00ff00"
        }

        req = Request(
            f"{BACKEND_URL}/api/conversations/{conversation_id}/branch",
            data=json.dumps(branch_data).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        response = urlopen(req, timeout=5)
        branch2 = json.loads(response.read().decode())

        branch2_id = branch2["conversation"]["id"]
        print(f"   ✓ Second branch created: {branch2_id}")

        # List branches again
        req = Request(
            f"{BACKEND_URL}/api/conversations/{conversation_id}/branches",
            method="GET",
        )
        response = urlopen(req, timeout=5)
        result = json.loads(response.read().decode())

        assert result["count"] >= 2, "Should have at least 2 branches now"
        print(f"   ✓ Total branches: {result['count']}")
        return True
    except Exception as e:
        print(f"   ✗ Multiple branches test failed: {e}")
        return False


def main():
    """Run all tests for conversation branching feature."""
    print("=" * 60)
    print("CONVERSATION BRANCHING TEST SUITE")
    print("Feature #48: Conversation branching creates alternative paths")
    print("=" * 60)

    results = []

    # Test 1: Backend health
    results.append(("Backend Health", test_backend_health()))

    if not results[-1][1]:
        print("\n❌ Backend not running - aborting tests")
        return

    # Test 2: Create conversation
    conversation_id, message_ids = test_create_conversation()
    if not conversation_id:
        print("\n❌ Failed to create conversation - aborting tests")
        return

    results.append(("Create Conversation", bool(conversation_id)))

    # Test 3: Create branch
    branch_id = test_create_branch(conversation_id, message_ids)
    results.append(("Create Branch", bool(branch_id)))

    if not branch_id:
        print("\n❌ Failed to create branch - aborting remaining tests")
        return

    # Test 4: Verify branch messages
    results.append(("Branch Messages", test_branch_messages(branch_id, 2)))

    # Test 5: Branch independence
    results.append(("Branch Independence", test_branch_independence(conversation_id, branch_id)))

    # Test 6: List branches
    results.append(("List Branches", test_list_branches(conversation_id)))

    # Test 7: Branch path
    results.append(("Branch Path", test_branch_path(branch_id)))

    # Test 8: Multiple branches
    results.append(("Multiple Branches", test_multiple_branches_from_same_point(conversation_id, message_ids)))

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result is True)
    failed = sum(1 for _, result in results if result is False)

    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")

    print(f"\nTotal: {passed} passed, {failed} failed")

    if passed == len(results):
        print("\n🎉 CONVERSATION BRANCHING FEATURE IS WORKING!")
    elif passed >= len(results) * 0.7:
        print("\n✓ Conversation branching feature is mostly working")
    else:
        print("\n❌ Conversation branching feature needs more work")

    print("=" * 60)


if __name__ == "__main__":
    main()
