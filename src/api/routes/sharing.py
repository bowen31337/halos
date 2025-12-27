"""Conversation sharing endpoints."""

import secrets
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.models import Conversation as ConversationModel, SharedConversation as SharedConversationModel, Message as MessageModel

router = APIRouter()


class ShareRequest(BaseModel):
    """Request model for creating a share link."""

    access_level: str = Field("read", description="read, comment, or edit")
    allow_comments: bool = Field(False, description="Allow comments on shared conversation")
    expires_in_days: Optional[int] = Field(None, description="Days until link expires (optional)")


class ShareResponse(BaseModel):
    """Response model for share link."""

    id: str
    conversation_id: str
    share_token: str
    access_level: str
    allow_comments: bool
    is_public: bool
    created_at: str
    expires_at: Optional[str]
    view_count: int


class SharedConversationView(BaseModel):
    """Response model for viewing a shared conversation."""

    id: str
    title: str
    model: str
    messages: list[dict]
    access_level: str
    allow_comments: bool


@router.post("/{conversation_id}/share", status_code=status.HTTP_201_CREATED)
async def create_share_link(
    conversation_id: str,
    request: ShareRequest,
    db: AsyncSession = Depends(get_db),
) -> ShareResponse:
    """Create a shareable link for a conversation."""

    # Verify conversation exists
    result = await db.execute(
        select(ConversationModel).where(ConversationModel.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Generate unique share token
    share_token = secrets.token_urlsafe(32)

    # Calculate expiration if specified
    expires_at = None
    if request.expires_in_days:
        expires_at = datetime.utcnow() + timedelta(days=request.expires_in_days)

    # Create shared conversation record
    shared = SharedConversationModel(
        conversation_id=conversation_id,
        share_token=share_token,
        access_level=request.access_level,
        allow_comments=request.allow_comments,
        expires_at=expires_at,
    )

    db.add(shared)
    await db.commit()
    await db.refresh(shared)

    return ShareResponse(
        id=shared.id,
        conversation_id=shared.conversation_id,
        share_token=shared.share_token,
        access_level=shared.access_level,
        allow_comments=shared.allow_comments,
        is_public=shared.is_public,
        created_at=shared.created_at.isoformat(),
        expires_at=shared.expires_at.isoformat() if shared.expires_at else None,
        view_count=shared.view_count,
    )


@router.get("/share/{share_token}")
async def view_shared_conversation(
    share_token: str,
    db: AsyncSession = Depends(get_db),
) -> SharedConversationView:
    """View a shared conversation by token."""

    # Find the shared conversation
    result = await db.execute(
        select(SharedConversationModel).where(SharedConversationModel.share_token == share_token)
    )
    shared = result.scalar_one_or_none()

    if not shared:
        raise HTTPException(status_code=404, detail="Share link not found")

    # Check if expired
    if shared.expires_at and shared.expires_at < datetime.utcnow():
        raise HTTPException(status_code=410, detail="Share link has expired")

    # Check if active
    if not shared.is_public:
        raise HTTPException(status_code=403, detail="Share link is no longer active")

    # Get the conversation
    result = await db.execute(
        select(ConversationModel).where(ConversationModel.id == shared.conversation_id)
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Get messages (only if access level allows)
    messages = []
    if shared.access_level in ["read", "comment", "edit"]:
        result = await db.execute(
            select(MessageModel)
            .where(MessageModel.conversation_id == shared.conversation_id)
            .order_by(MessageModel.created_at)
        )
        messages_result = result.scalars().all()

        messages = [
            {
                "id": msg.id,
                "role": msg.role,
                "content": msg.content,
                "createdAt": msg.created_at.isoformat(),
                "attachments": msg.attachments,
                "thinkingContent": msg.thinking_content,
            }
            for msg in messages_result
        ]

    # Increment view count
    shared.view_count += 1
    shared.last_viewed_at = datetime.utcnow()
    await db.commit()

    return SharedConversationView(
        id=conversation.id,
        title=conversation.title,
        model=conversation.model,
        messages=messages,
        access_level=shared.access_level,
        allow_comments=shared.allow_comments,
    )


@router.get("/{conversation_id}/shares")
async def list_shares(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
) -> list[ShareResponse]:
    """List all share links for a conversation."""

    result = await db.execute(
        select(SharedConversationModel)
        .where(SharedConversationModel.conversation_id == conversation_id)
        .order_by(SharedConversationModel.created_at.desc())
    )
    shares = result.scalars().all()

    return [
        ShareResponse(
            id=share.id,
            conversation_id=share.conversation_id,
            share_token=share.share_token,
            access_level=share.access_level,
            allow_comments=share.allow_comments,
            is_public=share.is_public,
            created_at=share.created_at.isoformat(),
            expires_at=share.expires_at.isoformat() if share.expires_at else None,
            view_count=share.view_count,
        )
        for share in shares
    ]


@router.delete("/share/{share_token}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_share_link(
    share_token: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Revoke a share link by deactivating it."""

    result = await db.execute(
        select(SharedConversationModel).where(SharedConversationModel.share_token == share_token)
    )
    shared = result.scalar_one_or_none()

    if not shared:
        raise HTTPException(status_code=404, detail="Share link not found")

    # Deactivate instead of deleting (for audit trail)
    shared.is_public = False
    await db.commit()


@router.delete("/{conversation_id}/shares", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_all_shares(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Revoke all share links for a conversation."""

    result = await db.execute(
        select(SharedConversationModel).where(SharedConversationModel.conversation_id == conversation_id)
    )
    shares = result.scalars().all()

    for share in shares:
        share.is_public = False

    await db.commit()
