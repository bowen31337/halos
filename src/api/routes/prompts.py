"""Prompt library management endpoints."""

from typing import Optional
from uuid import UUID
import json

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.models.prompt import Prompt

router = APIRouter()


class PromptCreate(BaseModel):
    """Request model for creating a prompt."""

    title: str
    content: str
    category: str = "general"
    description: Optional[str] = None
    tags: Optional[list[str]] = None


class PromptUpdate(BaseModel):
    """Request model for updating a prompt."""

    title: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[list[str]] = None
    is_active: Optional[bool] = None


@router.get("")
async def list_prompts(
    db: AsyncSession = Depends(get_db),
    category: Optional[str] = None,
    active_only: bool = True,
) -> list[dict]:
    """List all prompts with optional filtering."""
    query = select(Prompt)

    if active_only:
        query = query.where(Prompt.is_active == True)

    if category:
        query = query.where(Prompt.category == category)

    # Order by usage count (most used first), then by most recent
    query = query.order_by(Prompt.usage_count.desc(), Prompt.created_at.desc())

    result = await db.execute(query)
    prompts = result.scalars().all()

    return [prompt.to_dict() for prompt in prompts]


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_prompt(
    data: PromptCreate,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Create a new prompt."""
    # Convert tags list to JSON string
    tags_json = json.dumps(data.tags) if data.tags else None

    prompt = Prompt(
        title=data.title,
        content=data.content,
        category=data.category,
        description=data.description,
        tags=tags_json,
    )

    db.add(prompt)
    await db.commit()
    await db.refresh(prompt)

    return prompt.to_dict()


@router.get("/search")
async def search_prompts(
    q: str,
    db: AsyncSession = Depends(get_db),
    active_only: bool = True,
) -> list[dict]:
    """Search prompts by title, content, description, or tags."""
    query = select(Prompt).where(
        Prompt.title.ilike(f"%{q}%")
        | Prompt.content.ilike(f"%{q}%")
        | Prompt.description.ilike(f"%{q}%")
        | Prompt.tags.ilike(f"%{q}%")
    )

    if active_only:
        query = query.where(Prompt.is_active == True)

    query = query.order_by(Prompt.usage_count.desc(), Prompt.created_at.desc())

    result = await db.execute(query)
    prompts = result.scalars().all()

    return [prompt.to_dict() for prompt in prompts]


@router.get("/{prompt_id}")
async def get_prompt(
    prompt_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get a specific prompt."""
    result = await db.execute(select(Prompt).where(Prompt.id == str(prompt_id)))
    prompt = result.scalar_one_or_none()

    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")

    return prompt.to_dict()


@router.put("/{prompt_id}")
async def update_prompt(
    prompt_id: UUID,
    data: PromptUpdate,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Update a prompt."""
    result = await db.execute(select(Prompt).where(Prompt.id == str(prompt_id)))
    prompt = result.scalar_one_or_none()

    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")

    if data.title is not None:
        prompt.title = data.title
    if data.content is not None:
        prompt.content = data.content
    if data.category is not None:
        prompt.category = data.category
    if data.description is not None:
        prompt.description = data.description
    if data.tags is not None:
        prompt.tags = json.dumps(data.tags) if data.tags else None
    if data.is_active is not None:
        prompt.is_active = data.is_active

    await db.commit()
    await db.refresh(prompt)

    return prompt.to_dict()


@router.delete("/{prompt_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_prompt(
    prompt_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a prompt."""
    result = await db.execute(select(Prompt).where(Prompt.id == str(prompt_id)))
    prompt = result.scalar_one_or_none()

    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")

    await db.delete(prompt)
    await db.commit()


@router.post("/{prompt_id}/use", status_code=status.HTTP_200_OK)
async def use_prompt(
    prompt_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Mark a prompt as used (increments usage count)."""
    result = await db.execute(select(Prompt).where(Prompt.id == str(prompt_id)))
    prompt = result.scalar_one_or_none()

    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")

    # Increment usage count
    prompt.usage_count += 1
    await db.commit()
    await db.refresh(prompt)

    return prompt.to_dict()


@router.get("/categories/list")
async def list_categories(
    db: AsyncSession = Depends(get_db),
    active_only: bool = True,
) -> list[str]:
    """Get all unique categories."""
    query = select(Prompt.category).distinct()

    if active_only:
        # Need to join with Prompt table to filter by is_active
        # Since we're selecting distinct categories, we need a different approach
        # Let's just get all prompts first and extract categories
        query = select(Prompt).where(Prompt.is_active == True)

    result = await db.execute(query)

    if active_only:
        prompts = result.scalars().all()
        categories = list(set(p.category for p in prompts))
    else:
        categories = [row[0] for row in result.fetchall()]

    return sorted(categories)
