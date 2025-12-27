"""Test conversation branching functionality."""

import pytest
import json
from uuid import UUID
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.conversation import Conversation as ConversationModel
from src.models.message import Message as MessageModel
from src.models.artifact import Artifact as ArtifactModel
from src.core.database import get_db


async def test_create_branch_from_conversation(client, test_db):
    """Test creating a branch from a conversation."""
    # Create a conversation
    conversation_data = {
        "title": "Test Conversation",
        "model": "claude-sonnet-4-5-20250929"
    }

    response = client.post("/api/conversations", json=conversation_data)
    assert response.status_code == 201
    conversation_data = response.json()
    conversation_id = conversation_data["id"]

    # Create some messages in the conversation
    messages_data = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there!"},
        {"role": "user", "content": "How are you?"},
        {"role": "assistant", "content": "I'm doing well, thank you!"},
    ]

    for msg_data in messages_data:
        msg_response = client.post(f"/api/conversations/{conversation_id}/messages", json=msg_data)
        assert msg_response.status_code == 200

    # Get the messages to find the branch point
    response = client.get(f"/api/conversations/{conversation_id}/messages")
    assert response.status_code == 200
    messages = response.json()

    # Create a branch from the second message (assistant's first response)
    branch_point_message_id = messages[1]["id"]
    branch_data = {
        "branch_name": "Alternative Response",
        "branch_color": "blue",
        "message_id": branch_point_message_id
    }

    response = client.post(f"/api/conversations/{conversation_id}/branch", json=branch_data)
    assert response.status_code == 200

    branch_data_response = response.json()
    assert branch_data_response["branch_name"] == "Alternative Response"
    assert branch_data_response["branch_color"] == "blue"
    assert branch_data_response["parent_conversation_id"] == conversation_id
    assert branch_data_response["branch_point_message_id"] == branch_point_message_id

    # Verify the branch was created in the database
    branch_id = branch_data_response["id"]
    result = await test_db.execute(
        select(ConversationModel).where(ConversationModel.id == branch_id)
    )
    branch = result.scalar_one_or_none()
    assert branch is not None
    assert branch.parent_conversation_id == conversation_id
    assert branch.branch_point_message_id == branch_point_message_id
    assert branch.branch_name == "Alternative Response"

    # Verify messages were copied
    assert branch_data_response["message_count"] == 2  # First two messages should be copied


async def test_create_branch_from_specific_message(client, test_db):
    """Test creating a branch from different message positions."""
    # Create a conversation with multiple messages
    conversation_data = {"title": "Test Conversation", "model": "claude-sonnet-4-5-20250929"}
    response = client.post("/api/conversations", json=conversation_data)
    conversation_id = response.json()["id"]

    # Create messages
    messages_data = [
        {"role": "user", "content": "Message 1"},
        {"role": "assistant", "content": "Response 1"},
        {"role": "user", "content": "Message 2"},
        {"role": "assistant", "content": "Response 2"},
        {"role": "user", "content": "Message 3"},
        {"role": "assistant", "content": "Response 3"},
    ]

    message_ids = []
    for msg_data in messages_data:
        response = client.post(f"/api/conversations/{conversation_id}/messages", json=msg_data)
        message_ids.append(response.json()["id"])

    # Test branching from different positions
    test_cases = [
        (message_ids[0], 1),  # From first message (user)
        (message_ids[2], 3),  # From third message (user)
        (message_ids[4], 5),  # From fifth message (user)
    ]

    for branch_point_id, expected_message_count in test_cases:
        branch_data = {
            "branch_name": f"Branch from message {branch_point_id}",
            "message_id": branch_point_id
        }

        response = client.post(f"/api/conversations/{conversation_id}/branch", json=branch_data)
        assert response.status_code == 200

        branch_info = response.json()
        assert branch_info["message_count"] == expected_message_count

        # Verify all messages up to and including the branch point were copied
        branch_messages_response = client.get(f"/api/conversations/{branch_info['id']}/messages")
        assert branch_messages_response.status_code == 200
        branch_messages = branch_messages_response.json()
        assert len(branch_messages) == expected_message_count


