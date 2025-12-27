"""Artifact management endpoints."""

import re
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.models.artifact import Artifact
from src.models.conversation import Conversation

router = APIRouter()


class ArtifactUpdate(BaseModel):
    """Request model for updating an artifact."""
    content: Optional[str] = None
    title: Optional[str] = None


class ArtifactDetectionRequest(BaseModel):
    """Request model for detecting artifacts in content."""
    content: str
    conversation_id: Optional[str] = None


class ArtifactCreate(BaseModel):
    """Request model for creating an artifact."""
    content: str
    title: str
    language: str
    conversation_id: Optional[str] = None


# Language detection mapping
LANGUAGE_ALIASES = {
    "javascript": "js",
    "typescript": "ts",
    "python": "py",
    "java": "java",
    "cpp": "cpp",
    "c++": "cpp",
    "csharp": "cs",
    "c#": "cs",
    "go": "go",
    "rust": "rs",
    "ruby": "rb",
    "php": "php",
    "swift": "swift",
    "kotlin": "kt",
    "html": "html",
    "css": "css",
    "json": "json",
    "yaml": "yaml",
    "markdown": "md",
    "bash": "bash",
    "shell": "bash",
    "sql": "sql",
    "graphql": "graphql",
    "xml": "xml",
}

# React/JSX specific detection
REACT_PATTERNS = [
    r"import\s+.*React",
    r"export\s+default\s+function\s+\w+\([^)]*\)\s*{[^}]*return[^}]*<",
    r"const\s+\w+\s*=\s*\([^)]*\)\s*=>\s*{[^}]*return[^}]*<",
    r"function\s+\w+\([^)]*\)\s*{[^}]*return[^}]*<",
    r"jsx",
    r"tsx",
]


def detect_language(code: str, language_hint: str = "") -> str:
    """Detect the programming language of a code block."""
    # Check for React/JSX patterns first (highest priority)
    for pattern in REACT_PATTERNS:
        if re.search(pattern, code, re.IGNORECASE):
            return "React/JSX"

    # If language hint is provided, use it
    if language_hint:
        normalized = language_hint.lower().strip()
        return LANGUAGE_ALIASES.get(normalized, normalized)

    # Simple heuristics
    if "def " in code and ":" in code and "import " not in code:
        return "python"
    if "function " in code or "=> " in code or "let " in code or "const " in code:
        return "javascript"
    if "public class " in code or "System.out.println" in code:
        return "java"
    if "#include " in code or "std::" in code:
        return "cpp"
    if "package " in code and "func " in code:
        return "go"

    return "code"


def extract_title_from_code(code: str, language: str) -> str:
    """Extract a meaningful title from code content."""
    # Look for function/class names
    patterns = [
        r"function\s+(\w+)",  # function myFunction() { ... }
        r"const\s+(\w+)\s*=\s*\(",  # const MyComponent = ({ ... })
        r"export\s+default\s+function\s+(\w+)",  # export default function MyComponent()
        r"class\s+(\w+)",  # class MyClass { ... }
        r"def\s+(\w+)",  # def my_function(): ...
    ]

    for pattern in patterns:
        match = re.search(pattern, code)
        if match:
            name = match.group(1)
            # Capitalize for components
            if language == "React/JSX" and name[0].islower():
                name = name[0].upper() + name[1:]
            return name

    # Fallback: extract first line or use generic name
    first_line = code.strip().split('\n')[0]
    if len(first_line) < 50:
        return first_line.strip().strip('/*#').strip()

    return "Code Artifact"


