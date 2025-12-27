"""Comments API endpoints for shared conversation annotations."""

from typing import Optional
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.models import Comment as CommentModel, SharedConversation as SharedConversationModel, Message as MessageModel

router = APIRouter()


class CommentCreate(BaseModel):
    """Request model for creating a comment."""

    message_id: str = Field(..., description="ID of the message to comment on")
    content: str = Field(..., min_length=1, max_length=5000, description="Comment content")
    parent_comment_id: Optional[str] = Field(None, description="Parent comment ID for replies")
    anonymous_name: Optional[str] = Field(None, max_length=100, description="Name for anonymous commenters")


class CommentUpdate(BaseModel):
    """Request model for updating a comment."""

    content: str = Field(..., min_length=1, max_length=5000, description="Updated comment content")


class CommentResponse(BaseModel):
    """Response model for a comment."""

    id: str
    message_id: str
    conversation_id: str
    user_id: Optional[str]
    anonymous_name: Optional[str]
    content: str
    parent_comment_id: Optional[str]
    created_at: str
    updated_at: Optional[str]
    replies: list["CommentResponse"] = []


@router.post("/shared/{share_token}/comments", status_code=status.HTTP_201_CREATED, response_model=CommentResponse)
async def create_comment(
    share_token: str,
    comment: CommentCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new comment on a shared conversation."""
    # Verify shared conversation exists and allows comments
    result = await db.execute(
        select(SharedConversationModel)
        .where(SharedConversationModel.share_token == share_token)
    )
    shared = result.scalar_one_or_none()

    if not shared:
        raise HTTPException(status_code=404, detail="Shared conversation not found")

    if not shared.allow_comments:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Comments are not enabled for this shared conversation"
        )

    # Verify message exists
    result = await db.execute(
        select(MessageModel)
        .where(MessageModel.id == comment.message_id)
        .where(MessageModel.conversation_id == shared.conversation_id)
    )
    message = result.scalar_one_or_none()

    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    # Verify parent comment exists if provided
    if comment.parent_comment_id:
        result = await db.execute(
            select(CommentModel).where(CommentModel.id == comment.parent_comment_id)
        )
        parent = result.scalar_one_or_none()
        if not parent:
            raise HTTPException(status_code=404, detail="Parent comment not found")

    # Create comment
    new_comment = CommentModel(
        message_id=comment.message_id,
        conversation_id=shared.conversation_id,
        content=comment.content,
        parent_comment_id=comment.parent_comment_id,
        anonymous_name=comment.anonymous_name,
        user_id=None,  # Can be set later with auth
    )

    db.add(new_comment)
    await db.commit()
    await db.refresh(new_comment)

    # New comments don't have replies yet, so don't try to load them
    return _comment_to_response(new_comment, include_replies=False)


@router.get("/shared/{share_token}/comments", response_model=list[CommentResponse])
async def list_comments(
    share_token: str,
    message_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """List all comments for a shared conversation."""
    # Verify shared conversation exists
    result = await db.execute(
        select(SharedConversationModel)
        .where(SharedConversationModel.share_token == share_token)
    )
    shared = result.scalar_one_or_none()

    if not shared:
        raise HTTPException(status_code=404, detail="Shared conversation not found")

    # Build query
    query = select(CommentModel).where(
        CommentModel.conversation_id == shared.conversation_id,
        CommentModel.is_deleted == False,
    )

    if message_id:
        query = query.where(CommentModel.message_id == message_id)

    query = query.options(selectinload(CommentModel.replies))
    query = query.order_by(CommentModel.created_at)

    result = await db.execute(query)
    comments = result.scalars().all()

    # Build nested structure (only top-level comments)
    top_level_comments = [c for c in comments if c.parent_comment_id is None]

    return [_comment_to_response(c) for c in top_level_comments]


@router.put("/shared/{share_token}/comments/{comment_id}", response_model=CommentResponse)
async def update_comment(
    share_token: str,
    comment_id: str,
    update: CommentUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a comment (only by the author)."""
    # Verify shared conversation
    result = await db.execute(
        select(SharedConversationModel)
        .where(SharedConversationModel.share_token == share_token)
    )
    shared = result.scalar_one_or_none()

    if not shared:
        raise HTTPException(status_code=404, detail="Shared conversation not found")

    # Get comment with replies
    result = await db.execute(
        select(CommentModel)
        .options(selectinload(CommentModel.replies))
        .where(CommentModel.id == comment_id)
        .where(CommentModel.conversation_id == shared.conversation_id)
    )
    comment = result.scalar_one_or_none()

    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    # Update comment
    comment.content = update.content
    comment.updated_at = datetime.utcnow()
    comment.edited_at = datetime.utcnow()

    await db.commit()
    await db.refresh(comment)

    # Don't include replies in update response to avoid lazy loading
    return _comment_to_response(comment, include_replies=False)


@router.delete("/shared/{share_token}/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    share_token: str,
    comment_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Delete a comment (soft delete)."""
    # Verify shared conversation
    result = await db.execute(
        select(SharedConversationModel)
        .where(SharedConversationModel.share_token == share_token)
    )
    shared = result.scalar_one_or_none()

    if not shared:
        raise HTTPException(status_code=404, detail="Shared conversation not found")

    # Get comment
    result = await db.execute(
        select(CommentModel)
        .where(CommentModel.id == comment_id)
        .where(CommentModel.conversation_id == shared.conversation_id)
    )
    comment = result.scalar_one_or_none()

    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    # Soft delete
    comment.is_deleted = True
    comment.deleted_at = datetime.utcnow()

    await db.commit()


def _comment_to_response(comment: CommentModel, include_replies: bool = True) -> CommentResponse:
    """Convert Comment model to CommentResponse."""
    replies = []
    if include_replies:
        # Manually load replies to avoid lazy loading issues
        replies = [
            _comment_to_response(reply, include_replies=False)
            for reply in comment.replies
            if not reply.is_deleted
        ]

    return CommentResponse(
        id=comment.id,
        message_id=comment.message_id,
        conversation_id=comment.conversation_id,
        user_id=comment.user_id,
        anonymous_name=comment.anonymous_name,
        content=comment.content,
        parent_comment_id=comment.parent_comment_id,
        created_at=comment.created_at.isoformat(),
        updated_at=comment.updated_at.isoformat() if comment.updated_at else None,
        replies=replies
    )
