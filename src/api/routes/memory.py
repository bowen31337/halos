"""Long-term memory management endpoints."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.models.memory import Memory

router = APIRouter()


class MemoryCreate(BaseModel):
    """Request model for creating a memory."""

    content: str
    category: str = "fact"  # fact, preference, context
    source_conversation_id: Optional[str] = None


class MemoryUpdate(BaseModel):
    """Request model for updating a memory."""

    content: Optional[str] = None
    category: Optional[str] = None
    is_active: Optional[bool] = None


@router.get("")
async def list_memories(
    db: AsyncSession = Depends(get_db),
    category: Optional[str] = None,
    active_only: bool = True,
) -> list[dict]:
    """List all memories with optional filtering."""
    query = select(Memory)

    if active_only:
        query = query.where(Memory.is_active == True)

    if category:
        query = query.where(Memory.category == category)

    # Order by most recent first
    query = query.order_by(Memory.created_at.desc())

    result = await db.execute(query)
    memories = result.scalars().all()

    return [mem.to_dict() for mem in memories]


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_memory(
    data: MemoryCreate,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Create a new memory."""
    memory = Memory(
        content=data.content,
        category=data.category,
        source_conversation_id=data.source_conversation_id,
    )

    db.add(memory)
    await db.commit()
    await db.refresh(memory)

    return memory.to_dict()


@router.get("/search")
async def search_memories(
    q: str,
    db: AsyncSession = Depends(get_db),
    active_only: bool = True,
) -> list[dict]:
    """Search memories by content."""
    query = select(Memory).where(Memory.content.ilike(f"%{q}%"))

    if active_only:
        query = query.where(Memory.is_active == True)

    query = query.order_by(Memory.created_at.desc())

    result = await db.execute(query)
    memories = result.scalars().all()

    return [mem.to_dict() for mem in memories]


@router.get("/{memory_id}")
async def get_memory(
    memory_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get a specific memory."""
    result = await db.execute(select(Memory).where(Memory.id == str(memory_id)))
    memory = result.scalar_one_or_none()

    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")

    return memory.to_dict()


@router.put("/{memory_id}")
async def update_memory(
    memory_id: UUID,
    data: MemoryUpdate,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Update a memory."""
    result = await db.execute(select(Memory).where(Memory.id == str(memory_id)))
    memory = result.scalar_one_or_none()

    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")

    if data.content is not None:
        memory.content = data.content
    if data.category is not None:
        memory.category = data.category
    if data.is_active is not None:
        memory.is_active = data.is_active

    await db.commit()
    await db.refresh(memory)

    return memory.to_dict()


@router.delete("/{memory_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_memory(
    memory_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a memory."""
    result = await db.execute(select(Memory).where(Memory.id == str(memory_id)))
    memory = result.scalar_one_or_none()

    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")

    await db.delete(memory)
    await db.commit()


@router.post("/extract", status_code=status.HTTP_201_CREATED)
async def extract_memory(
    content: str,
    conversation_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Extract and store a memory from conversation content.

    This endpoint allows the agent to automatically save important information
    to long-term memory.
    """
    # Simple extraction: just store the content as-is
    # In a real implementation, this would use NLP to extract structured memory

    memory = Memory(
        content=content,
        category="fact",
        source_conversation_id=conversation_id,
    )

    db.add(memory)
    await db.commit()
    await db.refresh(memory)

    return memory.to_dict()