def extract_code_blocks(content: str) -> list[dict]:
    """Extract code blocks from markdown content."""
    # Pattern to match code blocks with optional language
    # ```language
    # code
    # ```
    pattern = r"```(\w+)?\n(.*?)\n```"
    matches = re.findall(pattern, content, re.DOTALL)

    artifacts = []
    for language_hint, code in matches:
        if not code.strip():
            continue

        language = detect_language(code, language_hint)
        title = extract_title_from_code(code, language)

        # Auto-detect artifact type from language
        language_lower = language.lower()
        if language_lower in ["html", "htm"]:
            artifact_type = "html"
        elif language_lower in ["svg"]:
            artifact_type = "svg"
        elif language_lower in ["mermaid"]:
            artifact_type = "mermaid"
        elif language_lower in ["latex", "tex"]:
            artifact_type = "latex"
        else:
            artifact_type = "code"

        artifacts.append({
            "content": code,
            "language": language,
            "title": title,
            "artifact_type": artifact_type,
        })

    return artifacts


@router.post("/detect")
async def detect_artifacts(request: ArtifactDetectionRequest) -> list[dict]:
    """Detect code artifacts in content (markdown code blocks)."""
    artifacts = extract_code_blocks(request.content)
    return artifacts


@router.post("/create", status_code=status.HTTP_201_CREATED)
async def create_artifact(data: ArtifactCreate, db: AsyncSession = Depends(get_db)) -> dict:
    """Create a new artifact."""
    # Verify conversation exists if provided
    if data.conversation_id:
        result = await db.execute(
            select(Conversation).where(Conversation.id == data.conversation_id)
        )
        conversation = result.scalar_one_or_none()
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

    # Auto-detect artifact type from language
    language_lower = data.language.lower()
    if language_lower in ["html", "htm"]:
        artifact_type = "html"
    elif language_lower in ["svg"]:
        artifact_type = "svg"
    elif language_lower in ["mermaid"]:
        artifact_type = "mermaid"
    elif language_lower in ["latex", "tex"]:
        artifact_type = "latex"
    else:
        artifact_type = "code"

    artifact = Artifact(
        conversation_id=data.conversation_id,
        content=data.content,
        title=data.title,
        language=data.language,
        artifact_type=artifact_type,
    )

    db.add(artifact)
    await db.commit()
    await db.refresh(artifact)

    return {
        "id": artifact.id,
        "conversation_id": artifact.conversation_id,
        "title": artifact.title,
        "content": artifact.content,
        "language": artifact.language,
        "artifact_type": artifact.artifact_type,
        "version": artifact.version,
        "created_at": artifact.created_at.isoformat() if artifact.created_at else None,
    }


@router.get("/conversations/{conversation_id}/artifacts")
async def list_artifacts(conversation_id: str, db: AsyncSession = Depends(get_db)) -> list[dict]:
    """List all artifacts in a conversation."""
    # Verify conversation exists
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Get artifacts
    result = await db.execute(
        select(Artifact)
        .where(Artifact.conversation_id == conversation_id)
        .where(Artifact.is_deleted == False)
        .where(Artifact.is_archived == False)
        .order_by(Artifact.created_at.desc())
    )
    artifacts = result.scalars().all()

    return [
        {
            "id": a.id,
            "conversation_id": a.conversation_id,
            "title": a.title,
            "content": a.content,
            "language": a.language,
            "artifact_type": a.artifact_type,
            "version": a.version,
            "created_at": a.created_at.isoformat() if a.created_at else None,
        }
        for a in artifacts
    ]


@router.get("/{artifact_id}")
async def get_artifact(artifact_id: str, db: AsyncSession = Depends(get_db)) -> dict:
    """Get a specific artifact."""
    result = await db.execute(
        select(Artifact).where(Artifact.id == artifact_id).where(Artifact.is_deleted == False)
    )
    artifact = result.scalar_one_or_none()

    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")

    return {
        "id": artifact.id,
        "conversation_id": artifact.conversation_id,
        "title": artifact.title,
        "content": artifact.content,
        "language": artifact.language,
        "artifact_type": artifact.artifact_type,
        "version": artifact.version,
        "parent_artifact_id": artifact.parent_artifact_id,
        "created_at": artifact.created_at.isoformat() if artifact.created_at else None,
    }


