"""Test the conversation tags/labels feature."""
import pytest
from httpx import AsyncClient
import json


@pytest.mark.asyncio
async def test_conversation_tags_backend(async_client: AsyncClient):
    """Test that the backend properly handles conversation tags."""

    # 1. Create some tags
    tag1_response = await async_client.post("/api/tags", json={
        "name": "Important",
        "color": "#ef4444"
    })
    assert tag1_response.status_code == 201
    tag1 = tag1_response.json()

    tag2_response = await async_client.post("/api/tags", json={
        "name": "Work",
        "color": "#3b82f6"
    })
    assert tag2_response.status_code == 201
    tag2 = tag2_response.json()

    # 2. Verify tags can be listed
    response = await async_client.get("/api/tags")
    assert response.status_code == 200
    tags = response.json()
    assert len(tags) >= 2
    assert any(tag["name"] == "Important" for tag in tags)
    assert any(tag["name"] == "Work" for tag in tags)

    # 3. Create a conversation
    response = await async_client.post("/api/conversations", json={
        "title": "Test Conversation for Tags",
        "model": "claude-sonnet-4-5-20250929"
    })
    assert response.status_code == 201
    conversation = response.json()
    conversation_id = conversation["id"]

    # 4. Verify conversation initially has no tags
    assert len(conversation["tags"]) == 0

    # 5. Add tags to conversation
    response = await async_client.post(f"/api/conversations/{conversation_id}/tags", json={
        "tag_ids": [tag1["id"], tag2["id"]]
    })
    assert response.status_code == 200
    result = response.json()
    assert len(result["tags"]) == 2
    assert result["tag_ids"] == [tag1["id"], tag2["id"]]

    # 6. Verify conversation list includes tags
    response = await async_client.get("/api/conversations")
    assert response.status_code == 200
    conversations = response.json()
    test_conv = next((c for c in conversations if c["id"] == conversation_id), None)
    assert test_conv is not None
    assert len(test_conv["tags"]) == 2
    assert any(tag["name"] == "Important" for tag in test_conv["tags"])
    assert any(tag["name"] == "Work" for tag in test_conv["tags"])

    print("✓ Backend conversation tags working correctly!")


@pytest.mark.asyncio
async def test_tag_filtering(async_client: AsyncClient):
    """Test conversation filtering by tags."""

    # 1. Create tags
    tag1_response = await async_client.post("/api/tags", json={
        "name": "TestTag1",
        "color": "#10b981"
    })
    tag1 = tag1_response.json()

    tag2_response = await async_client.post("/api/tags", json={
        "name": "TestTag2",
        "color": "#f59e0b"
    })
    tag2 = tag2_response.json()

    # 2. Create conversations with different tag combinations
    conv1_response = await async_client.post("/api/conversations", json={
        "title": "Conv with Tag1",
        "model": "claude-sonnet-4-5-20250929"
    })
    conv1 = conv1_response.json()

    conv2_response = await async_client.post("/api/conversations", json={
        "title": "Conv with Tag2",
        "model": "claude-sonnet-4-5-20250929"
    })
    conv2 = conv2_response.json()

    conv3_response = await async_client.post("/api/conversations", json={
        "title": "Conv with Both Tags",
        "model": "claude-sonnet-4-5-20250929"
    })
    conv3 = conv3_response.json()

    # 3. Add tags to conversations
    await async_client.post(f"/api/conversations/{conv1['id']}/tags", json={
        "tag_ids": [tag1["id"]]
    })

    await async_client.post(f"/api/conversations/{conv2['id']}/tags", json={
        "tag_ids": [tag2["id"]]
    })

    await async_client.post(f"/api/conversations/{conv3['id']}/tags", json={
        "tag_ids": [tag1["id"], tag2["id"]]
    })

    # 4. Test filtering conversations by tag1
    response = await async_client.get(f"/api/conversations/filter/by-tags?tag_ids={tag1['id']}")
    assert response.status_code == 200
    filtered_convs = response.json()
    conv_ids = [conv["id"] for conv in filtered_convs]
    assert conv1["id"] in conv_ids  # Has tag1
    assert conv3["id"] in conv_ids  # Has tag1 and tag2
    assert conv2["id"] not in conv_ids  # Only has tag2

    # 5. Test filtering conversations by tag2
    response = await async_client.get(f"/api/conversations/filter/by-tags?tag_ids={tag2['id']}")
    assert response.status_code == 200
    filtered_convs = response.json()
    conv_ids = [conv["id"] for conv in filtered_convs]
    assert conv2["id"] in conv_ids  # Has tag2
    assert conv3["id"] in conv_ids  # Has tag1 and tag2
    assert conv1["id"] not in conv_ids  # Only has tag1

    # 6. Test filtering conversations by both tags (AND logic)
    response = await async_client.get(f"/api/conversations/filter/by-tags?tag_ids={tag1['id']},{tag2['id']}")
    assert response.status_code == 200
    filtered_convs = response.json()
    conv_ids = [conv["id"] for conv in filtered_convs]
    assert conv3["id"] in conv_ids  # Has both tag1 and tag2
    assert conv1["id"] not in conv_ids  # Only has tag1
    assert conv2["id"] not in conv_ids  # Only has tag2

    print("✓ Tag filtering working correctly!")


