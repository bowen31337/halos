"""Health check endpoints."""

from fastapi import APIRouter

router = APIRouter()


@router.get("")
async def health_check() -> dict[str, str]:
    """Check API health status."""
    return {
        "status": "healthy",
        "service": "claude-clone-api",
    }
