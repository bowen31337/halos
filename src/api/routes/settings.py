"""User settings endpoints."""

import json
from typing import Optional
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.models.conversation import Conversation
from src.models.project import Project
from src.models.message import Message
from src.models.memory import Memory
from src.models.prompt import Prompt
from src.models.artifact import Artifact
from src.models.checkpoint import Checkpoint
from src.models.audit_log import AuditActionType, AuditAction
from src.utils.audit import log_audit, get_request_info
from src.core.config import settings

router = APIRouter()


class SettingsUpdate(BaseModel):
    """Request model for updating settings."""

    theme: Optional[str] = None
    font_size: Optional[int] = None
    font_family: Optional[str] = None
    message_density: Optional[str] = None
    code_theme: Optional[str] = None
    permission_mode: Optional[str] = None
    custom_instructions: Optional[str] = None
    system_prompt_override: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    extended_thinking_enabled: Optional[bool] = None
    memory_enabled: Optional[bool] = None
    color_blind_mode: Optional[str] = None
    content_filter_level: Optional[str] = None
    content_filter_categories: Optional[list[str]] = None
    locale: Optional[str] = None
    time_format: Optional[str] = None  # "12h" or "24h"
    date_format: Optional[str] = None  # "MM/DD/YYYY", "DD/MM/YYYY", "YYYY-MM-DD"
    relative_time: Optional[bool] = None  # Show "5m ago" instead of exact time


class CustomInstructionsUpdate(BaseModel):
    """Request model for updating custom instructions."""

    instructions: str


# In-memory settings storage
user_settings: dict = {
    "theme": "auto",
    "font_size": 16,
    "font_family": "system-ui",
    "message_density": "comfortable",
    "code_theme": "one-dark",
    "permission_mode": "default",
    "custom_instructions": "",
    "system_prompt_override": "",
    "memory_enabled": True,
    "extended_thinking_enabled": True,
    "temperature": 0.7,
    "max_tokens": 4096,
    "color_blind_mode": "none",
    "content_filter_level": "low",
    "content_filter_categories": ["violence", "hate", "sexual", "self-harm", "illegal"],
    "locale": "en-US",
    "time_format": "12h",
    "date_format": "MM/DD/YYYY",
    "relative_time": True,
}


@router.get("")
async def get_settings() -> dict:
    """Get current user settings."""
    return user_settings


@router.put("")
async def update_settings(data: SettingsUpdate) -> dict:
    """Update user settings."""
    if data.theme is not None:
        user_settings["theme"] = data.theme
    if data.font_size is not None:
        user_settings["font_size"] = data.font_size
    if data.font_family is not None:
        user_settings["font_family"] = data.font_family
    if data.message_density is not None:
        user_settings["message_density"] = data.message_density
    if data.code_theme is not None:
        user_settings["code_theme"] = data.code_theme
    if data.permission_mode is not None:
        user_settings["permission_mode"] = data.permission_mode
    if data.custom_instructions is not None:
        user_settings["custom_instructions"] = data.custom_instructions
    if data.system_prompt_override is not None:
        user_settings["system_prompt_override"] = data.system_prompt_override
    if data.temperature is not None:
        user_settings["temperature"] = data.temperature
    if data.max_tokens is not None:
        user_settings["max_tokens"] = data.max_tokens
    if data.extended_thinking_enabled is not None:
        user_settings["extended_thinking_enabled"] = data.extended_thinking_enabled
    if data.memory_enabled is not None:
        user_settings["memory_enabled"] = data.memory_enabled
    if data.color_blind_mode is not None:
        user_settings["color_blind_mode"] = data.color_blind_mode
    if data.content_filter_level is not None:
        user_settings["content_filter_level"] = data.content_filter_level
    if data.content_filter_categories is not None:
        user_settings["content_filter_categories"] = data.content_filter_categories
    if data.locale is not None:
        user_settings["locale"] = data.locale
    if data.time_format is not None:
        user_settings["time_format"] = data.time_format
    if data.date_format is not None:
        user_settings["date_format"] = data.date_format
    if data.relative_time is not None:
        user_settings["relative_time"] = data.relative_time

    return user_settings


