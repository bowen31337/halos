"""Project management endpoints."""

import json
from typing import Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.models.project import Project
from src.models.conversation import Conversation

router = APIRouter()


class ProjectCreate(BaseModel):
    """Request model for creating a project."""

    name: str
    description: Optional[str] = None
    color: Optional[str] = "#CC785C"
    icon: Optional[str] = None
    custom_instructions: Optional[str] = None


class ProjectUpdate(BaseModel):
    """Request model for updating a project."""

    name: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None
    icon: Optional[str] = None
    custom_instructions: Optional[str] = None
    is_archived: Optional[bool] = None
    is_pinned: Optional[bool] = None


@router.get("")
async def list_projects(
    archived: bool = False,
    db: AsyncSession = Depends(get_db)
) -> list[dict]:
    """List all projects."""
    result = await db.execute(
        select(Project).where(Project.is_archived == archived)
    )
    projects = result.scalars().all()

    return [
        {
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "color": p.color,
            "icon": p.icon,
            "custom_instructions": p.custom_instructions,
            "is_archived": p.is_archived,
            "is_pinned": p.is_pinned,
            "created_at": p.created_at.isoformat() if p.created_at else None,
            "updated_at": p.updated_at.isoformat() if p.updated_at else None,
        }
        for p in projects
    ]


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_project(
    data: ProjectCreate,
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Create a new project."""
    project = Project(
        name=data.name,
        description=data.description,
        color=data.color,
        icon=data.icon,
        custom_instructions=data.custom_instructions,
    )

    db.add(project)
    await db.commit()
    await db.refresh(project)

    return {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "color": project.color,
        "icon": project.icon,
        "custom_instructions": project.custom_instructions,
        "is_archived": project.is_archived,
        "is_pinned": project.is_pinned,
        "created_at": project.created_at.isoformat() if project.created_at else None,
        "updated_at": project.updated_at.isoformat() if project.updated_at else None,
    }


@router.get("/{project_id}")
async def get_project(
    project_id: str,
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Get a specific project."""
    result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "color": project.color,
        "icon": project.icon,
        "custom_instructions": project.custom_instructions,
        "is_archived": project.is_archived,
        "is_pinned": project.is_pinned,
        "created_at": project.created_at.isoformat() if project.created_at else None,
        "updated_at": project.updated_at.isoformat() if project.updated_at else None,
    }


@router.put("/{project_id}")
async def update_project(
    project_id: str,
    data: ProjectUpdate,
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Update a project."""
    result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Update fields if provided
    if data.name is not None:
        project.name = data.name
    if data.description is not None:
        project.description = data.description
    if data.color is not None:
        project.color = data.color
    if data.icon is not None:
        project.icon = data.icon
    if data.custom_instructions is not None:
        project.custom_instructions = data.custom_instructions
    if data.is_archived is not None:
        project.is_archived = data.is_archived
    if data.is_pinned is not None:
        project.is_pinned = data.is_pinned

    await db.commit()
    await db.refresh(project)

    return {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "color": project.color,
        "icon": project.icon,
        "custom_instructions": project.custom_instructions,
        "is_archived": project.is_archived,
        "is_pinned": project.is_pinned,
        "created_at": project.created_at.isoformat() if project.created_at else None,
        "updated_at": project.updated_at.isoformat() if project.updated_at else None,
    }


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: str,
    db: AsyncSession = Depends(get_db)
) -> None:
    """Delete a project."""
    result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Unlink conversations from this project
    await db.execute(
        select(Conversation).where(Conversation.project_id == project_id)
    )
    conversations = result.scalars().all()
    for conv in conversations:
        conv.project_id = None

    await db.delete(project)
    await db.commit()


@router.get("/{project_id}/conversations")
async def list_project_conversations(
    project_id: str,
    db: AsyncSession = Depends(get_db)
) -> list[dict]:
    """List all conversations in a project."""
    # Verify project exists
    result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Get conversations
    result = await db.execute(
        select(Conversation)
        .where(Conversation.project_id == project_id)
        .where(Conversation.is_deleted == False)
        .order_by(Conversation.updated_at.desc())
    )
    conversations = result.scalars().all()

    return [
        {
            "id": c.id,
            "title": c.title,
            "model": c.model,
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "updated_at": c.updated_at.isoformat() if c.updated_at else None,
            "last_message_at": c.last_message_at.isoformat() if c.last_message_at else None,
            "message_count": c.message_count,
            "is_archived": c.is_archived,
            "is_pinned": c.is_pinned,
        }
        for c in conversations
    ]


@router.put("/{project_id}/settings")
async def update_project_settings(
    project_id: str,
    settings: dict,
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Update project settings."""
    result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    project.settings = json.dumps(settings)
    await db.commit()
    await db.refresh(project)

    return {"status": "updated", "settings": settings}
