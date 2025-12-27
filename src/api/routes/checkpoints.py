"""Checkpoint management endpoints."""

from typing import Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

router = APIRouter()


class CheckpointCreate(BaseModel):
    """Request model for creating a checkpoint."""

    name: Optional[str] = None
    notes: Optional[str] = None


class CheckpointUpdate(BaseModel):
    """Request model for updating a checkpoint."""

    name: Optional[str] = None
    notes: Optional[str] = None


# In-memory storage
checkpoints_db: dict[UUID, dict] = {}


@router.get("/conversations/{conversation_id}/checkpoints")
async def list_checkpoints(conversation_id: UUID) -> list[dict]:
    """List all checkpoints for a conversation."""
    return [
        cp for cp in checkpoints_db.values() if cp.get("conversation_id") == str(conversation_id)
    ]


@router.post("/conversations/{conversation_id}/checkpoints", status_code=status.HTTP_201_CREATED)
async def create_checkpoint(conversation_id: UUID, data: CheckpointCreate) -> dict:
    """Create a new checkpoint for a conversation."""
    from datetime import datetime

    checkpoint_id = uuid4()
    now = datetime.utcnow().isoformat()

    checkpoint = {
        "id": str(checkpoint_id),
        "conversation_id": str(conversation_id),
        "name": data.name or f"Checkpoint {now}",
        "notes": data.notes,
        "state_snapshot": {},  # Would contain serialized LangGraph state
        "created_at": now,
    }

    checkpoints_db[checkpoint_id] = checkpoint
    return checkpoint


@router.get("/{checkpoint_id}")
async def get_checkpoint(checkpoint_id: UUID) -> dict:
    """Get a specific checkpoint."""
    if checkpoint_id not in checkpoints_db:
        raise HTTPException(status_code=404, detail="Checkpoint not found")
    return checkpoints_db[checkpoint_id]


@router.put("/{checkpoint_id}")
async def update_checkpoint(checkpoint_id: UUID, data: CheckpointUpdate) -> dict:
    """Update a checkpoint."""
    if checkpoint_id not in checkpoints_db:
        raise HTTPException(status_code=404, detail="Checkpoint not found")

    checkpoint = checkpoints_db[checkpoint_id]

    if data.name is not None:
        checkpoint["name"] = data.name
    if data.notes is not None:
        checkpoint["notes"] = data.notes

    return checkpoint


@router.post("/{checkpoint_id}/restore")
async def restore_checkpoint(checkpoint_id: UUID) -> dict:
    """Restore conversation to a checkpoint state."""
    if checkpoint_id not in checkpoints_db:
        raise HTTPException(status_code=404, detail="Checkpoint not found")

    checkpoint = checkpoints_db[checkpoint_id]

    # TODO: Implement actual state restoration with LangGraph
    return {
        "status": "restored",
        "checkpoint_id": str(checkpoint_id),
        "conversation_id": checkpoint["conversation_id"],
        "message": "Conversation restored to checkpoint state",
    }


@router.delete("/{checkpoint_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_checkpoint(checkpoint_id: UUID) -> None:
    """Delete a checkpoint."""
    if checkpoint_id not in checkpoints_db:
        raise HTTPException(status_code=404, detail="Checkpoint not found")
    del checkpoints_db[checkpoint_id]
