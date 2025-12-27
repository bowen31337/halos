"""Conversation management endpoints."""

from typing import Optional
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.models import Conversation as ConversationModel

router = APIRouter()


class ConversationCreate(BaseModel):
    """Request model for creating a conversation."""

    title: Optional[str] = None
    project_id: Optional[UUID] = None
    model: str = "claude-sonnet-4-5-20250929"


class ConversationUpdate(BaseModel):
    """Request model for updating a conversation."""

    title: Optional[str] = None
    is_archived: Optional[bool] = None
    is_pinned: Optional[bool] = None


class ConversationResponse(BaseModel):
    """Response model for a conversation."""

    id: str
    title: str
    model: str
    project_id: Optional[str] = None
    is_archived: bool = False
    is_pinned: bool = False
    message_count: int = 0
    created_at: str
    updated_at: str


@router.get("")
async def list_conversations(
    project_id: Optional[UUID] = None,
    archived: bool = False,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """List all conversations."""
    query = select(ConversationModel).where(ConversationModel.is_deleted == False)

    if archived:
        query = query.where(ConversationModel.is_archived == True)
    else:
        query = query.where(ConversationModel.is_archived == False)

    if project_id:
        query = query.where(ConversationModel.project_id == str(project_id))

    query = query.order_by(ConversationModel.updated_at.desc()).offset(offset).limit(limit)

    result = await db.execute(query)
    conversations = result.scalars().all()

    return [
        {
            "id": conv.id,
            "title": conv.title,
            "model": conv.model,
            "project_id": conv.project_id,
            "is_archived": conv.is_archived,
            "is_pinned": conv.is_pinned,
            "message_count": conv.message_count,
            "created_at": conv.created_at.isoformat(),
            "updated_at": conv.updated_at.isoformat(),
        }
        for conv in conversations
    ]


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_conversation(
    data: ConversationCreate,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Create a new conversation."""
    now = datetime.utcnow()

    conversation = ConversationModel(
        title=data.title or "New Conversation",
        model=data.model,
        project_id=str(data.project_id) if data.project_id else None,
        created_at=now,
        updated_at=now,
        last_message_at=now,
    )

    db.add(conversation)
    await db.commit()
    await db.refresh(conversation)

    return {
        "id": conversation.id,
        "title": conversation.title,
        "model": conversation.model,
        "project_id": conversation.project_id,
        "is_archived": conversation.is_archived,
        "is_pinned": conversation.is_pinned,
        "message_count": conversation.message_count,
        "created_at": conversation.created_at.isoformat(),
        "updated_at": conversation.updated_at.isoformat(),
    }


@router.get("/{conversation_id}")
async def get_conversation(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get a specific conversation."""
    result = await db.execute(select(ConversationModel).where(ConversationModel.id == conversation_id))
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return {
        "id": conversation.id,
        "title": conversation.title,
        "model": conversation.model,
        "project_id": conversation.project_id,
        "is_archived": conversation.is_archived,
        "is_pinned": conversation.is_pinned,
        "message_count": conversation.message_count,
        "created_at": conversation.created_at.isoformat(),
        "updated_at": conversation.updated_at.isoformat(),
    }


@router.put("/{conversation_id}")
async def update_conversation(
    conversation_id: str,
    data: ConversationUpdate,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Update a conversation."""
    result = await db.execute(select(ConversationModel).where(ConversationModel.id == conversation_id))
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    if data.title is not None:
        conversation.title = data.title
    if data.is_archived is not None:
        conversation.is_archived = data.is_archived
    if data.is_pinned is not None:
        conversation.is_pinned = data.is_pinned

    conversation.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(conversation)

    return {
        "id": conversation.id,
        "title": conversation.title,
        "model": conversation.model,
        "project_id": conversation.project_id,
        "is_archived": conversation.is_archived,
        "is_pinned": conversation.is_pinned,
        "message_count": conversation.message_count,
        "created_at": conversation.created_at.isoformat(),
        "updated_at": conversation.updated_at.isoformat(),
    }


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a conversation (soft delete)."""
    result = await db.execute(select(ConversationModel).where(ConversationModel.id == conversation_id))
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    conversation.is_deleted = True
    await db.commit()


@router.post("/{conversation_id}/duplicate")
async def duplicate_conversation(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Duplicate a conversation."""
    result = await db.execute(select(ConversationModel).where(ConversationModel.id == conversation_id))
    original = result.scalar_one_or_none()

    if not original:
        raise HTTPException(status_code=404, detail="Conversation not found")

    now = datetime.utcnow()

    duplicate = ConversationModel(
        title=f"{original.title} (Copy)",
        model=original.model,
        project_id=original.project_id,
        created_at=now,
        updated_at=now,
        last_message_at=now,
    )

    db.add(duplicate)
    await db.commit()
    await db.refresh(duplicate)

    return {
        "id": duplicate.id,
        "title": duplicate.title,
        "model": duplicate.model,
        "project_id": duplicate.project_id,
        "is_archived": duplicate.is_archived,
        "is_pinned": duplicate.is_pinned,
        "message_count": duplicate.message_count,
        "created_at": duplicate.created_at.isoformat(),
        "updated_at": duplicate.updated_at.isoformat(),
    }
