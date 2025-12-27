"""Test conversation branching functionality."""

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.conversation import Conversation as ConversationModel
from src.models.message import Message as MessageModel


@pytest.mark.asyncio
async def test_create_branch_from_conversation(client, test_db):
    """Test creating a branch from a conversation."""
    # Create a conversation
    conversation_data = {
        "title": "Test Conversation",
        "model": "claude-sonnet-4-5-20250929"
    }

    response = await client.post("/api/conversations", json=conversation_data)
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
        msg_response = await client.post(f"/api/messages/conversations/{conversation_id}/messages", json=msg_data)
        assert msg_response.status_code == 201

    # Get the messages to find the branch point
    response = await client.get(f"/api/messages/conversations/{conversation_id}/messages")
    assert response.status_code == 200
    messages = response.json()

    # Create a branch from the second message (assistant's first response)
    branch_point_message_id = messages[1]["id"]
    branch_data = {
        "branch_name": "Alternative Response",
        "branch_color": "blue",
        "message_id": branch_point_message_id
    }

    response = await client.post(f"/api/conversations/{conversation_id}/branch", json=branch_data)
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


@pytest.mark.asyncio
async def test_list_branches(client, test_db):
    """Test listing all branches for a conversation."""
    # Create a conversation
    conversation_data = {"title": "Parent Conversation", "model": "claude-sonnet-4-5-20250929"}
    response = await client.post("/api/conversations", json=conversation_data)
    conversation_id = response.json()["id"]

    # Create some messages
    for i in range(3):
        msg_data = {"role": "user", "content": f"Message {i+1}"}
        await client.post(f"/api/messages/conversations/{conversation_id}/messages", json=msg_data)

    # Create multiple branches
    branches_data = [
        {"branch_name": "Branch 1", "branch_color": "red", "message_id": None},
        {"branch_name": "Branch 2", "branch_color": "green", "message_id": None},
        {"branch_name": "Branch 3", "branch_color": "blue", "message_id": None},
    ]

    messages_response = await client.get(f"/api/messages/conversations/{conversation_id}/messages")
    messages = messages_response.json()

    for i, branch_data in enumerate(branches_data):
        branch_data["message_id"] = messages[1]["id"]  # Branch from second message
        response = await client.post(f"/api/conversations/{conversation_id}/branch", json=branch_data)
        assert response.status_code == 200

    # List branches
    response = await client.get(f"/api/conversations/{conversation_id}/branches")
    assert response.status_code == 200

    branches = response.json()
    assert len(branches["branches"]) == 3

    # Verify branch details
    for i, branch in enumerate(branches["branches"]):
        assert branch["branch_name"] == f"Branch {i+1}"
        assert branch["parent_conversation_id"] == conversation_id
        assert branch["model"] == "claude-sonnet-4-5-20250929"


@pytest.mark.asyncio
async def test_branch_path(client, test_db):
    """Test getting the branch path from root to current."""
    # Create a root conversation
    conversation_data = {"title": "Root Conversation", "model": "claude-sonnet-4-5-20250929"}
    response = await client.post("/api/conversations", json=conversation_data)
    root_id = response.json()["id"]

    # Create messages
    for i in range(3):
        msg_data = {"role": "user", "content": f"Message {i+1}"}
        await client.post(f"/api/messages/conversations/{root_id}/messages", json=msg_data)

    # Create a branch
    messages_response = await client.get(f"/api/messages/conversations/{root_id}/messages")
    messages = messages_response.json()

    branch_data = {
        "branch_name": "First Branch",
        "branch_color": "red",
        "message_id": messages[1]["id"]
    }

    response = await client.post(f"/api/conversations/{root_id}/branch", json=branch_data)
    assert response.status_code == 200
    branch_info = response.json()
    branch_id = branch_info["id"]

    # Get branch path from root
    response = await client.get(f"/api/conversations/{root_id}/branch-path")
    assert response.status_code == 200
    path = response.json()
    assert len(path["branch_path"]) == 1
    assert path["is_branch"] == False

    # Get branch path from branch
    response = await client.get(f"/api/conversations/{branch_id}/branch-path")
    assert response.status_code == 200
    path = response.json()
    assert len(path["branch_path"]) == 2
    assert path["is_branch"] == True
    assert path["root_conversation_id"] == root_id


@pytest.mark.asyncio
async def test_switch_branch(client, test_db):
    """Test switching between branches."""
    # Create a root conversation
    conversation_data = {"title": "Root", "model": "claude-sonnet-4-5-20250929"}
    response = await client.post("/api/conversations", json=conversation_data)
    root_id = response.json()["id"]

    # Create messages
    for i in range(3):
        msg_data = {"role": "user", "content": f"Message {i+1}"}
        await client.post(f"/api/messages/conversations/{root_id}/messages", json=msg_data)

    # Get messages for branching
    messages_response = await client.get(f"/api/messages/conversations/{root_id}/messages")
    messages = messages_response.json()

    # Create two branches
    branch1_data = {"branch_name": "Branch A", "message_id": messages[1]["id"]}
    response1 = await client.post(f"/api/conversations/{root_id}/branch", json=branch1_data)
    branch1_id = response1.json()["id"]

    branch2_data = {"branch_name": "Branch B", "message_id": messages[1]["id"]}
    response2 = await client.post(f"/api/conversations/{root_id}/branch", json=branch2_data)
    branch2_id = response2.json()["id"]

    # Switch from branch1 to branch2
    switch_response = await client.put(
        f"/api/conversations/{branch1_id}/switch-to-branch/{branch2_id}"
    )
    assert switch_response.status_code == 200

    # Verify the switch worked
    result = switch_response.json()
    assert result["target_conversation"]["id"] == branch2_id
    assert result["switched_from"] == branch1_id
    assert result["switched_to"] == branch2_id


@pytest.mark.asyncio
async def test_branch_tree(client, test_db):
    """Test getting the branch tree structure."""
    # Create a root conversation
    conversation_data = {"title": "Root", "model": "claude-sonnet-4-5-20250929"}
    response = await client.post("/api/conversations", json=conversation_data)
    root_id = response.json()["id"]

    # Create messages
    for i in range(3):
        msg_data = {"role": "user", "content": f"Message {i+1}"}
        await client.post(f"/api/messages/conversations/{root_id}/messages", json=msg_data)

    # Create a branch
    messages_response = await client.get(f"/api/messages/conversations/{root_id}/messages")
    messages = messages_response.json()

    branch_data = {
        "branch_name": "First Branch",
        "branch_color": "red",
        "message_id": messages[1]["id"]
    }

    response = await client.post(f"/api/conversations/{root_id}/branch", json=branch_data)
    assert response.status_code == 200
    branch_info = response.json()
    branch_id = branch_info["id"]

    # Get branch tree from root
    response = await client.get(f"/api/conversations/{root_id}/branch-tree")
    assert response.status_code == 200

    tree = response.json()
    assert tree["root"]["id"] == root_id
    assert tree["current_conversation"]["id"] == root_id
    assert len(tree["branches"]) >= 1

    # Get branch tree from branch
    response = await client.get(f"/api/conversations/{branch_id}/branch-tree")
    assert response.status_code == 200

    branch_tree = response.json()
    assert branch_tree["root"]["id"] == root_id
    assert branch_tree["current_conversation"]["id"] == branch_id
