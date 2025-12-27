"""User settings endpoints."""

import json
from typing import Optional
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel
from sqlalchemy import select
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