async def test_create_branch_with_existing_artifacts(client, test_db):
    """Test creating a branch when the parent conversation has artifacts."""
    # Create conversation and messages
    conversation_data = {"title": "Test with Artifacts", "model": "claude-sonnet-4-5-20250929"}
    response = client.post("/api/conversations", json=conversation_data)
    conversation_id = response.json()["id"]

    # Create messages
    for i in range(3):
        msg_data = {"role": "user", "content": f"Message {i+1}"}
        client.post(f"/api/conversations/{conversation_id}/messages", json=msg_data)

    # Create an artifact in the parent conversation
    artifact_data = {
        "title": "Test Artifact",
        "content": "This is test code",
        "language": "python",
        "artifact_type": "code"
    }
    response = client.post(f"/api/conversations/{conversation_id}/artifacts", json=artifact_data)
    assert response.status_code == 200
    artifact_id = response.json()["id"]

    # Create a branch
    branch_data = {
        "branch_name": "Branch with Artifacts",
        "message_id": "message-id-2"  # This should be a real message ID
    }

    # First get the actual message IDs
    messages_response = client.get(f"/api/conversations/{conversation_id}/messages")
    messages = messages_response.json()
    branch_data["message_id"] = messages[1]["id"]

    response = client.post(f"/api/conversations/{conversation_id}/branch", json=branch_data)
    assert response.status_code == 200

    branch_info = response.json()
    branch_id = branch_info["id"]

    # Verify the branch was created
    assert branch_info["branch_name"] == "Branch with Artifacts"

    # Note: Artifacts are not copied to branches by design, as they are conversation-specific
    # This is the expected behavior


async def test_list_branches(client, test_db):
    """Test listing all branches for a conversation."""
    # Create a conversation
    conversation_data = {"title": "Parent Conversation", "model": "claude-sonnet-4-5-20250929"}
    response = client.post("/api/conversations", json=conversation_data)
    conversation_id = response.json()["id"]

    # Create some messages
    for i in range(3):
        msg_data = {"role": "user", "content": f"Message {i+1}"}
        client.post(f"/api/conversations/{conversation_id}/messages", json=msg_data)

    # Create multiple branches
    branches_data = [
        {"branch_name": "Branch 1", "branch_color": "red", "message_id": None},
        {"branch_name": "Branch 2", "branch_color": "green", "message_id": None},
        {"branch_name": "Branch 3", "branch_color": "blue", "message_id": None},
    ]

    messages_response = client.get(f"/api/conversations/{conversation_id}/messages")
    messages = messages_response.json()

    for i, branch_data in enumerate(branches_data):
        branch_data["message_id"] = messages[1]["id"]  # Branch from second message
        response = client.post(f"/api/conversations/{conversation_id}/branch", json=branch_data)
        assert response.status_code == 200

    # List branches
    response = client.get(f"/api/conversations/{conversation_id}/branches")
    assert response.status_code == 200

    branches = response.json()
    assert len(branches["branches"]) == 3

    # Verify branch details
    for i, branch in enumerate(branches["branches"]):
        assert branch["branch_name"] == f"Branch {i+1}"
        assert branch["parent_conversation_id"] == conversation_id
        assert branch["model"] == "claude-sonnet-4-5-20250929"


