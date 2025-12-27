"""Project management endpoints."""

import json
import os
from pathlib import Path
from typing import Optional
from uuid import UUID, uuid4
import aiofiles
from aiofiles import os as aiofiles_os

from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.models.project import Project
from src.models.conversation import Conversation
from src.models.project_file import ProjectFile

router = APIRouter()

# Directory for project files
PROJECT_FILES_DIR = Path("data/project_files")
PROJECT_FILES_DIR.mkdir(parents=True, exist_ok=True)


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
    result = await db.execute(
        select(Conversation).where(Conversation.project_id == project_id)
    )
    conversations = result.scalars().all()
    for conv in conversations:
        conv.project_id = None

    # Delete all project files from database and disk
    result = await db.execute(
        select(ProjectFile).where(ProjectFile.project_id == project_id)
    )
    project_files = result.scalars().all()
    for file in project_files:
        # Delete file from disk
        try:
            file_path = Path(file.file_path)
            if file_path.exists():
                file_path.unlink()
        except Exception:
            pass
        await db.delete(file)

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


@router.post("/{project_id}/files", status_code=status.HTTP_201_CREATED)
async def upload_project_file(
    project_id: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Upload a file to a project's knowledge base."""
    # Verify project exists
    result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Generate unique filename
    file_extension = file.filename.split(".")[-1] if file.filename and "." in file.filename else ""
    unique_filename = f"{uuid4()}.{file_extension}" if file_extension else str(uuid4())

    # Create project-specific directory
    project_dir = PROJECT_FILES_DIR / project_id
    project_dir.mkdir(parents=True, exist_ok=True)

    file_path = project_dir / unique_filename

    # Save file
    try:
        contents = await file.read()
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(contents)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save file: {str(e)}"
        )

    # Extract text content for certain file types
    content = None
    if file.content_type in ["text/plain", "text/markdown", "text/csv"]:
        content = contents.decode("utf-8", errors="ignore")
    elif file.content_type == "application/json":
        try:
            content = json.dumps(json.loads(contents.decode("utf-8", errors="ignore")), indent=2)
        except:
            content = contents.decode("utf-8", errors="ignore")

    # Create database record
    project_file = ProjectFile(
        project_id=project_id,
        filename=unique_filename,
        original_filename=file.filename or "unknown",
        file_path=str(file_path),
        file_url=f"/api/projects/{project_id}/files/{unique_filename}",
        file_size=len(contents),
        content_type=file.content_type,
        content=content,
    )

    db.add(project_file)
    await db.commit()
    await db.refresh(project_file)

    return {
        "id": project_file.id,
        "project_id": project_file.project_id,
        "filename": project_file.filename,
        "original_filename": project_file.original_filename,
        "file_url": project_file.file_url,
        "file_size": project_file.file_size,
        "content_type": project_file.content_type,
        "content": project_file.content,
        "created_at": project_file.created_at.isoformat() if project_file.created_at else None,
    }


@router.get("/{project_id}/files")
async def list_project_files(
    project_id: str,
    db: AsyncSession = Depends(get_db)
) -> list[dict]:
    """List all files in a project's knowledge base."""
    # Verify project exists
    result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Get project files
    result = await db.execute(
        select(ProjectFile)
        .where(ProjectFile.project_id == project_id)
        .where(ProjectFile.is_archived == False)
        .where(ProjectFile.is_deleted == False)
        .order_by(ProjectFile.created_at.desc())
    )
    files = result.scalars().all()

    return [
        {
            "id": f.id,
            "project_id": f.project_id,
            "filename": f.filename,
            "original_filename": f.original_filename,
            "file_url": f.file_url,
            "file_size": f.file_size,
            "content_type": f.content_type,
            "content": f.content[:500] if f.content else None,  # Preview first 500 chars
            "created_at": f.created_at.isoformat() if f.created_at else None,
        }
        for f in files
    ]


@router.get("/{project_id}/files/{filename}")
async def get_project_file(
    project_id: str,
    filename: str,
    db: AsyncSession = Depends(get_db)
) -> FileResponse:
    """Download a file from a project's knowledge base."""
    # Verify project exists
    result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Get file record
    result = await db.execute(
        select(ProjectFile)
        .where(ProjectFile.project_id == project_id)
        .where(ProjectFile.filename == filename)
        .where(ProjectFile.is_deleted == False)
    )
    project_file = result.scalar_one_or_none()

    if not project_file:
        raise HTTPException(status_code=404, detail="File not found")

    file_path = Path(project_file.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found on disk")

    return FileResponse(
        file_path,
        filename=project_file.original_filename,
        media_type=project_file.content_type or "application/octet-stream"
    )


@router.delete("/{project_id}/files/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project_file(
    project_id: str,
    file_id: str,
    db: AsyncSession = Depends(get_db)
) -> None:
    """Delete a file from a project's knowledge base."""
    # Verify project exists
    result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Get file record
    result = await db.execute(
        select(ProjectFile)
        .where(ProjectFile.id == file_id)
        .where(ProjectFile.project_id == project_id)
    )
    project_file = result.scalar_one_or_none()

    if not project_file:
        raise HTTPException(status_code=404, detail="File not found")

    # Delete file from disk
    try:
        file_path = Path(project_file.file_path)
        if file_path.exists():
            file_path.unlink()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete file from disk: {str(e)}"
        )

    # Mark as deleted in database
    project_file.is_deleted = True
    await db.commit()