@router.put("/{artifact_id}")
async def update_artifact(artifact_id: str, data: ArtifactUpdate, db: AsyncSession = Depends(get_db)) -> dict:
    """Update an artifact."""
    result = await db.execute(
        select(Artifact).where(Artifact.id == artifact_id).where(Artifact.is_deleted == False)
    )
    artifact = result.scalar_one_or_none()

    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")

    if data.content is not None:
        artifact.content = data.content
    if data.title is not None:
        artifact.title = data.title

    artifact.version = artifact.version + 1

    await db.commit()
    await db.refresh(artifact)

    return {
        "id": artifact.id,
        "conversation_id": artifact.conversation_id,
        "title": artifact.title,
        "content": artifact.content,
        "language": artifact.language,
        "artifact_type": artifact.artifact_type,
        "version": artifact.version,
        "created_at": artifact.created_at.isoformat() if artifact.created_at else None,
    }


@router.delete("/{artifact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_artifact(artifact_id: str, db: AsyncSession = Depends(get_db)) -> None:
    """Delete an artifact (soft delete)."""
    result = await db.execute(
        select(Artifact).where(Artifact.id == artifact_id).where(Artifact.is_deleted == False)
    )
    artifact = result.scalar_one_or_none()

    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")

    artifact.is_deleted = True
    await db.commit()


@router.post("/{artifact_id}/fork")
async def fork_artifact(artifact_id: str, db: AsyncSession = Depends(get_db)) -> dict:
    """Fork an artifact to create a new version."""
    result = await db.execute(
        select(Artifact).where(Artifact.id == artifact_id).where(Artifact.is_deleted == False)
    )
    original = result.scalar_one_or_none()

    if not original:
        raise HTTPException(status_code=404, detail="Artifact not found")

    new_artifact = Artifact(
        conversation_id=original.conversation_id,
        content=original.content,
        title=original.title,
        language=original.language,
        artifact_type=original.artifact_type,
        parent_artifact_id=artifact_id,
        version=1,
    )

    db.add(new_artifact)
    await db.commit()
    await db.refresh(new_artifact)

    return {
        "id": new_artifact.id,
        "conversation_id": new_artifact.conversation_id,
        "title": new_artifact.title,
        "content": new_artifact.content,
        "language": new_artifact.language,
        "artifact_type": new_artifact.artifact_type,
        "version": new_artifact.version,
        "parent_artifact_id": new_artifact.parent_artifact_id,
        "created_at": new_artifact.created_at.isoformat() if new_artifact.created_at else None,
    }


@router.get("/{artifact_id}/versions")
async def get_artifact_versions(artifact_id: str, db: AsyncSession = Depends(get_db)) -> list[dict]:
    """Get version history for an artifact."""
    result = await db.execute(
        select(Artifact).where(Artifact.id == artifact_id).where(Artifact.is_deleted == False)
    )
    original = result.scalar_one_or_none()

    if not original:
        raise HTTPException(status_code=404, detail="Artifact not found")

    # Get all versions (original and forks)
    result = await db.execute(
        select(Artifact)
        .where(
            (Artifact.parent_artifact_id == artifact_id) |
            (Artifact.id == artifact_id)
        )
        .where(Artifact.is_deleted == False)
        .order_by(Artifact.version)
    )
    versions = result.scalars().all()

    return [
        {
            "id": v.id,
            "conversation_id": v.conversation_id,
            "title": v.title,
            "content": v.content,
            "language": v.language,
            "artifact_type": v.artifact_type,
            "version": v.version,
            "parent_artifact_id": v.parent_artifact_id,
            "created_at": v.created_at.isoformat() if v.created_at else None,
        }
        for v in versions
    ]


@router.get("/{artifact_id}/download")
async def download_artifact(artifact_id: str, db: AsyncSession = Depends(get_db)) -> dict:
    """Download artifact content."""
    result = await db.execute(
        select(Artifact).where(Artifact.id == artifact_id).where(Artifact.is_deleted == False)
    )
    artifact = result.scalar_one_or_none()

    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")

    return {
        "filename": f"{artifact.title or 'artifact'}.{artifact.language or 'txt'}",
        "content": artifact.content,
        "content_type": "text/plain",
    }
