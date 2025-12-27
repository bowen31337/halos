"""Health check endpoints."""

from datetime import datetime
from typing import Any, Dict
from fastapi import APIRouter
from sqlalchemy import text
from src.core.database import async_session_factory
from src.core.config import settings

router = APIRouter()


async def check_database() -> Dict[str, Any]:
    """Check database connectivity."""
    try:
        async with async_session_factory() as session:
            # Execute a simple query to check connection
            await session.execute(text("SELECT 1"))
            return {
                "status": "healthy",
                "connected": True
            }
    except Exception as e:
        return {
            "status": "unhealthy",
            "connected": False,
            "error": str(e)
        }


async def check_agent_framework() -> Dict[str, Any]:
    """Check agent framework status."""
    try:
        # Check if deepagents is available
        try:
            from deepagents import create_deep_agent
            agent_available = True
        except ImportError:
            agent_available = False

        # Check if API key is configured
        api_key = settings.get_anthropic_api_key()
        has_api_key = api_key is not None and len(api_key) > 0

        return {
            "status": "healthy" if (agent_available and has_api_key) else "degraded",
            "deepagents_available": agent_available,
            "api_key_configured": has_api_key,
            "default_model": settings.default_model
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


@router.get("")
async def health_check() -> Dict[str, Any]:
    """Check API health status including all components."""
    db_status = await check_database()
    agent_status = await check_agent_framework()

    # Overall health is healthy only if all components are healthy
    overall_status = "healthy"
    if db_status["status"] != "healthy" or agent_status["status"] == "unhealthy":
        overall_status = "unhealthy"
    elif agent_status["status"] == "degraded":
        overall_status = "degraded"

    return {
        "status": overall_status,
        "service": "claude-clone-api",
        "version": settings.app_version,
        "timestamp": datetime.utcnow().isoformat(),
        "components": {
            "database": db_status,
            "agent_framework": agent_status
        }
    }
