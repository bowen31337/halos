"""Conversation management endpoints."""

from typing import Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

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


class Conversation(BaseModel):
    """Response model for a conversation."""

    id: UUID
    title: str
    model: str
    project_id: Optional[UUID] = None
    is_archived: bool = False
    is_pinned: bool = False
    message_count: int = 0
    created_at: str
    updated_at: str


# In-memory storage for development
conversations_db: dict[UUID, dict] = {}


@router.get("")
async def list_conversations(
    project_id: Optional[UUID] = None,
    archived: bool = False,
    limit: int = 50,
    offset: int = 0,
) -> list[dict]:
    """List all conversations."""
    result = []
    for conv_id, conv in conversations_db.items():
        if archived == conv.get("is_archived", False):
            if project_id is None or conv.get("project_id") == project_id:
                result.append(conv)
    return result[offset : offset + limit]


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_conversation(data: ConversationCreate) -> dict:
    """Create a new conversation."""
    from datetime import datetime

    conv_id = uuid4()
    now = datetime.utcnow().isoformat()

    conversation = {
        "id": str(conv_id),
        "title": data.title or "New Conversation",
        "model": data.model,
        "project_id": str(data.project_id) if data.project_id else None,
        "is_archived": False,
        "is_pinned": False,
        "message_count": 0,
        "created_at": now,
        "updated_at": now,
    }

    conversations_db[conv_id] = conversation
    return conversation


@router.get("/{conversation_id}")
async def get_conversation(conversation_id: UUID) -> dict:
    """Get a specific conversation."""
    if conversation_id not in conversations_db:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversations_db[conversation_id]


@router.put("/{conversation_id}")
async def update_conversation(conversation_id: UUID, data: ConversationUpdate) -> dict:
    """Update a conversation."""
    if conversation_id not in conversations_db:
        raise HTTPException(status_code=404, detail="Conversation not found")

    from datetime import datetime

    conv = conversations_db[conversation_id]

    if data.title is not None:
        conv["title"] = data.title
    if data.is_archived is not None:
        conv["is_archived"] = data.is_archived
    if data.is_pinned is not None:
        conv["is_pinned"] = data.is_pinned

    conv["updated_at"] = datetime.utcnow().isoformat()

    return conv


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(conversation_id: UUID) -> None:
    """Delete a conversation."""
    if conversation_id not in conversations_db:
        raise HTTPException(status_code=404, detail="Conversation not found")
    del conversations_db[conversation_id]


@router.post("/{conversation_id}/duplicate")
async def duplicate_conversation(conversation_id: UUID) -> dict:
    """Duplicate a conversation."""
    if conversation_id not in conversations_db:
        raise HTTPException(status_code=404, detail="Conversation not found")

    from datetime import datetime

    original = conversations_db[conversation_id]
    new_id = uuid4()
    now = datetime.utcnow().isoformat()

    duplicate = {
        **original,
        "id": str(new_id),
        "title": f"{original['title']} (Copy)",
        "created_at": now,
        "updated_at": now,
    }

    conversations_db[new_id] = duplicate
    return duplicate
