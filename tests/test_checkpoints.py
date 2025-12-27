"""Test checkpoint functionality."""

import pytest
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.conversation import Conversation as ConversationModel
from src.models.message import Message as MessageModel
from src.models.artifact import Artifact as ArtifactModel
from src.models.checkpoint import Checkpoint as CheckpointModel
from src.core.database import get_db


@pytest.mark.asyncio
async def test_create_checkpoint(client, test_db):
    """Test creating a checkpoint for a conversation."""
    # Create a conversation
    conversation_data = {
        "title": "Test Conversation",
        "model": "claude-sonnet-4-5-20250929"
    }
    response = await client.post("/api/conversations", json=conversation_data)
    assert response.status_code == 201
    conversation = response.json()
    conversation_id = conversation["id"]

    # Add some messages
    messages_data = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there!"},
        {"role": "user", "content": "How are you?"},
    ]
    for msg_data in messages_data:
        await client.post(f"/api/messages/conversations/{conversation_id}/messages", json=msg_data)

    # Create a checkpoint
    checkpoint_data = {
        "name": "Test Checkpoint",
        "notes": "Before major change"
    }
    response = await client.post(
        f"/api/conversations/{conversation_id}/checkpoints",
        json=checkpoint_data
    )
    assert response.status_code == 201
    checkpoint = response.json()

    # Verify checkpoint structure
    assert "id" in checkpoint
    assert checkpoint["conversation_id"] == conversation_id
    assert checkpoint["name"] == "Test Checkpoint"
    assert checkpoint["notes"] == "Before major change"
    assert "state_snapshot" in checkpoint
    assert "created_at" in checkpoint
    assert "updated_at" in checkpoint

    # Verify state snapshot contains messages
    state_snapshot = checkpoint["state_snapshot"]
    assert "messages" in state_snapshot
    assert len(state_snapshot["messages"]) == 3
    assert state_snapshot["messages"][0]["content"] == "Hello"
    assert state_snapshot["messages"][0]["role"] == "user"

    # Verify conversation metadata is captured
    assert "conversation_metadata" in state_snapshot
    assert state_snapshot["conversation_metadata"]["title"] == "Test Conversation"


@pytest.mark.asyncio
async def test_create_checkpoint_with_artifacts(client, test_db):
    """Test creating a checkpoint that includes artifacts."""
    # Create conversation and add messages
    conversation_data = {"title": "Test", "model": "claude-sonnet-4-5-20250929"}
    response = await client.post("/api/conversations", json=conversation_data)
    conversation_id = response.json()["id"]

    await client.post(f"/api/messages/conversations/{conversation_id}/messages",
                     json={"role": "user", "content": "Create code"})

    # Create an artifact
    artifact_data = {
        "conversation_id": conversation_id,
        "content": "def hello(): pass",
        "title": "test.py",
        "language": "python"
    }
    artifact_response = await client.post("/api/artifacts/create", json=artifact_data)
    assert artifact_response.status_code == 201

    # Create checkpoint
    response = await client.post(
        f"/api/conversations/{conversation_id}/checkpoints",
        json={"name": "With Artifact"}
    )
    assert response.status_code == 201
    checkpoint = response.json()

    # Verify artifact is in snapshot
    artifacts = checkpoint["state_snapshot"]["artifacts"]
    assert len(artifacts) == 1
    assert artifacts[0]["title"] == "test.py"
    assert artifacts[0]["content"] == "def hello(): pass"


@pytest.mark.asyncio
async def test_list_checkpoints(client, test_db):
    """Test listing all checkpoints for a conversation."""
    # Create conversation
    conversation_data = {"title": "Test", "model": "claude-sonnet-4-5-20250929"}
    response = await client.post("/api/conversations", json=conversation_data)
    conversation_id = response.json()["id"]

    # Create multiple checkpoints
    for i in range(3):
        await client.post(
            f"/api/conversations/{conversation_id}/checkpoints",
            json={"name": f"Checkpoint {i}"}
        )

    # List checkpoints
    response = await client.get(f"/api/conversations/{conversation_id}/checkpoints")
    assert response.status_code == 200
    checkpoints = response.json()

    assert len(checkpoints) == 3
    # Should be ordered by created_at descending
    assert checkpoints[0]["name"] == "Checkpoint 2"
    assert checkpoints[2]["name"] == "Checkpoint 0"


