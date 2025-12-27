"""Message management endpoints."""

from typing import Optional
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.models import Message, Conversation

router = APIRouter()


class MessageCreate(BaseModel):
    """Request model for creating a message."""

    role: str  # user, assistant, system, tool
    content: str
    attachments: Optional[list[dict]] = None
    tool_calls: Optional[dict] = None
    tool_results: Optional[dict] = None
    thinking_content: Optional[str] = None


class MessageUpdate(BaseModel):
    """Request model for updating a message."""

    content: str


@router.get("/conversations/{conversation_id}/messages")
async def list_messages(
    conversation_id: str,
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """List messages in a conversation."""
    query = (
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
        .offset(offset)
        .limit(limit)
    )

    result = await db.execute(query)
    messages = result.scalars().all()

    return [
        {
            "id": msg.id,
            "conversationId": msg.conversation_id,
            "role": msg.role,
            "content": msg.content,
            "tool_calls": msg.tool_calls,
            "tool_results": msg.tool_results,
            "thinking_content": msg.thinking_content,
            "attachments": msg.attachments,
            "createdAt": msg.created_at.isoformat(),
            "editedAt": msg.edited_at.isoformat() if msg.edited_at else None,
        }
        for msg in messages
    ]


@router.post("/conversations/{conversation_id}/messages", status_code=status.HTTP_201_CREATED)
async def create_message(
    conversation_id: str,
    data: MessageCreate,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Create a new message in a conversation."""
    # Verify conversation exists
    conv_result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conversation = conv_result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    now = datetime.utcnow()

    message = Message(
        conversation_id=conversation_id,
        role=data.role,
        content=data.content,
        attachments=data.attachments,
        tool_calls=data.tool_calls,
        tool_results=data.tool_results,
        thinking_content=data.thinking_content,
        created_at=now,
    )

    db.add(message)

    # Update conversation message count and last_message_at
    conversation.message_count += 1
    conversation.last_message_at = now

    await db.commit()
    await db.refresh(message)

    return {
        "id": message.id,
        "conversationId": message.conversation_id,
        "role": message.role,
        "content": message.content,
        "tool_calls": message.tool_calls,
        "tool_results": message.tool_results,
        "thinking_content": message.thinking_content,
        "attachments": message.attachments,
        "createdAt": message.created_at.isoformat(),
        "editedAt": message.edited_at.isoformat() if message.edited_at else None,
    }


@router.get("/{message_id}")
async def get_message(
    message_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get a specific message."""
    result = await db.execute(select(Message).where(Message.id == message_id))
    message = result.scalar_one_or_none()

    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    return {
        "id": message.id,
        "conversationId": message.conversation_id,
        "role": message.role,
        "content": message.content,
        "tool_calls": message.tool_calls,
        "tool_results": message.tool_results,
        "thinking_content": message.thinking_content,
        "attachments": message.attachments,
        "createdAt": message.created_at.isoformat(),
        "editedAt": message.edited_at.isoformat() if message.edited_at else None,
    }


@router.put("/{message_id}")
async def update_message(
    message_id: str,
    data: MessageUpdate,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Update a message."""
    result = await db.execute(select(Message).where(Message.id == message_id))
    message = result.scalar_one_or_none()

    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    message.content = data.content
    message.edited_at = datetime.utcnow()

    await db.commit()
    await db.refresh(message)

    return {
        "id": message.id,
        "conversationId": message.conversation_id,
        "role": message.role,
        "content": message.content,
        "tool_calls": message.tool_calls,
        "tool_results": message.tool_results,
        "thinking_content": message.thinking_content,
        "attachments": message.attachments,
        "createdAt": message.created_at.isoformat(),
        "editedAt": message.edited_at.isoformat() if message.edited_at else None,
    }


@router.delete("/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_message(
    message_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a message."""
    result = await db.execute(select(Message).where(Message.id == message_id))
    message = result.scalar_one_or_none()

    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    # Update conversation message count
    conv_result = await db.execute(
        select(Conversation).where(Conversation.id == message.conversation_id)
    )
    conversation = conv_result.scalar_one_or_none()
    if conversation:
        conversation.message_count = max(0, conversation.message_count - 1)

    await db.delete(message)
    await db.commit()