@pytest.mark.asyncio
async def test_tag_crud_operations(async_client: AsyncClient):
    """Test complete CRUD operations for tags."""

    # 1. Create tag
    response = await async_client.post("/api/tags", json={
        "name": "CRUDTest",
        "color": "#8b5cf6"
    })
    assert response.status_code == 201
    tag = response.json()
    tag_id = tag["id"]

    # 2. Read tag
    response = await async_client.get(f"/api/tags/{tag_id}")
    assert response.status_code == 200
    retrieved_tag = response.json()
    assert retrieved_tag["name"] == "CRUDTest"
    assert retrieved_tag["color"] == "#8b5cf6"

    # 3. Update tag
    response = await async_client.put(f"/api/tags/{tag_id}", json={
        "name": "CRUDTestUpdated",
        "color": "#ec4899"
    })
    assert response.status_code == 200
    updated_tag = response.json()
    assert updated_tag["name"] == "CRUDTestUpdated"
    assert updated_tag["color"] == "#ec4899"

    # 4. Delete tag
    response = await async_client.delete(f"/api/tags/{tag_id}")
    assert response.status_code == 204

    # 5. Verify tag is deleted (soft delete)
    response = await async_client.get(f"/api/tags/{tag_id}")
    assert response.status_code == 404

    print("✓ Tag CRUD operations working correctly!")


def test_frontend_conversation_type_includes_tags():
    """Test that the frontend Conversation type includes tags field."""

    # Check the TypeScript type file
    import os
    type_file = "client/src/stores/conversationStore.ts"

    assert os.path.exists(type_file), f"Type file not found at {type_file}"

    with open(type_file, 'r') as f:
        content = f.read()

    # Check that the Conversation interface includes tags
    assert 'tags: Tag[]' in content, "Frontend Conversation type missing tags field"
    assert 'export interface Tag' in content, "Frontend missing Tag interface"

    print("✓ Frontend Conversation type includes tags!")


def test_sidebar_component_includes_tags_ui():
    """Test that the Sidebar component includes tags UI."""

    import os
    sidebar_file = "client/src/components/Sidebar.tsx"

    assert os.path.exists(sidebar_file), f"Sidebar component not found at {sidebar_file}"

    with open(sidebar_file, 'r') as f:
        content = f.read()

    # Check for tags-related elements
    assert 'availableTags' in content, "Sidebar missing availableTags state"
    assert 'selectedTagIds' in content, "Sidebar missing selectedTagIds state"
    assert 'handleTagFilter' in content, "Sidebar missing handleTagFilter function"
    assert 'Filter by tags' in content, "Sidebar missing tags filter UI"
    assert 'conv.tags' in content, "Sidebar missing tags display"

    print("✓ Sidebar component includes tags UI!")


if __name__ == "__main__":
    print("Run tests with: pytest tests/test_conversation_tags.py -v")