"""Project file management endpoints."""

import os
from pathlib import Path
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.models.project import Project
from src.models.project_file import ProjectFile

router = APIRouter()

# Directory for project files
PROJECT_FILES_DIR = Path("data/project_files")


@router.get("/{project_id}/files")
async def list_project_files(
    project_id: str,
    db: AsyncSession = Depends(get_db)
) -> list[dict]:
    """List all files in a project."""
    # Verify project exists
    result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Get files
    result = await db.execute(
        select(ProjectFile)
        .where(ProjectFile.project_id == project_id)
        .where(ProjectFile.is_deleted == False)
        .order_by(ProjectFile.created_at.desc())
    )
    files = result.scalars().all()

    return [
        {
            "id": f.id,
            "filename": f.filename,
            "original_filename": f.original_filename,
            "file_url": f.file_url,
            "file_size": f.file_size,
            "content_type": f.content_type,
            "created_at": f.created_at.isoformat() if f.created_at else None,
        }
        for f in files
    ]


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

    # Create uploads directory if it doesn't exist
    PROJECT_FILES_DIR.mkdir(parents=True, exist_ok=True)

    # Generate unique filename
    unique_id = str(uuid4())
    file_extension = Path(file.filename).suffix if file.filename else ".txt"
    unique_filename = f"{unique_id}{file_extension}"
    file_path = PROJECT_FILES_DIR / unique_filename

    # Save the file
    try:
        content = await file.read()
        with open(file_path, "wb") as buffer:
            buffer.write(content)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save file: {str(e)}"
        )

    # Extract text content from PDF if possible (basic implementation)
    file_content = None
    if file.content_type == "application/pdf":
        # Try to extract text from PDF (basic implementation)
        try:
            import subprocess
            result = subprocess.run(
                ["pdftotext", str(file_path), "-"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                file_content = result.stdout
        except Exception:
            pass  # PDF extraction is optional

    # Create database record
    project_file = ProjectFile(
        project_id=project_id,
        filename=unique_filename,
        original_filename=file.filename or "unknown",
        file_path=str(file_path),
        file_url=f"/api/projects/{project_id}/files/{unique_filename}/download",
        file_size=len(content),
        content_type=file.content_type,
        content=file_content,
    )

    db.add(project_file)
    await db.commit()
    await db.refresh(project_file)

    return {
        "id": project_file.id,
        "filename": project_file.filename,
        "original_filename": project_file.original_filename,
        "file_url": project_file.file_url,
        "file_size": project_file.file_size,
        "content_type": project_file.content_type,
        "created_at": project_file.created_at.isoformat() if project_file.created_at else None,
    }


@router.get("/{project_id}/files/{filename}/download")
async def download_project_file(
    project_id: str,
    filename: str,
    db: AsyncSession = Depends(get_db)
) -> FileResponse:
    """Download a project file."""
    # Verify project exists
    result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Find the file record
    result = await db.execute(
        select(ProjectFile)
        .where(ProjectFile.project_id == project_id)
        .where(ProjectFile.filename == filename)
        .where(ProjectFile.is_deleted == False)
    )
    project_file = result.scalar_one_or_none()

    if not project_file:
        raise HTTPException(status_code=404, detail="File not found")

    # Check if file exists on disk
    file_path = Path(project_file.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found on disk")

    return FileResponse(
        path=file_path,
        filename=project_file.original_filename,
        media_type=project_file.content_type or "application/octet-stream"
    )


@router.delete("/{project_id}/files/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project_file(
    project_id: str,
    file_id: str,
    db: AsyncSession = Depends(get_db)
) -> None:
    """Delete a file from a project."""
    # Verify project exists
    result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Find the file
    result = await db.execute(
        select(ProjectFile)
        .where(ProjectFile.id == file_id)
        .where(ProjectFile.project_id == project_id)
    )
    project_file = result.scalar_one_or_none()

    if not project_file:
        raise HTTPException(status_code=404, detail="File not found")

    # Mark as deleted (soft delete)
    project_file.is_deleted = True
    await db.commit()


@router.get("/{project_id}/files/{file_id}/content")
async def get_project_file_content(
    project_id: str,
    file_id: str,
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Get the extracted content of a project file."""
    # Verify project exists
    result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Find the file
    result = await db.execute(
        select(ProjectFile)
        .where(ProjectFile.id == file_id)
        .where(ProjectFile.project_id == project_id)
        .where(ProjectFile.is_deleted == False)
    )
    project_file = result.scalar_one_or_none()

    if not project_file:
        raise HTTPException(status_code=404, detail="File not found")

    return {
        "id": project_file.id,
        "filename": project_file.filename,
        "content": project_file.content,
    }