async def test_get_branch_tree(client, test_db):
    """Test getting the branch tree structure."""
    # Create a conversation
    conversation_data = {"title": "Root Conversation", "model": "claude-sonnet-4-5-20250929"}
    response = client.post("/api/conversations", json=conversation_data)
    conversation_id = response.json()["id"]

    # Create messages
    for i in range(3):
        msg_data = {"role": "user", "content": f"Message {i+1}"}
        client.post(f"/api/conversations/{conversation_id}/messages", json=msg_data)

    # Create a branch
    messages_response = client.get(f"/api/conversations/{conversation_id}/messages")
    messages = messages_response.json()

    branch_data = {
        "branch_name": "First Branch",
        "branch_color": "red",
        "message_id": messages[1]["id"]
    }

    response = client.post(f"/api/conversations/{conversation_id}/branch", json=branch_data)
    assert response.status_code == 200
    branch_info = response.json()
    branch_id = branch_info["id"]

    # Get branch tree from root conversation
    response = client.get(f"/api/conversations/{conversation_id}/branch-tree")
    assert response.status_code == 200

    tree = response.json()
    assert "root" in tree
    assert "branches" in tree
    assert "current_conversation" in tree

    assert tree["root"]["id"] == conversation_id
    assert tree["current_conversation"]["id"] == conversation_id
    assert len(tree["branches"]) == 1
    assert tree["branches"][0]["id"] == branch_id
    assert tree["branches"][0]["branch_name"] == "First Branch"

    # Get branch tree from branch conversation
    response = client.get(f"/api/conversations/{branch_id}/branch-tree")
    assert response.status_code == 200

    branch_tree = response.json()
    assert branch_tree["root"]["id"] == conversation_id  # Root should be the original conversation
    assert branch_tree["current_conversation"]["id"] == branch_id


async def test_create_branch_error_cases(client, test_db):
    """Test error cases for branch creation."""
    # Test creating branch from non-existent conversation
    branch_data = {
        "branch_name": "Test Branch",
        "message_id": "non-existent-message-id"
    }

    response = client.post("/api/conversations/non-existent-id/branch", json=branch_data)
    assert response.status_code == 404
    assert "Parent conversation not found" in response.json()["detail"]

    # Test creating branch from non-existent message
    conversation_data = {"title": "Test", "model": "claude-sonnet-4-5-20250929"}
    response = client.post("/api/conversations", json=conversation_data)
    conversation_id = response.json()["id"]

    branch_data = {
        "branch_name": "Test Branch",
        "message_id": "non-existent-message-id"
    }

    response = client.post(f"/api/conversations/{conversation_id}/branch", json=branch_data)
    assert response.status_code == 404
    assert "Branch point message not found" in response.json()["detail"]

    # Test creating branch with message from different conversation
    conversation_data2 = {"title": "Another Conversation", "model": "claude-sonnet-4-5-20250929"}
    response = client.post("/api/conversations", json=conversation_data2)
    conversation_id2 = response.json()["id"]

    # Create a message in the second conversation
    msg_data = {"role": "user", "content": "Test message"}
    response = client.post(f"/api/conversations/{conversation_id2}/messages", json=msg_data)
    message_id = response.json()["id"]

    # Try to branch from the second conversation's message in the first conversation
    branch_data = {
        "branch_name": "Invalid Branch",
        "message_id": message_id
    }

    response = client.post(f"/api/conversations/{conversation_id}/branch", json=branch_data)
    assert response.status_code == 400
    assert "does not belong to this conversation" in response.json()["detail"]


async def test_branch_validation(client, test_db):
    """Test branch validation and edge cases."""
    # Create a conversation
    conversation_data = {"title": "Test Conversation", "model": "claude-sonnet-4-5-20250929"}
    response = client.post("/api/conversations", json=conversation_data)
    conversation_id = response.json()["id"]

    # Create a message
    msg_data = {"role": "user", "content": "Test message"}
    response = client.post(f"/api/conversations/{conversation_id}/messages", json=msg_data)
    message_id = response.json()["id"]

    # Test with empty branch name
    branch_data = {
        "branch_name": "",
        "message_id": message_id
    }

    response = client.post(f"/api/conversations/{conversation_id}/branch", json=branch_data)
    assert response.status_code == 422  # Validation error

    # Test with too long branch name
    branch_data = {
        "branch_name": "a" * 101,  # Exceeds max_length=100
        "message_id": message_id
    }

    response = client.post(f"/api/conversations/{conversation_id}/branch", json=branch_data)
    assert response.status_code == 422  # Validation error

    # Test with valid data
    branch_data = {
        "branch_name": "Valid Branch Name",
        "message_id": message_id
    }

    response = client.post(f"/api/conversations/{conversation_id}/branch", json=branch_data)
    assert response.status_code == 200

    branch_info = response.json()
    assert branch_info["branch_name"] == "Valid Branch Name"


