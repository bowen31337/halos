"""Project management endpoints."""

from typing import Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

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


# In-memory storage
projects_db: dict[UUID, dict] = {}
project_files_db: dict[UUID, list[dict]] = {}


@router.get("")
async def list_projects(archived: bool = False) -> list[dict]:
    """List all projects."""
    return [p for p in projects_db.values() if p.get("is_archived", False) == archived]


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_project(data: ProjectCreate) -> dict:
    """Create a new project."""
    from datetime import datetime

    project_id = uuid4()
    now = datetime.utcnow().isoformat()

    project = {
        "id": str(project_id),
        "name": data.name,
        "description": data.description,
        "color": data.color,
        "icon": data.icon,
        "custom_instructions": data.custom_instructions,
        "is_archived": False,
        "is_pinned": False,
        "created_at": now,
        "updated_at": now,
    }

    projects_db[project_id] = project
    project_files_db[project_id] = []
    return project


@router.get("/{project_id}")
async def get_project(project_id: UUID) -> dict:
    """Get a specific project."""
    if project_id not in projects_db:
        raise HTTPException(status_code=404, detail="Project not found")
    return projects_db[project_id]


@router.put("/{project_id}")
async def update_project(project_id: UUID, data: ProjectUpdate) -> dict:
    """Update a project."""
    if project_id not in projects_db:
        raise HTTPException(status_code=404, detail="Project not found")

    from datetime import datetime

    project = projects_db[project_id]

    if data.name is not None:
        project["name"] = data.name
    if data.description is not None:
        project["description"] = data.description
    if data.color is not None:
        project["color"] = data.color
    if data.icon is not None:
        project["icon"] = data.icon
    if data.custom_instructions is not None:
        project["custom_instructions"] = data.custom_instructions
    if data.is_archived is not None:
        project["is_archived"] = data.is_archived

    project["updated_at"] = datetime.utcnow().isoformat()

    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(project_id: UUID) -> None:
    """Delete a project."""
    if project_id not in projects_db:
        raise HTTPException(status_code=404, detail="Project not found")
    del projects_db[project_id]
    if project_id in project_files_db:
        del project_files_db[project_id]


@router.get("/{project_id}/files")
async def list_project_files(project_id: UUID) -> list[dict]:
    """List files in a project."""
    if project_id not in projects_db:
        raise HTTPException(status_code=404, detail="Project not found")
    return project_files_db.get(project_id, [])


@router.post("/{project_id}/files", status_code=status.HTTP_201_CREATED)
async def upload_project_file(project_id: UUID) -> dict:
    """Upload a file to a project."""
    if project_id not in projects_db:
        raise HTTPException(status_code=404, detail="Project not found")

    from datetime import datetime

    # TODO: Handle actual file upload
    file_id = uuid4()
    now = datetime.utcnow().isoformat()

    file_entry = {
        "id": str(file_id),
        "project_id": str(project_id),
        "filename": "placeholder.txt",
        "file_type": "text",
        "size_bytes": 0,
        "created_at": now,
    }

    project_files_db.setdefault(project_id, []).append(file_entry)
    return file_entry


@router.delete("/{project_id}/files/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project_file(project_id: UUID, file_id: UUID) -> None:
    """Delete a file from a project."""
    if project_id not in projects_db:
        raise HTTPException(status_code=404, detail="Project not found")

    files = project_files_db.get(project_id, [])
    for i, f in enumerate(files):
        if f["id"] == str(file_id):
            del files[i]
            return

    raise HTTPException(status_code=404, detail="File not found")


@router.get("/{project_id}/conversations")
async def list_project_conversations(project_id: UUID) -> list[dict]:
    """List all conversations in a project."""
    if project_id not in projects_db:
        raise HTTPException(status_code=404, detail="Project not found")

    # TODO: Implement with actual conversations DB
    return []
