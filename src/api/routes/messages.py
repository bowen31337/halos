"""Message management endpoints."""

from typing import Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

router = APIRouter()


class MessageCreate(BaseModel):
    """Request model for creating a message."""

    role: str  # user, assistant, system
    content: str
    attachments: Optional[list[dict]] = None


class MessageUpdate(BaseModel):
    """Request model for updating a message."""

    content: str


# In-memory storage for development
messages_db: dict[UUID, list[dict]] = {}  # conversation_id -> messages


@router.get("/conversations/{conversation_id}/messages")
async def list_messages(
    conversation_id: UUID,
    limit: int = 100,
    offset: int = 0,
) -> list[dict]:
    """List messages in a conversation."""
    if conversation_id not in messages_db:
        return []
    return messages_db[conversation_id][offset : offset + limit]


@router.post("/conversations/{conversation_id}/messages", status_code=status.HTTP_201_CREATED)
async def create_message(conversation_id: UUID, data: MessageCreate) -> dict:
    """Create a new message in a conversation."""
    from datetime import datetime

    if conversation_id not in messages_db:
        messages_db[conversation_id] = []

    message = {
        "id": str(uuid4()),
        "conversation_id": str(conversation_id),
        "role": data.role,
        "content": data.content,
        "attachments": data.attachments or [],
        "created_at": datetime.utcnow().isoformat(),
    }

    messages_db[conversation_id].append(message)
    return message


@router.get("/{message_id}")
async def get_message(message_id: UUID) -> dict:
    """Get a specific message."""
    for conv_messages in messages_db.values():
        for msg in conv_messages:
            if msg["id"] == str(message_id):
                return msg
    raise HTTPException(status_code=404, detail="Message not found")


@router.put("/{message_id}")
async def update_message(message_id: UUID, data: MessageUpdate) -> dict:
    """Update a message."""
    from datetime import datetime

    for conv_messages in messages_db.values():
        for msg in conv_messages:
            if msg["id"] == str(message_id):
                msg["content"] = data.content
                msg["edited_at"] = datetime.utcnow().isoformat()
                return msg
    raise HTTPException(status_code=404, detail="Message not found")


@router.delete("/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_message(message_id: UUID) -> None:
    """Delete a message."""
    for conv_messages in messages_db.values():
        for i, msg in enumerate(conv_messages):
            if msg["id"] == str(message_id):
                del conv_messages[i]
                return
    raise HTTPException(status_code=404, detail="Message not found")