async def test_branch_point_message_marking(client, test_db):
    """Test that branch point messages are properly marked."""
    # Create a conversation with messages
    conversation_data = {"title": "Test Conversation", "model": "claude-sonnet-4-5-20250929"}
    response = client.post("/api/conversations", json=conversation_data)
    conversation_id = response.json()["id"]

    messages_data = [
        {"role": "user", "content": "Message 1"},
        {"role": "assistant", "content": "Response 1"},
        {"role": "user", "content": "Message 2"},
    ]

    message_ids = []
    for msg_data in messages_data:
        response = client.post(f"/api/conversations/{conversation_id}/messages", json=msg_data)
        message_ids.append(response.json()["id"])

    # Create a branch
    branch_data = {
        "branch_name": "Test Branch",
        "message_id": message_ids[1]  # Branch from second message
    }

    response = client.post(f"/api/conversations/{conversation_id}/branch", json=branch_data)
    assert response.status_code == 200

    # Verify the branch point message is marked
    result = await test_db.execute(
        select(MessageModel).where(MessageModel.id == message_ids[1])
    )
    message = result.scalar_one()
    assert message.is_branch_point == True

    # Verify the branch was created with correct metadata
    branch_info = response.json()
    assert branch_info["branch_point_message_id"] == message_ids[1]
    assert branch_info["parent_conversation_id"] == conversation_id


async def test_branch_message_content_preservation(client, test_db):
    """Test that message content is properly preserved when branching."""
    # Create a conversation with rich content
    conversation_data = {"title": "Test Conversation", "model": "claude-sonnet-4-5-20250929"}
    response = client.post("/api/conversations", json=conversation_data)
    conversation_id = response.json()["id"]

    rich_message_data = {
        "role": "user",
        "content": "This is a test message with **markdown** and `code`",
        "attachments": ["image1.jpg", "image2.png"],
        "input_tokens": 50,
        "output_tokens": 0,
        "cache_read_tokens": 10,
        "cache_write_tokens": 5
    }

    response = client.post(f"/api/conversations/{conversation_id}/messages", json=rich_message_data)
    assert response.status_code == 200
    original_message_id = response.json()["id"]

    # Create a branch
    branch_data = {
        "branch_name": "Rich Content Branch",
        "message_id": original_message_id
    }

    response = client.post(f"/api/conversations/{conversation_id}/branch", json=branch_data)
    assert response.status_code == 200

    branch_info = response.json()
    branch_id = branch_info["id"]

    # Get messages from the branch
    response = client.get(f"/api/conversations/{branch_id}/messages")
    assert response.status_code == 200

    branch_messages = response.json()
    assert len(branch_messages) == 1

    branch_message = branch_messages[0]
    assert branch_message["content"] == rich_message_data["content"]
    assert branch_message["role"] == rich_message_data["role"]
    assert branch_message["attachments"] == rich_message_data["attachments"]
    assert branch_message["input_tokens"] == rich_message_data["input_tokens"]
    assert branch_message["output_tokens"] == rich_message_data["output_tokens"]
    assert branch_message["cache_read_tokens"] == rich_message_data["cache_read_tokens"]
    assert branch_message["cache_write_tokens"] == rich_message_data["cache_write_tokens"]


