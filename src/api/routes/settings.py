"""User settings endpoints."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.models.conversation import Conversation
from src.models.project import Project

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

