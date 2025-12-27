"""Long-term memory management endpoints."""

from typing import Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

router = APIRouter()


class MemoryCreate(BaseModel):
    """Request model for creating a memory."""

    content: str
    category: str = "fact"  # fact, preference, context


class MemoryUpdate(BaseModel):
    """Request model for updating a memory."""

    content: Optional[str] = None
    category: Optional[str] = None
    is_active: Optional[bool] = None


# In-memory storage
memories_db: dict[UUID, dict] = {}


@router.get("")
async def list_memories(
    category: Optional[str] = None,
    active_only: bool = True,
) -> list[dict]:
    """List all memories."""
    result = []
    for mem in memories_db.values():
        if active_only and not mem.get("is_active", True):
            continue
        if category and mem.get("category") != category:
            continue
        result.append(mem)
    return result


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_memory(data: MemoryCreate) -> dict:
    """Create a new memory."""
    from datetime import datetime

    memory_id = uuid4()
    now = datetime.utcnow().isoformat()

    memory = {
        "id": str(memory_id),
        "content": data.content,
        "category": data.category,
        "is_active": True,
        "created_at": now,
        "updated_at": now,
    }

    memories_db[memory_id] = memory
    return memory


@router.get("/search")
async def search_memories(q: str) -> list[dict]:
    """Search memories by content."""
    results = []
    q_lower = q.lower()
    for mem in memories_db.values():
        if q_lower in mem.get("content", "").lower():
            results.append(mem)
    return results


@router.get("/{memory_id}")
async def get_memory(memory_id: UUID) -> dict:
    """Get a specific memory."""
    if memory_id not in memories_db:
        raise HTTPException(status_code=404, detail="Memory not found")
    return memories_db[memory_id]


@router.put("/{memory_id}")
async def update_memory(memory_id: UUID, data: MemoryUpdate) -> dict:
    """Update a memory."""
    if memory_id not in memories_db:
        raise HTTPException(status_code=404, detail="Memory not found")

    from datetime import datetime

    memory = memories_db[memory_id]

    if data.content is not None:
        memory["content"] = data.content
    if data.category is not None:
        memory["category"] = data.category
    if data.is_active is not None:
        memory["is_active"] = data.is_active

    memory["updated_at"] = datetime.utcnow().isoformat()

    return memory


@router.delete("/{memory_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_memory(memory_id: UUID) -> None:
    """Delete a memory."""
    if memory_id not in memories_db:
        raise HTTPException(status_code=404, detail="Memory not found")
    del memories_db[memory_id]
