"""Activity logging utility functions."""

from datetime import datetime
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from src.models.activity_log import ActivityLog


async def log_activity(
    db: AsyncSession,
    user_id: str,
    activity_type: str,
    description: str,
    entity_id: Optional[str] = None,
    entity_type: Optional[str] = None,
    metadata: Optional[dict] = None
) -> ActivityLog:
    """Log a user activity.

    Args:
        db: Database session
        user_id: User who performed the action
        activity_type: Type of activity (e.g., 'conversation_create', 'message_send')
        description: Human-readable description
        entity_id: ID of related entity (optional)
        entity_type: Type of related entity (optional)
        metadata: Additional metadata (optional)

    Returns:
        The created ActivityLog record
    """
    activity = ActivityLog(
        user_id=user_id,
        activity_type=activity_type,
        description=description,
        entity_id=entity_id,
        entity_type=entity_type,
        metadata=metadata or {}
    )

    db.add(activity)
    await db.commit()
    await db.refresh(activity)

    return activity


# Predefined activity types and their templates
ACTIVITY_TYPES = {
    # Conversation activities
    "conversation_create": "Created a new conversation",
    "conversation_rename": "Renamed conversation to '{new_title}'",
    "conversation_delete": "Deleted conversation '{title}'",
    "message_send": "Sent a message in '{conversation_title}'",

    # File activities
    "file_upload": "Uploaded file '{filename}'",
    "file_download": "Downloaded file '{filename}'",
    "file_delete": "Deleted file '{filename}'",
    "file_edit": "Edited file '{filename}'",

    # Project activities
    "project_create": "Created project '{project_name}'",
    "project_update": "Updated project '{project_name}'",
    "project_delete": "Deleted project '{project_name}'",

    # Sharing activities
    "share_create": "Shared '{entity_name}' with {recipient}",
    "share_accept": "Accepted shared '{entity_name}'",
    "share_revoke": "Revoked access to '{entity_name}'",

    # Collaboration activities
    "collaboration_join": "Joined collaboration session for '{conversation_title}'",
    "collaboration_leave": "Left collaboration session for '{conversation_title}'",

    # Agent activities
    "agent_invoke": "Invoked agent in '{conversation_title}'",
    "agent_response": "Received agent response in '{conversation_title}'",

    # Artifact activities
    "artifact_create": "Created artifact '{artifact_name}'",
    "artifact_export": "Exported artifact '{artifact_name}'",

    # Settings activities
    "settings_update": "Updated settings",
    "api_key_create": "Created API key '{key_name}'",
    "api_key_delete": "Deleted API key '{key_name}'",
}


async def log_activity_from_template(
    db: AsyncSession,
    user_id: str,
    activity_type: str,
    entity_id: Optional[str] = None,
    entity_type: Optional[str] = None,
    **kwargs
) -> Optional[ActivityLog]:
    """Log activity using a predefined template.

    Args:
        db: Database session
        user_id: User who performed the action
        activity_type: Type of activity (must be in ACTIVITY_TYPES)
        entity_id: ID of related entity
        entity_type: Type of related entity
        **kwargs: Template variables

    Returns:
        The created ActivityLog record, or None if activity_type not found
    """
    template = ACTIVITY_TYPES.get(activity_type)
    if not template:
        return None

    description = template.format(**kwargs)

    return await log_activity(
        db=db,
        user_id=user_id,
        activity_type=activity_type,
        description=description,
        entity_id=entity_id,
        entity_type=entity_type,
        metadata=kwargs
    )
