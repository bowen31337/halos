"""Test comments feature for shared conversations."""

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Conversation as ConversationModel, Message as MessageModel
from src.models.shared_conversation import SharedConversation as SharedConversationModel
from src.models.comment import Comment as CommentModel


@pytest.mark.asyncio
async def test_create_comment_on_shared_conversation(async_client: AsyncClient, test_db: AsyncSession):
    """Test creating a comment on a shared conversation."""
    # Create conversation
    conv = ConversationModel(
        title="Test Conversation",
        model="claude-sonnet-4-5-20250929",
    )
    test_db.add(conv)
    await test_db.flush()

    # Create message
    msg = MessageModel(
        conversation_id=conv.id,
        role="user",
        content="Test message",
    )
    test_db.add(msg)
    await test_db.flush()

    # Create shared conversation with comments enabled
    shared = SharedConversationModel(
        conversation_id=conv.id,
        share_token="test_token_123",
        allow_comments=True,
        access_level="comment",
    )
    test_db.add(shared)
    await test_db.commit()

    # Create comment
    response = await async_client.post(
        f"/api/comments/shared/{shared.share_token}/comments",
        json={
            "message_id": str(msg.id),
            "content": "This is a test comment",
            "anonymous_name": "Test User",
        }
    )

    assert response.status_code == 201
    data = response.json()
    assert data["content"] == "This is a test comment"
    assert data["anonymous_name"] == "Test User"
    assert data["message_id"] == str(msg.id)


@pytest.mark.asyncio
async def test_create_comment_reply(async_client: AsyncClient, test_db: AsyncSession):
    """Test creating a reply to a comment."""
    # Create conversation, message, and shared conversation
    conv = ConversationModel(title="Test", model="claude-sonnet-4-5-20250929")
    test_db.add(conv)
    await test_db.flush()

    msg = MessageModel(conversation_id=conv.id, role="user", content="Test")
    test_db.add(msg)
    await test_db.flush()

    shared = SharedConversationModel(
        conversation_id=conv.id,
        share_token="reply_token",
        allow_comments=True,
        access_level="comment",
    )
    test_db.add(shared)
    await test_db.flush()

    # Create parent comment
    parent = CommentModel(
        message_id=msg.id,
        conversation_id=conv.id,
        content="Parent comment",
        anonymous_name="User 1",
    )
    test_db.add(parent)
    await test_db.commit()

    # Create reply
    response = await async_client.post(
        f"/api/comments/shared/{shared.share_token}/comments",
        json={
            "message_id": str(msg.id),
            "content": "This is a reply",
            "parent_comment_id": str(parent.id),
            "anonymous_name": "User 2",
        }
    )

    assert response.status_code == 201
    data = response.json()
    assert data["content"] == "This is a reply"
    assert data["parent_comment_id"] == str(parent.id)


@pytest.mark.asyncio
async def test_list_comments(async_client: AsyncClient, test_db: AsyncSession):
    """Test listing comments for a shared conversation."""
    # Create test data
    conv = ConversationModel(title="Test", model="claude-sonnet-4-5-20250929")
    test_db.add(conv)
    await test_db.flush()

    msg = MessageModel(conversation_id=conv.id, role="user", content="Test")
    test_db.add(msg)
    await test_db.flush()

    shared = SharedConversationModel(
        conversation_id=conv.id,
        share_token="list_token",
        allow_comments=True,
        access_level="comment",
    )
    test_db.add(shared)
    await test_db.flush()

    # Create comments
    comment1 = CommentModel(
        message_id=msg.id,
        conversation_id=conv.id,
        content="Comment 1",
        anonymous_name="User 1",
    )
    test_db.add(comment1)

    comment2 = CommentModel(
        message_id=msg.id,
        conversation_id=conv.id,
        content="Comment 2",
        anonymous_name="User 2",
    )
    test_db.add(comment2)
    await test_db.commit()

    # List comments
    response = await async_client.get(
        f"/api/comments/shared/{shared.share_token}/comments"
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["content"] == "Comment 1"
    assert data[1]["content"] == "Comment 2"


@pytest.mark.asyncio
async def test_update_comment(async_client: AsyncClient, test_db: AsyncSession):
    """Test updating a comment."""
    # Create test data
    conv = ConversationModel(title="Test", model="claude-sonnet-4-5-20250929")
    test_db.add(conv)
    await test_db.flush()

    msg = MessageModel(conversation_id=conv.id, role="user", content="Test")
    test_db.add(msg)
    await test_db.flush()

    shared = SharedConversationModel(
        conversation_id=conv.id,
        share_token="update_token",
        allow_comments=True,
        access_level="comment",
    )
    test_db.add(shared)
    await test_db.flush()

    comment = CommentModel(
        message_id=msg.id,
        conversation_id=conv.id,
        content="Original content",
        anonymous_name="User",
    )
    test_db.add(comment)
    await test_db.commit()

    # Update comment
    response = await async_client.put(
        f"/api/comments/shared/{shared.share_token}/comments/{comment.id}",
        json={"content": "Updated content"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["content"] == "Updated content"
    assert data["updated_at"] is not None


@pytest.mark.asyncio
async def test_delete_comment(async_client: AsyncClient, test_db: AsyncSession):
    """Test deleting a comment."""
    # Create test data
    conv = ConversationModel(title="Test", model="claude-sonnet-4-5-20250929")
    test_db.add(conv)
    await test_db.flush()

    msg = MessageModel(conversation_id=conv.id, role="user", content="Test")
    test_db.add(msg)
    await test_db.flush()

    shared = SharedConversationModel(
        conversation_id=conv.id,
        share_token="delete_token",
        allow_comments=True,
        access_level="comment",
    )
    test_db.add(shared)
    await test_db.flush()

    comment = CommentModel(
        message_id=msg.id,
        conversation_id=conv.id,
        content="To be deleted",
        anonymous_name="User",
    )
    test_db.add(comment)
    await test_db.commit()

    # Delete comment
    response = await async_client.delete(
        f"/api/comments/shared/{shared.share_token}/comments/{comment.id}"
    )

    assert response.status_code == 204

    # Verify soft delete
    result = await test_db.execute(
        select(CommentModel).where(CommentModel.id == comment.id)
    )
    deleted_comment = result.scalar_one()
    assert deleted_comment.is_deleted is True
    assert deleted_comment.deleted_at is not None


@pytest.mark.asyncio
async def test_comments_disabled_when_not_allowed(async_client: AsyncClient, test_db: AsyncSession):
    """Test that comments are rejected when not enabled on shared conversation."""
    # Create test data with comments disabled
    conv = ConversationModel(title="Test", model="claude-sonnet-4-5-20250929")
    test_db.add(conv)
    await test_db.flush()

    msg = MessageModel(conversation_id=conv.id, role="user", content="Test")
    test_db.add(msg)
    await test_db.flush()

    shared = SharedConversationModel(
        conversation_id=conv.id,
        share_token="no_comments_token",
        allow_comments=False,  # Comments disabled
        access_level="read",
    )
    test_db.add(shared)
    await test_db.commit()

    # Try to create comment
    response = await async_client.post(
        f"/api/comments/shared/{shared.share_token}/comments",
        json={
            "message_id": str(msg.id),
            "content": "This should fail",
            "anonymous_name": "User",
        }
    )

    assert response.status_code == 403
    detail = response.json()
    assert "detail" in detail or "error" in detail
    error_msg = detail.get("detail", detail.get("error", "")).lower()
    assert "not enabled" in error_msg or "forbidden" in error_msg
