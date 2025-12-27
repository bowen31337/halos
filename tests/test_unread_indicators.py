"""Test the unread message indicators feature."""
import pytest
from httpx import AsyncClient
import json


@pytest.mark.asyncio
async def test_unread_message_indicators_backend(async_client: AsyncClient):
    """Test that the backend properly handles unread message indicators."""

    # 1. Create a conversation
    response = await async_client.post("/api/conversations", json={
        "title": "Test Conversation for Unread",
        "model": "claude-sonnet-4-5-20250929"
    })
    assert response.status_code == 201
    conversation = response.json()
    conversation_id = conversation["id"]

    # 2. Verify initial unread count is 0
    assert conversation["unread_count"] == 0

    # 3. Increment unread count via mark-unread endpoint
    response = await async_client.post(f"/api/conversations/{conversation_id}/mark-unread")
    assert response.status_code == 200
    result = response.json()
    assert result["unread_count"] == 1

    # 4. Verify conversation list includes unread count
    response = await async_client.get("/api/conversations")
    assert response.status_code == 200
    conversations = response.json()
    test_conv = next((c for c in conversations if c["id"] == conversation_id), None)
    assert test_conv is not None
    assert test_conv["unread_count"] == 1

    # 5. Mark as read
    response = await async_client.post(f"/api/conversations/{conversation_id}/mark-read")
    assert response.status_code == 200
    result = response.json()
    assert result["unread_count"] == 0

    # 6. Verify conversation list shows 0 unread
    response = await async_client.get("/api/conversations")
    assert response.status_code == 200
    conversations = response.json()
    test_conv = next((c for c in conversations if c["id"] == conversation_id), None)
    assert test_conv is not None
    assert test_conv["unread_count"] == 0

    print("✓ Backend unread indicators working correctly!")


@pytest.mark.asyncio
async def test_unread_count_increments_on_assistant_message(async_client: AsyncClient):
    """Test that unread count increments when assistant messages are added."""

    # 1. Create a conversation
    response = await async_client.post("/api/conversations", json={
        "title": "Test Conversation for Assistant Messages",
        "model": "claude-sonnet-4-5-20250929"
    })
    assert response.status_code == 201
    conversation = response.json()
    conversation_id = conversation["id"]

    # 2. Add a user message (should not increment unread)
    response = await async_client.post(f"/api/conversations/{conversation_id}/messages", json={
        "role": "user",
        "content": "Hello",
        "attachments": [],
        "tool_calls": {},
        "tool_results": {},
        "thinking_content": ""
    })
    assert response.status_code == 201

    # 3. Verify unread count is still 0
    response = await async_client.get(f"/api/conversations/{conversation_id}")
    assert response.status_code == 200
    conv_data = response.json()
    assert conv_data["unread_count"] == 0

    # 4. Add an assistant message (should increment unread)
    response = await async_client.post(f"/api/conversations/{conversation_id}/messages", json={
        "role": "assistant",
        "content": "Hi there!",
        "attachments": [],
        "tool_calls": {},
        "tool_results": {},
        "thinking_content": ""
    })
    assert response.status_code == 201

    # 5. Verify unread count is now 1
    response = await async_client.get(f"/api/conversations/{conversation_id}")
    assert response.status_code == 200
    conv_data = response.json()
    assert conv_data["unread_count"] == 1

    print("✓ Unread count increments on assistant messages!")


@pytest.mark.asyncio
async def test_frontend_conversation_type_includes_unread_count():
    """Test that the frontend Conversation type includes unreadCount."""

    # Check the TypeScript type file
    import os
    type_file = "client/src/stores/conversationStore.ts"

    assert os.path.exists(type_file), f"Type file not found at {type_file}"

    with open(type_file, 'r') as f:
        content = f.read()

    # Check that the Conversation interface includes unreadCount
    assert 'unreadCount: number' in content, "Frontend Conversation type missing unreadCount field"

    print("✓ Frontend Conversation type includes unreadCount!")


def test_sidebar_component_includes_unread_indicator():
    """Test that the Sidebar component includes unread indicator UI."""

    import os
    sidebar_file = "client/src/components/Sidebar.tsx"

    assert os.path.exists(sidebar_file), f"Sidebar component not found at {sidebar_file}"

    with open(sidebar_file, 'r') as f:
        content = f.read()

    # Check for unread indicator elements in the ConversationItem component
    assert 'conv.unreadCount > 0' in content, "Sidebar missing unread count condition"
    assert 'bg-[var(--primary)] rounded-full' in content, "Sidebar missing unread indicator dot"
    assert 'text-xs text-[var(--text-secondary)]' in content, "Sidebar missing unread count text"

    print("✓ Sidebar component includes unread indicator UI!")


@pytest.mark.asyncio
async def test_complete_unread_flow(async_client: AsyncClient):
    """Test the complete unread message flow."""

    # 1. Create conversation
    response = await async_client.post("/api/conversations", json={
        "title": "Complete Flow Test",
        "model": "claude-sonnet-4-5-20250929"
    })
    assert response.status_code == 201
    conversation = response.json()
    conversation_id = conversation["id"]

    # 2. Add assistant message (creates unread)
    response = await async_client.post(f"/api/conversations/{conversation_id}/messages", json={
        "role": "assistant",
        "content": "Test response",
        "attachments": [],
        "tool_calls": {},
        "tool_results": {},
        "thinking_content": ""
    })
    assert response.status_code == 201

    # 3. Verify unread count is 1
    response = await async_client.get(f"/api/conversations/{conversation_id}")
    assert response.status_code == 200
    conv_data = response.json()
    assert conv_data["unread_count"] == 1

    # 4. Mark as read
    response = await async_client.post(f"/api/conversations/{conversation_id}/mark-read")
    assert response.status_code == 200

    # 5. Verify unread count is 0
    response = await async_client.get(f"/api/conversations/{conversation_id}")
    assert response.status_code == 200
    conv_data = response.json()
    assert conv_data["unread_count"] == 0

    print("✓ Complete unread message flow working!")


if __name__ == "__main__":
    print("Run tests with: pytest tests/test_unread_indicators.py -v")