"""Checkpoint management endpoints."""

from typing import Optional
from uuid import UUID, uuid4
from datetime import datetime

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.core.database import get_db
from src.models.checkpoint import Checkpoint
from src.models.conversation import Conversation
from src.models.message import Message
from src.models.artifact import Artifact

# Router for conversation-specific checkpoint operations (prefixed with /conversations)
conversation_router = APIRouter()
# Router for checkpoint-specific operations (prefixed with /checkpoints)
checkpoint_router = APIRouter()


class CheckpointCreate(BaseModel):
    """Request model for creating a checkpoint."""

    name: Optional[str] = None
    notes: Optional[str] = None


class CheckpointUpdate(BaseModel):
    """Request model for updating a checkpoint."""

    name: Optional[str] = None
    notes: Optional[str] = None


class CheckpointResponse(BaseModel):
    """Response model for checkpoint data."""

    id: str
    conversation_id: str
    name: str
    notes: Optional[str] = None
    state_snapshot: dict
    created_at: str
    updated_at: str


@conversation_router.get("/{conversation_id}/checkpoints", response_model=list[CheckpointResponse])
async def list_checkpoints(
    conversation_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> list[dict]:
    """List all checkpoints for a conversation."""
    result = await db.execute(
        select(Checkpoint)
        .where(Checkpoint.conversation_id == str(conversation_id))
        .order_by(Checkpoint.created_at.desc())
    )
    checkpoints = result.scalars().all()

    return [
        {
            "id": cp.id,
            "conversation_id": cp.conversation_id,
            "name": cp.name,
            "notes": cp.notes,
            "state_snapshot": cp.state_snapshot,
            "created_at": cp.created_at.isoformat(),
            "updated_at": cp.updated_at.isoformat(),
        }
        for cp in checkpoints
    ]


@conversation_router.post("/{conversation_id}/checkpoints", status_code=status.HTTP_201_CREATED)
async def create_checkpoint(
    conversation_id: UUID,
    data: CheckpointCreate,
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Create a new checkpoint for a conversation.

    The checkpoint captures:
    - All messages up to this point
    - Conversation metadata
    - Associated artifacts
    """
    # Verify conversation exists
    result = await db.execute(
        select(Conversation).where(Conversation.id == str(conversation_id))
    )
    conversation = result.scalar_one_or_none()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Get all messages for this conversation
    messages_result = await db.execute(
        select(Message)
        .where(Message.conversation_id == str(conversation_id))
        .order_by(Message.created_at.asc())
    )
    messages = messages_result.scalars().all()

    # Get all artifacts for this conversation
    artifacts_result = await db.execute(
        select(Artifact)
        .where(Artifact.conversation_id == str(conversation_id))
        .order_by(Artifact.created_at.asc())
    )
    artifacts = artifacts_result.scalars().all()

    # Create state snapshot
    state_snapshot = {
        "messages": [
            {
                "id": msg.id,
                "role": msg.role,
                "content": msg.content,
                "created_at": msg.created_at.isoformat(),
            }
            for msg in messages
        ],
        "conversation_metadata": {
            "title": conversation.title,
            "model": conversation.model,
            "thread_id": conversation.thread_id,
            "extended_thinking_enabled": conversation.extended_thinking_enabled,
        },
        "artifacts": [
            {
                "id": art.id,
                "title": art.title,
                "artifact_type": art.artifact_type,
                "content": art.content,
            }
            for art in artifacts
        ],
    }

    # Create checkpoint
    checkpoint = Checkpoint(
        id=str(uuid4()),
        conversation_id=str(conversation_id),
        name=data.name or f"Checkpoint {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}",
        notes=data.notes,
        state_snapshot=state_snapshot,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    db.add(checkpoint)
    await db.commit()
    await db.refresh(checkpoint)

    return {
        "id": checkpoint.id,
        "conversation_id": checkpoint.conversation_id,
        "name": checkpoint.name,
        "notes": checkpoint.notes,
        "state_snapshot": checkpoint.state_snapshot,
        "created_at": checkpoint.created_at.isoformat(),
        "updated_at": checkpoint.updated_at.isoformat(),
    }


@checkpoint_router.get("/{checkpoint_id}", response_model=CheckpointResponse)
async def get_checkpoint(
    checkpoint_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Get a specific checkpoint."""
    result = await db.execute(
        select(Checkpoint).where(Checkpoint.id == str(checkpoint_id))
    )
    checkpoint = result.scalar_one_or_none()

    if not checkpoint:
        raise HTTPException(status_code=404, detail="Checkpoint not found")

    return {
        "id": checkpoint.id,
        "conversation_id": checkpoint.conversation_id,
        "name": checkpoint.name,
        "notes": checkpoint.notes,
        "state_snapshot": checkpoint.state_snapshot,
        "created_at": checkpoint.created_at.isoformat(),
        "updated_at": checkpoint.updated_at.isoformat(),
    }


@checkpoint_router.put("/{checkpoint_id}", response_model=CheckpointResponse)
async def update_checkpoint(
    checkpoint_id: UUID,
    data: CheckpointUpdate,
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Update a checkpoint."""
    result = await db.execute(
        select(Checkpoint).where(Checkpoint.id == str(checkpoint_id))
    )
    checkpoint = result.scalar_one_or_none()

    if not checkpoint:
        raise HTTPException(status_code=404, detail="Checkpoint not found")

    if data.name is not None:
        checkpoint.name = data.name
    if data.notes is not None:
        checkpoint.notes = data.notes

    checkpoint.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(checkpoint)

    return {
        "id": checkpoint.id,
        "conversation_id": checkpoint.conversation_id,
        "name": checkpoint.name,
        "notes": checkpoint.notes,
        "state_snapshot": checkpoint.state_snapshot,
        "created_at": checkpoint.created_at.isoformat(),
        "updated_at": checkpoint.updated_at.isoformat(),
    }


@checkpoint_router.post("/{checkpoint_id}/restore")
async def restore_checkpoint(
    checkpoint_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Restore conversation to a checkpoint state.

    This endpoint:
    1. Retrieves the checkpoint's state snapshot
    2. Truncates all messages after the checkpoint point
    3. Restores conversation metadata
    4. Returns the restored state

    Note: This is a simplified implementation. In production, you might want to:
    - Create a new conversation branch instead of modifying the existing one
    - Use LangGraph checkpointing for state restoration
    - Implement transaction safety
    """
    result = await db.execute(
        select(Checkpoint).where(Checkpoint.id == str(checkpoint_id))
    )
    checkpoint = result.scalar_one_or_none()

    if not checkpoint:
        raise HTTPException(status_code=404, detail="Checkpoint not found")

    # Get the conversation
    conv_result = await db.execute(
        select(Conversation).where(Conversation.id == checkpoint.conversation_id)
    )
    conversation = conv_result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Get current messages
    current_messages_result = await db.execute(
        select(Message)
        .where(Message.conversation_id == checkpoint.conversation_id)
        .order_by(Message.created_at.asc())
    )
    current_messages = current_messages_result.scalars().all()

    # Get checkpoint message IDs
    checkpoint_message_ids = {msg["id"] for msg in checkpoint.state_snapshot.get("messages", [])}

    # Delete messages that came after the checkpoint
    messages_to_delete = [msg for msg in current_messages if msg.id not in checkpoint_message_ids]

    for msg in messages_to_delete:
        await db.delete(msg)

    # Update conversation metadata if it changed
    conv_metadata = checkpoint.state_snapshot.get("conversation_metadata", {})
    if conv_metadata:
        if "title" in conv_metadata:
            conversation.title = conv_metadata["title"]
        if "model" in conv_metadata:
            conversation.model = conv_metadata["model"]
        if "thread_id" in conv_metadata:
            conversation.thread_id = conv_metadata["thread_id"]
        if "extended_thinking_enabled" in conv_metadata:
            conversation.extended_thinking_enabled = conv_metadata["extended_thinking_enabled"]

    # Update message count
    conversation.message_count = len(checkpoint_message_ids)

    await db.commit()

    return {
        "status": "restored",
        "checkpoint_id": str(checkpoint_id),
        "conversation_id": checkpoint.conversation_id,
        "restored_message_count": len(checkpoint_message_ids),
        "deleted_message_count": len(messages_to_delete),
        "message": f"Conversation restored. Deleted {len(messages_to_delete)} messages, kept {len(checkpoint_message_ids)} messages from checkpoint.",
    }


@checkpoint_router.delete("/{checkpoint_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_checkpoint(
    checkpoint_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> None:
    """Delete a checkpoint."""
    result = await db.execute(
        select(Checkpoint).where(Checkpoint.id == str(checkpoint_id))
    )
    checkpoint = result.scalar_one_or_none()

    if not checkpoint:
        raise HTTPException(status_code=404, detail="Checkpoint not found")

    await db.delete(checkpoint)
    await db.commit()


# Main router for importing in __init__.py
router = conversation_router
