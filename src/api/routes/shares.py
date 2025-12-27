"""Share conversation endpoints for creating shareable links."""

from typing import Optional
from uuid import UUID, uuid4
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.models.conversation import Conversation, Message
from src.models.shared_conversation import SharedConversation

router = APIRouter()


class ShareConfig(BaseModel):
    """Configuration for creating a share link."""

    conversation_id: str
    read_only: bool = True
    expires_in_days: Optional[int] = None  # None = never expires


class ShareResponse(BaseModel):
    """Response model for share link creation."""

    share_id: str
    share_url: str
    read_only: bool
    expires_at: Optional[datetime]


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_share_link(
    config: ShareConfig,
    db: AsyncSession = Depends(get_db),
) -> ShareResponse:
    """
    Create a shareable link for a conversation.

    This generates a unique token that can be used to view (and optionally edit)
    a conversation without needing to authenticate.
    """
    # Verify conversation exists
    result = await db.execute(
        select(Conversation).where(Conversation.id == config.conversation_id)
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(
            status_code=404,
            detail=f"Conversation {config.conversation_id} not found"
        )

    # Generate unique share token
    share_token = str(uuid4())

    # Calculate expiration
    expires_at = None
    if config.expires_in_days:
        expires_at = datetime.utcnow() + timedelta(days=config.expires_in_days)

    # Create share link record
    share_link = SharedConversation(
        share_token=share_token,
        conversation_id=config.conversation_id,
        access_level="read" if config.read_only else "edit",
        expires_at=expires_at,
    )

    db.add(share_link)
    await db.commit()
    await db.refresh(share_link)

    # Generate full share URL
    # In production, this would use the actual domain
    share_url = f"/share/{share_token}"

    return ShareResponse(
        share_id=str(share_link.id),
        share_url=share_url,
        read_only=config.read_only,
        expires_at=expires_at,
    )


@router.get("/{share_token}")
async def get_shared_conversation(
    share_token: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Retrieve a shared conversation by token.

    Returns the conversation and its messages for viewing.
    """
    # Find the share link
    result = await db.execute(
        select(SharedConversation).where(SharedConversation.share_token == share_token)
    )
    share_link = result.scalar_one_or_none()

    if not share_link:
        raise HTTPException(
            status_code=404,
            detail="Share link not found"
        )

    # Check if expired
    if share_link.expires_at and share_link.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=410,
            detail="Share link has expired"
        )

    # Get the conversation
    result = await db.execute(
        select(Conversation).where(Conversation.id == share_link.conversation_id)
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(
            status_code=404,
            detail="Shared conversation no longer exists"
        )

    # Get messages for the conversation
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == share_link.conversation_id)
        .order_by(Message.created_at)
    )
    messages = result.scalars().all()

    # Increment view count
    share_link.view_count += 1
    share_link.last_viewed_at = datetime.utcnow()
    await db.commit()

    return {
        "id": str(conversation.id),
        "title": conversation.title,
        "model": conversation.model,
        "read_only": share_link.access_level == "read",
        "access_level": share_link.access_level,
        "created_at": conversation.created_at.isoformat(),
        "messages": [{"id": msg.id, "role": msg.role, "content": msg.content, "created_at": msg.created_at.isoformat()} for msg in messages],
        "expires_at": share_link.expires_at.isoformat() if share_link.expires_at else None,
        "allow_comments": share_link.allow_comments,
    }


@router.delete("/{share_token}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_share_link(
    share_token: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Revoke (delete) a share link.

    This prevents the link from being used to access the conversation.
    """
    result = await db.execute(
        select(SharedConversation).where(SharedConversation.share_token == share_token)
    )
    share_link = result.scalar_one_or_none()

    if not share_link:
        raise HTTPException(
            status_code=404,
            detail="Share link not found"
        )

    await db.delete(share_link)
    await db.commit()


@router.get("/conversation/{conversation_id}")
async def list_conversation_shares(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """
    List all share links for a conversation.
    """
    result = await db.execute(
        select(SharedConversation)
        .where(SharedConversation.conversation_id == conversation_id)
        .order_by(SharedConversation.created_at.desc())
    )
    shares = result.scalars().all()

    return [
        {
            "id": share.id,
            "share_token": share.share_token,
            "conversation_id": share.conversation_id,
            "access_level": share.access_level,
            "allow_comments": share.allow_comments,
            "is_public": share.is_public,
            "created_at": share.created_at.isoformat(),
            "expires_at": share.expires_at.isoformat() if share.expires_at else None,
            "view_count": share.view_count,
            "last_viewed_at": share.last_viewed_at.isoformat() if share.last_viewed_at else None,
        }
        for share in shares
    ]
