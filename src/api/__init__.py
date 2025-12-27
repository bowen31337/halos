"""API routes module."""

from fastapi import APIRouter

from src.api.routes import (
    agent,
    artifacts,
    auth,
    checkpoints,
    conversation_branching,
    conversations,
    health,
    memory,
    messages,
    projects,
    search,
    settings,
    usage,
)

router = APIRouter()

# Include all route modules
router.include_router(health.router, prefix="/health", tags=["Health"])
router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
router.include_router(conversations.router, prefix="/conversations", tags=["Conversations"])
router.include_router(conversation_branching.router, prefix="/conversations", tags=["Conversation Branching"])
router.include_router(messages.router, prefix="/messages", tags=["Messages"])
router.include_router(agent.router, prefix="/agent", tags=["Agent"])
router.include_router(artifacts.router, prefix="/artifacts", tags=["Artifacts"])
router.include_router(checkpoints.router, prefix="/checkpoints", tags=["Checkpoints"])
router.include_router(projects.router, prefix="/projects", tags=["Projects"])
router.include_router(memory.router, prefix="/memory", tags=["Memory"])
router.include_router(search.router, prefix="/search", tags=["Search"])
router.include_router(settings.router, prefix="/settings", tags=["Settings"])
router.include_router(usage.router, prefix="/usage", tags=["Usage"])
