"""Artifact management endpoints."""

from typing import Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

router = APIRouter()


class ArtifactUpdate(BaseModel):
    """Request model for updating an artifact."""

    content: Optional[str] = None
    title: Optional[str] = None


# In-memory storage
artifacts_db: dict[UUID, dict] = {}


@router.get("/conversations/{conversation_id}/artifacts")
async def list_artifacts(conversation_id: UUID) -> list[dict]:
    """List all artifacts in a conversation."""
    return [a for a in artifacts_db.values() if a.get("conversation_id") == str(conversation_id)]


@router.get("/{artifact_id}")
async def get_artifact(artifact_id: UUID) -> dict:
    """Get a specific artifact."""
    if artifact_id not in artifacts_db:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return artifacts_db[artifact_id]


@router.put("/{artifact_id}")
async def update_artifact(artifact_id: UUID, data: ArtifactUpdate) -> dict:
    """Update an artifact."""
    if artifact_id not in artifacts_db:
        raise HTTPException(status_code=404, detail="Artifact not found")

    artifact = artifacts_db[artifact_id]

    if data.content is not None:
        artifact["content"] = data.content
    if data.title is not None:
        artifact["title"] = data.title

    artifact["version"] = artifact.get("version", 1) + 1

    return artifact


@router.delete("/{artifact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_artifact(artifact_id: UUID) -> None:
    """Delete an artifact."""
    if artifact_id not in artifacts_db:
        raise HTTPException(status_code=404, detail="Artifact not found")
    del artifacts_db[artifact_id]


@router.post("/{artifact_id}/fork")
async def fork_artifact(artifact_id: UUID) -> dict:
    """Fork an artifact to create a new version."""
    if artifact_id not in artifacts_db:
        raise HTTPException(status_code=404, detail="Artifact not found")

    from datetime import datetime

    original = artifacts_db[artifact_id]
    new_id = uuid4()

    fork = {
        **original,
        "id": str(new_id),
        "parent_artifact_id": str(artifact_id),
        "version": 1,
        "created_at": datetime.utcnow().isoformat(),
    }

    artifacts_db[new_id] = fork
    return fork


@router.get("/{artifact_id}/versions")
async def get_artifact_versions(artifact_id: UUID) -> list[dict]:
    """Get version history for an artifact."""
    if artifact_id not in artifacts_db:
        raise HTTPException(status_code=404, detail="Artifact not found")

    # Find all artifacts in this version chain
    versions = []
    for a in artifacts_db.values():
        if a.get("parent_artifact_id") == str(artifact_id) or a.get("id") == str(artifact_id):
            versions.append(a)

    return sorted(versions, key=lambda x: x.get("version", 0))


@router.get("/{artifact_id}/download")
async def download_artifact(artifact_id: UUID) -> dict:
    """Download artifact content."""
    if artifact_id not in artifacts_db:
        raise HTTPException(status_code=404, detail="Artifact not found")

    artifact = artifacts_db[artifact_id]
    return {
        "filename": f"{artifact.get('title', 'artifact')}.{artifact.get('language', 'txt')}",
        "content": artifact.get("content", ""),
        "content_type": "text/plain",
    }