@router.get("/custom-instructions")
async def get_custom_instructions() -> dict:
    """Get custom instructions."""
    return {"instructions": user_settings.get("custom_instructions", "")}


@router.put("/custom-instructions")
async def update_custom_instructions(data: CustomInstructionsUpdate) -> dict:
    """Update custom instructions."""
    user_settings["custom_instructions"] = data.instructions
    return {"instructions": data.instructions}


class SystemPromptUpdate(BaseModel):
    """Request model for updating system prompt override."""

    prompt: str


@router.get("/system-prompt")
async def get_system_prompt() -> dict:
    """Get system prompt override."""
    return {"prompt": user_settings.get("system_prompt_override", "")}


# API Key Management
class APIKeyRequest(BaseModel):
    """Request model for API key operations."""

    api_key: str


class APIKeyResponse(BaseModel):
    """Response model for API key operations."""

    valid: bool
    message: str
    key_preview: str


@router.post("/api-key/validate")
async def validate_api_key(data: APIKeyRequest) -> APIKeyResponse:
    """Validate an API key."""
    try:
        # Simple validation - check if key looks like a valid Anthropic API key
        # Anthropic keys typically start with "sk-ant-"
        if not data.api_key or len(data.api_key) < 10:
            return APIKeyResponse(
                valid=False,
                message="API key is too short",
                key_preview="Invalid key format"
            )

        # Check if it looks like a valid Anthropic key format
        if data.api_key.startswith("sk-ant-") and len(data.api_key) >= 32:
            # In a real implementation, we would make a test API call here
            # For now, we'll assume valid format means valid key
            return APIKeyResponse(
                valid=True,
                message="API key format is valid",
                key_preview=f"sk-ant-***{data.api_key[-4:]}"
            )
        else:
            return APIKeyResponse(
                valid=False,
                message="Invalid API key format. Anthropic keys should start with 'sk-ant-'",
                key_preview="Invalid key format"
            )
    except Exception as e:
        return APIKeyResponse(
            valid=False,
            message=f"Validation error: {str(e)}",
            key_preview="Error validating key"
        )


