"""Search endpoints."""

from typing import Optional

from fastapi import APIRouter

router = APIRouter()


@router.get("/conversations")
async def search_conversations(
    q: str,
    project_id: Optional[str] = None,
) -> list[dict]:
    """Search conversations by title and content."""
    # TODO: Implement with actual database
    return []


@router.get("/messages")
async def search_messages(
    q: str,
    conversation_id: Optional[str] = None,
) -> list[dict]:
    """Search messages by content."""
    # TODO: Implement with actual database
    return []


@router.get("/files")
async def search_files(q: str) -> list[dict]:
    """Search files using grep-like pattern matching."""
    # TODO: Implement with file system search
    return []


@router.get("/global")
async def global_search(q: str) -> dict:
    """Search across all content types."""
    return {
        "conversations": [],
        "messages": [],
        "files": [],
        "memories": [],
    }