@pytest.mark.asyncio
async def test_get_checkpoint(client, test_db):
    """Test getting a specific checkpoint."""
    # Create conversation and checkpoint
    conversation_data = {"title": "Test", "model": "claude-sonnet-4-5-20250929"}
    response = await client.post("/api/conversations", json=conversation_data)
    conversation_id = response.json()["id"]

    response = await client.post(
        f"/api/conversations/{conversation_id}/checkpoints",
        json={"name": "Test", "notes": "Test notes"}
    )
    checkpoint_id = response.json()["id"]

    # Get checkpoint
    response = await client.get(f"/api/checkpoints/{checkpoint_id}")
    assert response.status_code == 200
    checkpoint = response.json()

    assert checkpoint["id"] == checkpoint_id
    assert checkpoint["name"] == "Test"
    assert checkpoint["notes"] == "Test notes"


@pytest.mark.asyncio
async def test_update_checkpoint(client, test_db):
    """Test updating a checkpoint."""
    # Create conversation and checkpoint
    conversation_data = {"title": "Test", "model": "claude-sonnet-4-5-20250929"}
    response = await client.post("/api/conversations", json=conversation_data)
    conversation_id = response.json()["id"]

    response = await client.post(
        f"/api/conversations/{conversation_id}/checkpoints",
        json={"name": "Original"}
    )
    checkpoint_id = response.json()["id"]

    # Update checkpoint
    update_data = {"name": "Updated", "notes": "New notes"}
    response = await client.put(f"/api/checkpoints/{checkpoint_id}", json=update_data)
    assert response.status_code == 200
    checkpoint = response.json()

    assert checkpoint["name"] == "Updated"
    assert checkpoint["notes"] == "New notes"


@pytest.mark.asyncio
async def test_restore_checkpoint(client, test_db):
    """Test restoring a conversation to a checkpoint."""
    # Create conversation
    conversation_data = {"title": "Test", "model": "claude-sonnet-4-5-20250929"}
    response = await client.post("/api/conversations", json=conversation_data)
    conversation_id = response.json()["id"]

    # Add 3 messages first
    messages = [
        {"role": "user", "content": "Msg 1"},
        {"role": "assistant", "content": "Resp 1"},
        {"role": "user", "content": "Msg 2"},
    ]
    for msg in messages:
        await client.post(f"/api/messages/conversations/{conversation_id}/messages", json=msg)

    # Create checkpoint after 3 messages
    response = await client.post(
        f"/api/conversations/{conversation_id}/checkpoints",
        json={"name": "After 3 messages"}
    )
    checkpoint_id = response.json()["id"]

    # Add more messages (2 more)
    await client.post(f"/api/messages/conversations/{conversation_id}/messages",
                     json={"role": "assistant", "content": "Resp 2"})
    await client.post(f"/api/messages/conversations/{conversation_id}/messages",
                     json={"role": "user", "content": "Msg 3"})

    # Verify we have 5 messages now (3 original + 2 added)
    response = await client.get(f"/api/messages/conversations/{conversation_id}/messages")
    assert len(response.json()) == 5

    # Restore checkpoint
    response = await client.post(f"/api/checkpoints/{checkpoint_id}/restore")
    assert response.status_code == 200
    result = response.json()

    assert result["status"] == "restored"
    assert result["restored_message_count"] == 3
    assert result["deleted_message_count"] == 2

    # Verify messages were restored
    response = await client.get(f"/api/messages/conversations/{conversation_id}/messages")
    messages_after_restore = response.json()
    assert len(messages_after_restore) == 3
    assert messages_after_restore[0]["content"] == "Msg 1"
    assert messages_after_restore[2]["content"] == "Msg 2"


