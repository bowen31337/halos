"""Test batch operations for conversations."""

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Conversation as ConversationModel
from src.models.message import Message as MessageModel


@pytest.mark.asyncio
async def test_batch_export_conversations(async_client: AsyncClient, test_db: AsyncSession):
    """Test batch export of conversations."""
    # Create test conversations
    conv_ids = []
    for i in range(3):
        conv = ConversationModel(
            title=f"Test Batch Conv {i}",
            model="claude-sonnet-4-5-20250929",
        )
        test_db.add(conv)
        await test_db.flush()  # Flush to get the ID
        conv_ids.append(str(conv.id))

        # Add messages
        msg = MessageModel(
            conversation_id=conv.id,
            role="user",
            content=f"Message {i}",
        )
        test_db.add(msg)

    await test_db.commit()

    # Test batch export
    response = await async_client.post(
        "/api/conversations/batch/export",
        json={"conversation_ids": conv_ids},
        params={"format": "json"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success_count"] == 3
    assert data["failure_count"] == 0
    assert len(data["results"]) == 3
    assert data["results"][0]["title"] == "Test Batch Conv 0"


@pytest.mark.asyncio
async def test_batch_delete_conversations(async_client: AsyncClient, test_db: AsyncSession):
    """Test batch delete of conversations."""
    # Create test conversations
    conv_ids = []
    for i in range(3):
        conv = ConversationModel(
            title=f"Test Batch Delete {i}",
            model="claude-sonnet-4-5-20250929",
        )
        test_db.add(conv)
        await test_db.flush()
        conv_ids.append(str(conv.id))

    await test_db.commit()

    # Verify they exist
    result = await test_db.execute(
        select(ConversationModel).where(ConversationModel.id.in_(conv_ids))
    )
    conversations = result.scalars().all()
    assert len(conversations) == 3

    # Test batch delete
    response = await async_client.post(
        "/api/conversations/batch/delete",
        json={"conversation_ids": conv_ids}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success_count"] == 3
    assert data["failure_count"] == 0
    assert set(data["deleted_ids"]) == set(conv_ids)

    # Verify they are soft deleted
    result = await test_db.execute(
        select(ConversationModel).where(ConversationModel.id.in_(conv_ids))
    )
    conversations = result.scalars().all()
    for conv in conversations:
        assert conv.is_deleted is True


@pytest.mark.asyncio
async def test_batch_archive_conversations(async_client: AsyncClient, test_db: AsyncSession):
    """Test batch archive of conversations."""
    # Create test conversations
    conv_ids = []
    for i in range(3):
        conv = ConversationModel(
            title=f"Test Batch Archive {i}",
            model="claude-sonnet-4-5-20250929",
            is_archived=False,
        )
        test_db.add(conv)
        await test_db.flush()
        conv_ids.append(str(conv.id))

    await test_db.commit()

    # Test batch archive
    response = await async_client.post(
        "/api/conversations/batch/archive",
        json={"conversation_ids": conv_ids}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success_count"] == 3
    assert data["failure_count"] == 0

    # Verify they are archived
    result = await test_db.execute(
        select(ConversationModel).where(ConversationModel.id.in_(conv_ids))
    )
    conversations = result.scalars().all()
    for conv in conversations:
        assert conv.is_archived is True


@pytest.mark.asyncio
async def test_batch_with_invalid_ids(async_client: AsyncClient, test_db: AsyncSession):
    """Test batch operations with invalid conversation IDs."""
    # Create one valid conversation
    conv = ConversationModel(
        title="Valid Conv",
        model="claude-sonnet-4-5-20250929",
    )
    test_db.add(conv)
    await test_db.flush()
    valid_id = str(conv.id)
    await test_db.commit()

    # Mix valid and invalid IDs
    invalid_ids = ["00000000-0000-0000-0000-000000000001", "00000000-0000-0000-0000-000000000002"]
    all_ids = [valid_id] + invalid_ids

    # Test batch delete with invalid IDs
    response = await async_client.post(
        "/api/conversations/batch/delete",
        json={"conversation_ids": all_ids}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success_count"] == 1
    assert data["failure_count"] == 2
    assert data["deleted_ids"] == [valid_id]


@pytest.mark.asyncio
async def test_batch_export_markdown_format(async_client: AsyncClient, test_db: AsyncSession):
    """Test batch export with markdown format."""
    # Create test conversation
    conv = ConversationModel(
        title="Markdown Test",
        model="claude-sonnet-4-5-20250929",
    )
    test_db.add(conv)
    await test_db.flush()
    conv_id = str(conv.id)

    msg = MessageModel(
        conversation_id=conv.id,
        role="user",
        content="Test message",
    )
    test_db.add(msg)
    await test_db.commit()
    await test_db.refresh(conv)

    # Test batch export with markdown
    response = await async_client.post(
        "/api/conversations/batch/export",
        json={"conversation_ids": [conv_id]},
        params={"format": "markdown"}
    )

    assert response.status_code == 200
    # The response should be a markdown string (not JSON for markdown format)
    assert "Markdown Test" in response.text
    assert "## 👤 User" in response.text
    assert "Test message" in response.text