async def test_multiple_branches_from_same_message(client, test_db):
    """Test creating multiple branches from the same message."""
    # Create a conversation
    conversation_data = {"title": "Test Conversation", "model": "claude-sonnet-4-5-20250929"}
    response = client.post("/api/conversations", json=conversation_data)
    conversation_id = response.json()["id"]

    # Create messages
    for i in range(3):
        msg_data = {"role": "user", "content": f"Message {i+1}"}
        client.post(f"/api/conversations/{conversation_id}/messages", json=msg_data)

    # Get the middle message to branch from
    messages_response = client.get(f"/api/conversations/{conversation_id}/messages")
    messages = messages_response.json()
    branch_point_message_id = messages[1]["id"]

    # Create multiple branches from the same message
    branches_data = [
        {"branch_name": "Branch A", "branch_color": "red"},
        {"branch_name": "Branch B", "branch_color": "green"},
        {"branch_name": "Branch C", "branch_color": "blue"},
    ]

    created_branches = []
    for branch_data in branches_data:
        branch_data["message_id"] = branch_point_message_id
        response = client.post(f"/api/conversations/{conversation_id}/branch", json=branch_data)
        assert response.status_code == 200
        created_branches.append(response.json())

    # Verify all branches were created
    assert len(created_branches) == 3

    for i, branch in enumerate(created_branches):
        assert branch["branch_name"] == branches_data[i]["branch_name"]
        assert branch["branch_color"] == branches_data[i]["branch_color"]
        assert branch["parent_conversation_id"] == conversation_id
        assert branch["branch_point_message_id"] == branch_point_message_id

        # Each branch should have the same number of messages (up to branch point)
        assert branch["message_count"] == 2

    # List branches to verify they all exist
    response = client.get(f"/api/conversations/{conversation_id}/branches")
    assert response.status_code == 200

    branches = response.json()
    assert len(branches) == 3


async def test_branch_tree_with_nested_branches(client, test_db):
    """Test branch tree structure with nested branches."""
    # Create root conversation
    conversation_data = {"title": "Root", "model": "claude-sonnet-4-5-20250929"}
    response = client.post("/api/conversations", json=conversation_data)
    root_id = response.json()["id"]

    # Add messages to root
    for i in range(3):
        msg_data = {"role": "user", "content": f"Root message {i+1}"}
        client.post(f"/api/conversations/{root_id}/messages", json=msg_data)

    # Create first branch from root
    messages_response = client.get(f"/api/conversations/{root_id}/messages")
    messages = messages_response.json()

    branch1_data = {
        "branch_name": "Branch 1",
        "message_id": messages[1]["id"]
    }

    response = client.post(f"/api/conversations/{root_id}/branch", json=branch1_data)
    assert response.status_code == 200
    branch1_id = response.json()["id"]

    # Add messages to first branch
    for i in range(2):
        msg_data = {"role": "user", "content": f"Branch 1 message {i+1}"}
        client.post(f"/api/conversations/{branch1_id}/messages", json=msg_data)

    # Create second branch from first branch
    branch1_messages_response = client.get(f"/api/conversations/{branch1_id}/messages")
    branch1_messages = branch1_messages_response.json()

    branch2_data = {
        "branch_name": "Branch 2",
        "message_id": branch1_messages[2]["id"]  # Branch from second message in branch 1
    }

    response = client.post(f"/api/conversations/{branch1_id}/branch", json=branch2_data)
    assert response.status_code == 200
    branch2_id = response.json()["id"]

    # Get branch tree from root
    response = client.get(f"/api/conversations/{root_id}/branch-tree")
    assert response.status_code == 200

    tree = response.json()
    assert tree["root"]["id"] == root_id
    assert len(tree["branches"]) == 2  # Should include both branches

    # Get branch tree from first branch
    response = client.get(f"/api/conversations/{branch1_id}/branch-tree")
    assert response.status_code == 200

    branch1_tree = response.json()
    assert branch1_tree["root"]["id"] == root_id
    assert branch1_tree["current_conversation"]["id"] == branch1_id
    assert len(branch1_tree["branches"]) == 1  # Should include branch 2

    # Get branch tree from second branch
    response = client.get(f"/api/conversations/{branch2_id}/branch-tree")
    assert response.status_code == 200

    branch2_tree = response.json()
    assert branch2_tree["root"]["id"] == root_id
    assert branch2_tree["current_conversation"]["id"] == branch2_id
    assert len(branch2_tree["branches"]) == 0  # No further branches