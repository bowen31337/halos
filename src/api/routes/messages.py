"""Message management endpoints."""

import os
import uuid
from typing import Optional
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.config import settings
from src.models import Message, Conversation

# Two separate routers for different path patterns
conversation_messages_router = APIRouter()
message_operations_router = APIRouter()

# Combined router for export
router = APIRouter()

# Include both routers with appropriate prefixes
# conversation_messages_router will handle /conversations/{id}/messages routes
# message_operations_router will handle /messages/{id} routes
# These will be included in __init__.py with proper prefixes

# Directory for uploaded images
UPLOAD_DIR = "/tmp/talos-uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


class MessageCreate(BaseModel):
    """Request model for creating a message."""

    role: str  # user, assistant, system, tool
    content: str
    attachments: Optional[list[str]] = None  # List of image URLs
    tool_calls: Optional[dict] = None
    tool_results: Optional[dict] = None
    thinking_content: Optional[str] = None
    suggested_follow_ups: Optional[list[str]] = None  # Suggested follow-up questions


class MessageUpdate(BaseModel):
    """Request model for updating a message."""

    content: str


# Conversation-specific message routes (for /api/conversations/{id}/messages)
@conversation_messages_router.get("/{conversation_id}/messages")
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
            "input_tokens": msg.input_tokens,
            "output_tokens": msg.output_tokens,
            "cache_read_tokens": msg.cache_read_tokens,
            "cache_write_tokens": msg.cache_write_tokens,
            "tool_calls": msg.tool_calls,
            "tool_results": msg.tool_results,
            "thinking_content": msg.thinking_content,
            "suggested_follow_ups": msg.suggested_follow_ups,
            "attachments": msg.attachments,
            "createdAt": msg.created_at.isoformat(),
            "editedAt": msg.edited_at.isoformat() if msg.edited_at else None,
        }
        for msg in messages
    ]


@conversation_messages_router.post("/{conversation_id}/messages", status_code=status.HTTP_201_CREATED)
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

    message = Message(
        conversation_id=conversation_id,
        role=data.role,
        content=data.content,
        attachments=data.attachments,
        tool_calls=data.tool_calls,
        tool_results=data.tool_results,
        thinking_content=data.thinking_content,
        suggested_follow_ups=data.suggested_follow_ups,
    )

    now = datetime.utcnow()

    db.add(message)

    # Update conversation message count and last_message_at
    conversation.message_count += 1
    conversation.last_message_at = now

    # Handle unread count - increment for assistant messages
    if data.role == 'assistant':
        conversation.unread_count += 1

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
        "suggested_follow_ups": message.suggested_follow_ups,
        "attachments": message.attachments,
        "input_tokens": message.input_tokens,
        "output_tokens": message.output_tokens,
        "cache_read_tokens": message.cache_read_tokens,
        "cache_write_tokens": message.cache_write_tokens,
        "createdAt": message.created_at.isoformat(),
        "editedAt": message.edited_at.isoformat() if message.edited_at else None,
    }


# Message CRUD routes (for /api/messages/{id})
@message_operations_router.get("/{message_id}")
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
        "suggested_follow_ups": message.suggested_follow_ups,
        "attachments": message.attachments,
        "input_tokens": message.input_tokens,
        "output_tokens": message.output_tokens,
        "cache_read_tokens": message.cache_read_tokens,
        "cache_write_tokens": message.cache_write_tokens,
        "createdAt": message.created_at.isoformat(),
        "editedAt": message.edited_at.isoformat() if message.edited_at else None,
    }


@message_operations_router.put("/{message_id}")
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
        "suggested_follow_ups": message.suggested_follow_ups,
        "attachments": message.attachments,
        "input_tokens": message.input_tokens,
        "output_tokens": message.output_tokens,
        "cache_read_tokens": message.cache_read_tokens,
        "cache_write_tokens": message.cache_write_tokens,
        "createdAt": message.created_at.isoformat(),
        "editedAt": message.edited_at.isoformat() if message.edited_at else None,
    }


@message_operations_router.delete("/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
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


@message_operations_router.post("/upload-image", status_code=status.HTTP_201_CREATED)
async def upload_image(file: UploadFile = File(...)) -> dict:
    """Upload an image file and return its URL."""
    # Validate file type
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail="Only image files are allowed"
        )

    # Generate unique filename
    file_extension = file.filename.split(".")[-1] if file.filename else "png"
    unique_filename = f"{uuid.uuid4()}.{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)

    # Save file
    try:
        contents = await file.read()
        with open(file_path, "wb") as f:
            f.write(contents)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save image: {str(e)}"
        )

    # Return URL to access the image
    image_url = f"/api/messages/images/{unique_filename}"
    return {
        "url": image_url,
        "filename": unique_filename,
        "original_filename": file.filename,
        "size": len(contents)
    }


@message_operations_router.get("/images/{filename}")
async def get_image(filename: str) -> FileResponse:
    """Serve an uploaded image file."""
    file_path = os.path.join(UPLOAD_DIR, filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Image not found")

    return FileResponse(file_path)


# Include sub-routers in the main router for convenience
router.include_router(conversation_messages_router)
router.include_router(message_operations_router)