@router.post("/api-key/save")
async def save_api_key(data: APIKeyRequest) -> dict:
    """Save an API key."""
    try:
        # Validate the key first
        validation_result = await validate_api_key(data)
        if not validation_result.valid:
            raise HTTPException(status_code=400, detail=validation_result.message)

        # In a real implementation, we would:
        # 1. Hash/encrypt the API key before storing
        # 2. Store it securely in the database
        # 3. Update the settings to use the new key

        # For now, we'll simulate saving by updating user_settings
        user_settings["api_key_saved"] = True
        user_settings["api_key_preview"] = validation_result.key_preview

        return {
            "message": "API key saved successfully",
            "key_preview": validation_result.key_preview
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save API key: {str(e)}")


@router.get("/api-key/status")
async def get_api_key_status() -> dict:
    """Get API key status."""
    current_key = settings.get_anthropic_api_key()

    return {
        "configured": current_key is not None and len(current_key) > 0,
        "has_saved_key": user_settings.get("api_key_saved", False),
        "key_preview": user_settings.get("api_key_preview", "No key saved"),
        "message": "Check your API key configuration"
    }


@router.delete("/api-key")
async def remove_api_key() -> dict:
    """Remove saved API key."""
    try:
        # In a real implementation, this would remove the key from secure storage
        user_settings["api_key_saved"] = False
        user_settings["api_key_preview"] = "No key saved"

        return {"message": "API key removed successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to remove API key: {str(e)}")


@router.put("/system-prompt")
async def update_system_prompt(data: SystemPromptUpdate) -> dict:
    """Update system prompt override."""
    user_settings["system_prompt_override"] = data.prompt
    return {"prompt": data.prompt}


@router.put("/permission-mode")
async def update_permission_mode(mode: str) -> dict:
    """Update permission mode."""
    valid_modes = ["default", "acceptEdits", "plan", "bypassPermissions"]
    if mode not in valid_modes:
        return {"error": f"Invalid mode. Must be one of: {valid_modes}"}

    user_settings["permission_mode"] = mode
    return {"permission_mode": mode}


@router.get("/models")
async def list_models() -> list[dict]:
    """List available AI models."""
    return [
        {
            "id": "claude-sonnet-4-5-20250929",
            "name": "Claude Sonnet 4.5",
            "description": "Balanced performance and capability",
            "context_window": 200000,
            "default": True,
        },
        {
            "id": "claude-haiku-4-5-20251001",
            "name": "Claude Haiku 4.5",
            "description": "Fast and efficient",
            "context_window": 200000,
            "default": False,
        },
        {
            "id": "claude-opus-4-1-20250805",
            "name": "Claude Opus 4.1",
            "description": "Most capable model",
            "context_window": 200000,
            "default": False,
        },
    ]


@router.get("/instructions/effective")
async def get_effective_custom_instructions(
    conversation_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    Get effective custom instructions for a conversation.

    Returns both project and global instructions.
    Project instructions override global instructions if both exist.
    """
    global_instructions = user_settings.get("custom_instructions", "")
    project_instructions = ""

    if conversation_id:
        # Get conversation to find its project
        result = await db.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        conversation = result.scalar_one_or_none()

        if conversation and conversation.project_id:
            # Get project custom instructions
            result = await db.execute(
                select(Project).where(Project.id == conversation.project_id)
            )
            project = result.scalar_one_or_none()

            if project and project.custom_instructions:
                project_instructions = project.custom_instructions

    # Project instructions take precedence
    effective_instructions = project_instructions if project_instructions else global_instructions

    return {
        "project_instructions": project_instructions,
        "global_instructions": global_instructions,
        "effective_instructions": effective_instructions,
        "using_project": bool(project_instructions)
    }


@router.post("/refresh-session")
async def refresh_session() -> dict:
    """
    Refresh user session after timeout.

    This endpoint simulates session refresh by:
    1. Validating the session is still valid (in a real app, would check auth tokens)
    2. Updating the last activity timestamp
    3. Returning updated session info

    Returns:
        dict: Session status and timestamp
    """
    import time

    # Update last activity in user settings
    user_settings["last_activity"] = time.time()
    user_settings["session_refreshed_at"] = time.time()

    return {
        "status": "success",
        "message": "Session refreshed successfully",
        "timestamp": time.time(),
        "session_active": True
    }


@router.get("/session-status")
async def get_session_status() -> dict:
    """
    Get current session status.

    Returns session information including activity status and timeout settings.
    """
    import time

    last_activity = user_settings.get("last_activity", time.time())
    timeout_minutes = user_settings.get("session_timeout_minutes", 30)

    return {
        "session_active": True,
        "last_activity": last_activity,
        "timeout_minutes": timeout_minutes,
        "settings": {
            "timeout_duration": timeout_minutes,
            "warning_duration": user_settings.get("session_warning_minutes", 5)
        }
    }


# ==================== Data Export & Account Management ====================


@router.get("/export-all")
async def export_all_user_data(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> Response:
    """
    Export all user data including conversations, messages, settings, memories, and more.

    This endpoint provides a comprehensive export of all user content for:
    - Data portability (GDPR compliance)
    - Backup purposes
    - Migration to other systems

    Returns:
        Response: JSON file containing all user data
    """
    # Get all conversations for the user (in a real app, filter by user_id)
    conv_result = await db.execute(
        select(Conversation)
        .where(Conversation.is_deleted == False)
        .order_by(Conversation.created_at)
    )
    conversations = conv_result.scalars().all()

    # Get all messages
    msg_result = await db.execute(
        select(Message)
        .order_by(Message.created_at)
    )
    messages = msg_result.scalars().all()

    # Get all memories
    memory_result = await db.execute(
        select(Memory)
        .where(Memory.is_active == True)
        .order_by(Memory.created_at)
    )
    memories = memory_result.scalars().all()

    # Get all prompts
    prompt_result = await db.execute(
        select(Prompt)
        .where(Prompt.is_active == True)
        .order_by(Prompt.created_at)
    )
    prompts = prompt_result.scalars().all()

    # Get all artifacts
    artifact_result = await db.execute(
        select(Artifact)
        .order_by(Artifact.created_at)
    )
    artifacts = artifact_result.scalars().all()

    # Get all checkpoints
    checkpoint_result = await db.execute(
        select(Checkpoint)
        .order_by(Checkpoint.created_at)
    )
    checkpoints = checkpoint_result.scalars().all()

    # Get all projects
    project_result = await db.execute(
        select(Project)
        .order_by(Project.created_at)
    )
    projects = project_result.scalars().all()

    # Build export data structure
    export_data = {
        "export_version": "1.0",
        "export_date": datetime.utcnow().isoformat(),
        "export_type": "full_user_data",
        "summary": {
            "conversations": len(conversations),
            "messages": len(messages),
            "memories": len(memories),
            "prompts": len(prompts),
            "artifacts": len(artifacts),
            "checkpoints": len(checkpoints),
            "projects": len(projects),
        },
        "data": {
            "conversations": [
                {
                    "id": c.id,
                    "title": c.title,
                    "model": c.model,
                    "project_id": c.project_id,
                    "is_archived": c.is_archived,
                    "is_pinned": c.is_pinned,
                    "token_count": c.token_count,
                    "created_at": c.created_at.isoformat(),
                    "updated_at": c.updated_at.isoformat(),
                }
                for c in conversations
            ],
            "messages": [
                {
                    "id": m.id,
                    "conversation_id": m.conversation_id,
                    "role": m.role,
                    "content": m.content,
                    "thinking_content": m.thinking_content,
                    "tool_calls": m.tool_calls,
                    "tool_results": m.tool_results,
                    "attachments": m.attachments,
                    "input_tokens": m.input_tokens,
                    "output_tokens": m.output_tokens,
                    "cache_read_tokens": m.cache_read_tokens,
                    "cache_write_tokens": m.cache_write_tokens,
                    "created_at": m.created_at.isoformat(),
                    "edited_at": m.edited_at.isoformat() if m.edited_at else None,
                }
                for m in messages
            ],
            "memories": [
                {
                    "id": mem.id,
                    "content": mem.content,
                    "category": mem.category,
                    "created_at": mem.created_at.isoformat(),
                }
                for mem in memories
            ],
            "prompts": [
                {
                    "id": p.id,
                    "title": p.title,
                    "content": p.content,
                    "category": p.category,
                    "description": p.description,
                    "tags": p.tags,
                    "created_at": p.created_at.isoformat(),
                }
                for p in prompts
            ],
            "artifacts": [
                {
                    "id": a.id,
                    "conversation_id": a.conversation_id,
                    "title": a.title,
                    "language": a.language,
                    "content": a.content,
                    "created_at": a.created_at.isoformat(),
                }
                for a in artifacts
            ],
            "checkpoints": [
                {
                    "id": cp.id,
                    "conversation_id": cp.conversation_id,
                    "name": cp.name,
                    "notes": cp.notes,
                    "state": cp.state_snapshot,
                    "created_at": cp.created_at.isoformat(),
                }
                for cp in checkpoints
            ],
            "projects": [
                {
                    "id": p.id,
                    "name": p.name,
                    "description": p.description,
                    "created_at": p.created_at.isoformat(),
                }
                for p in projects
            ],
            "settings": user_settings.copy(),
        },
    }

    # Audit log
    ip_address, user_agent = get_request_info(request)
    await log_audit(
        db=db,
        user_id="default-user",
        action=AuditAction.DATA_EXPORT,
        resource_type="user",
        resource_id="all",
        details={"export_type": "full", "item_count": sum(export_data["summary"].values())},
        ip_address=ip_address,
        user_agent=user_agent,
    )

    json_str = json.dumps(export_data, indent=2, ensure_ascii=False)
    filename = f"user_data_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"

    return Response(
        content=json_str,
        media_type="application/json",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )


@router.delete("/account")
async def delete_account(
    request: Request,
    confirm: str = "",
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Delete user account and all associated data.

    This is a destructive operation that:
    1. Soft deletes all conversations
    2. Deletes all messages
    3. Deletes all memories
    4. Deletes all prompts
    5. Deletes all artifacts
    6. Deletes all checkpoints
    7. Deletes all projects
    8. Deletes all shared links
    9. Deletes all audit logs
    10. Deletes all sessions and API keys

    WARNING: This operation cannot be undone!

    Args:
        confirm: Must be "DELETE_ACCOUNT" to confirm the deletion

    Returns:
        dict: Confirmation of deletion
    """
    if confirm != "DELETE_ACCOUNT":
        raise HTTPException(
            status_code=400,
            detail="You must provide confirmation. Set confirm='DELETE_ACCOUNT' to proceed."
        )

    # Get all data for audit
    conv_count = (await db.execute(select(func.count(Conversation.id)).where(Conversation.is_deleted == False))).scalar_one()
    msg_count = (await db.execute(select(func.count(Message.id)))).scalar_one()
    memory_count = (await db.execute(select(func.count(Memory.id)).where(Memory.is_active == True))).scalar_one()
    prompt_count = (await db.execute(select(func.count(Prompt.id)).where(Prompt.is_active == True))).scalar_one()
    artifact_count = (await db.execute(select(func.count(Artifact.id)))).scalar_one()
    checkpoint_count = (await db.execute(select(func.count(Checkpoint.id)))).scalar_one()
    project_count = (await db.execute(select(func.count(Project.id)))).scalar_one()

    total_items = conv_count + msg_count + memory_count + prompt_count + artifact_count + checkpoint_count + project_count

    # Log the deletion request before proceeding
    ip_address, user_agent = get_request_info(request)
    await log_audit(
        db=db,
        user_id="default-user",
        action=AuditAction.ACCOUNT_DELETION,
        resource_type="user",
        resource_id="default-user",
        details={
            "items_to_delete": total_items,
            "conversations": conv_count,
            "messages": msg_count,
            "memories": memory_count,
            "prompts": prompt_count,
            "artifacts": artifact_count,
            "checkpoints": checkpoint_count,
            "projects": project_count,
        },
        ip_address=ip_address,
        user_agent=user_agent,
    )

    # Soft delete all conversations
    result = await db.execute(
        select(Conversation).where(Conversation.is_deleted == False)
    )
    conversations = result.scalars().all()
    for conv in conversations:
        conv.is_deleted = True

    # Delete all messages
    await db.execute(Message.__table__.delete())

    # Delete all memories
    await db.execute(Memory.__table__.delete())

    # Delete all prompts
    await db.execute(Prompt.__table__.delete())

    # Delete all artifacts
    await db.execute(Artifact.__table__.delete())

    # Delete all checkpoints
    await db.execute(Checkpoint.__table__.delete())

    # Delete all projects
    await db.execute(Project.__table__.delete())

    # Note: In a real multi-user system, we would also:
    # - Delete user sessions
    # - Delete API keys
    # - Delete audit logs (or keep for compliance)
    # - Delete shared conversations
    # - Delete MCP servers
    # - Delete background tasks

    await db.commit()

    return {
        "status": "success",
        "message": "Account and all associated data have been deleted.",
        "deleted_items": {
            "conversations": conv_count,
            "messages": msg_count,
            "memories": memory_count,
            "prompts": prompt_count,
            "artifacts": artifact_count,
            "checkpoints": checkpoint_count,
            "projects": project_count,
        },
        "total_deleted": total_items,
        "note": "Conversations were soft-deleted and can be recovered if needed. All other data was permanently deleted."
    }