@pytest.mark.asyncio
async def test_delete_checkpoint(client, test_db):
    """Test deleting a checkpoint."""
    # Create conversation and checkpoint
    conversation_data = {"title": "Test", "model": "claude-sonnet-4-5-20250929"}
    response = await client.post("/api/conversations", json=conversation_data)
    conversation_id = response.json()["id"]

    response = await client.post(
        f"/api/conversations/{conversation_id}/checkpoints",
        json={"name": "To Delete"}
    )
    checkpoint_id = response.json()["id"]

    # Delete checkpoint
    response = await client.delete(f"/api/checkpoints/{checkpoint_id}")
    assert response.status_code == 204

    # Verify it's gone
    response = await client.get(f"/api/checkpoints/{checkpoint_id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_checkpoint_nonexistent_conversation(client, test_db):
    """Test creating checkpoint for non-existent conversation."""
    response = await client.post(
        "/api/conversations/00000000-0000-0000-0000-000000000000/checkpoints",
        json={"name": "Test"}
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_restore_nonexistent_checkpoint(client, test_db):
    """Test restoring non-existent checkpoint."""
    response = await client.post(
        "/api/checkpoints/00000000-0000-0000-0000-000000000000/restore"
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_checkpoint_with_default_name(client, test_db):
    """Test checkpoint creation with auto-generated name."""
    # Create conversation
    conversation_data = {"title": "Test", "model": "claude-sonnet-4-5-20250929"}
    response = await client.post("/api/conversations", json=conversation_data)
    conversation_id = response.json()["id"]

    # Create checkpoint without name
    response = await client.post(
        f"/api/conversations/{conversation_id}/checkpoints",
        json={}
    )
    assert response.status_code == 201
    checkpoint = response.json()

    # Should have auto-generated name
    assert "Checkpoint" in checkpoint["name"]
    assert checkpoint["notes"] is None


@pytest.mark.asyncio
async def test_multiple_checkpoints_same_conversation(client, test_db):
    """Test creating multiple checkpoints for the same conversation."""
    # Create conversation
    conversation_data = {"title": "Test", "model": "claude-sonnet-4-5-20250929"}
    response = await client.post("/api/conversations", json=conversation_data)
    conversation_id = response.json()["id"]

    # Add 2 initial messages
    for i in range(2):
        await client.post(f"/api/messages/conversations/{conversation_id}/messages",
                         json={"role": "user", "content": f"Message {i}"})

    # Create checkpoints at different points
    checkpoints = []
    for i in range(3):
        response = await client.post(
            f"/api/conversations/{conversation_id}/checkpoints",
            json={"name": f"CP {i}", "notes": f"After {i+1} messages"}
        )
        checkpoints.append(response.json())

        # Add one more message after each checkpoint (except last)
        if i < 2:
            await client.post(f"/api/messages/conversations/{conversation_id}/messages",
                             json={"role": "assistant", "content": f"Response {i}"})

    # Verify all checkpoints exist
    response = await client.get(f"/api/conversations/{conversation_id}/checkpoints")
    assert response.status_code == 200
    all_checkpoints = response.json()
    assert len(all_checkpoints) == 3

    # Verify each checkpoint has correct message count (API returns newest first)
    # all_checkpoints[0] = checkpoint 2 (4 messages)
    # all_checkpoints[1] = checkpoint 1 (3 messages)
    # all_checkpoints[2] = checkpoint 0 (2 messages)
    for i, cp in enumerate(all_checkpoints):
        msg_count = len(cp["state_snapshot"]["messages"])
        assert msg_count == 4 - i  # Newest checkpoint has 4, then 3, then 2


@pytest.mark.asyncio
async def test_checkpoint_preserves_conversation_metadata(client, test_db):
    """Test that checkpoint preserves all conversation metadata."""
    # Create conversation with specific settings
    conversation_data = {
        "title": "Original Title",
        "model": "claude-opus-4-1-20250805"
    }
    response = await client.post("/api/conversations", json=conversation_data)
    conversation_id = response.json()["id"]

    # Add a message
    await client.post(f"/api/messages/conversations/{conversation_id}/messages",
                     json={"role": "user", "content": "Test"})

    # Create checkpoint
    response = await client.post(
        f"/api/conversations/{conversation_id}/checkpoints",
        json={"name": "Metadata Test"}
    )
    checkpoint = response.json()

    # Verify metadata
    metadata = checkpoint["state_snapshot"]["conversation_metadata"]
    assert metadata["title"] == "Original Title"
    assert metadata["model"] == "claude-opus-4-1-20250805"
