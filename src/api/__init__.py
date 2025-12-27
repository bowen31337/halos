"""API routes module."""

from fastapi import APIRouter

from src.api.routes import (
    agent,
    artifacts,
    audit,
    auth,
    checkpoints,
    conversation_branching,
    conversations,
    folders,
    health,
    memory,
    messages,
    mcp,
    projects,
    prompts,
    search,
    settings,
    sharing,
    subagents,
    tags,
    tasks,
    usage,
)

router = APIRouter()

# Include all route modules
router.include_router(health.router, prefix="/health", tags=["Health"])
router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
router.include_router(conversations.router, prefix="/conversations", tags=["Conversations"])
router.include_router(conversation_branching.router, prefix="/conversations", tags=["Conversation Branching"])
router.include_router(sharing.router, prefix="/conversations", tags=["Sharing"])

# Message routes - split into two routers for different path patterns
# 1. Conversation-specific: /api/conversations/{id}/messages
router.include_router(messages.conversation_messages_router, prefix="/conversations", tags=["Messages"])
# 2. Message operations: /api/messages/{id}
router.include_router(messages.message_operations_router, prefix="/messages", tags=["Messages"])

router.include_router(agent.router, prefix="/agent", tags=["Agent"])
router.include_router(artifacts.router, prefix="/artifacts", tags=["Artifacts"])
# Checkpoints routes - conversation-specific ops under /conversations, checkpoint ops under /checkpoints
router.include_router(checkpoints.conversation_router, prefix="/conversations", tags=["Checkpoints"])
router.include_router(checkpoints.checkpoint_router, prefix="/checkpoints", tags=["Checkpoints"])
router.include_router(projects.router, prefix="/projects", tags=["Projects"])
router.include_router(folders.router, prefix="/folders", tags=["Folders"])
router.include_router(memory.router, prefix="/memory", tags=["Memory"])
router.include_router(search.router, prefix="/search", tags=["Search"])
router.include_router(settings.router, prefix="/settings", tags=["Settings"])
router.include_router(subagents.router, prefix="/subagents", tags=["SubAgents"])
router.include_router(tasks.router, prefix="/tasks", tags=["Tasks"])
router.include_router(usage.router, prefix="/usage", tags=["Usage"])
router.include_router(prompts.router, prefix="/prompts", tags=["Prompts"])
router.include_router(mcp.router, prefix="/mcp", tags=["MCP"])
router.include_router(audit.router, prefix="/audit", tags=["Audit"])
router.include_router(tags.router, prefix="/tags", tags=["Tags"])
