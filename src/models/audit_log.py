"""Audit Log model for tracking user actions and security events."""

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import String, DateTime, JSON, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column
import enum

from src.core.database import Base


class AuditActionType(enum.Enum):
    """Enumeration of audit action types."""

    # Conversation actions
    CONVERSATION_CREATE = "conversation_create"
    CONVERSATION_UPDATE = "conversation_update"
    CONVERSATION_DELETE = "conversation_delete"
    CONVERSATION_ARCHIVE = "conversation_archive"
    CONVERSATION_PIN = "conversation_pin"
    CONVERSATION_DUPLICATE = "conversation_duplicate"
    CONVERSATION_EXPORT = "conversation_export"
    CONVERSATION_BRANCH = "conversation_branch"
    CONVERSATION_READ = "conversation_read"
    CONVERSATION_UNREAD = "conversation_unread"

    # Message actions
    MESSAGE_CREATE = "message_create"
    MESSAGE_UPDATE = "message_update"
    MESSAGE_DELETE = "message_delete"
    MESSAGE_REGENERATE = "message_regenerate"

    # Project actions
    PROJECT_CREATE = "project_create"
    PROJECT_UPDATE = "project_update"
    PROJECT_DELETE = "project_delete"
    PROJECT_FILE_UPLOAD = "project_file_upload"
    PROJECT_FILE_DELETE = "project_file_delete"

    # Folder actions
    FOLDER_CREATE = "folder_create"
    FOLDER_UPDATE = "folder_update"
    FOLDER_DELETE = "folder_delete"
    FOLDER_ADD_ITEM = "folder_add_item"
    FOLDER_REMOVE_ITEM = "folder_remove_item"

    # Artifact actions
    ARTIFACT_CREATE = "artifact_create"
    ARTIFACT_UPDATE = "artifact_update"
    ARTIFACT_DELETE = "artifact_delete"
    ARTIFACT_FORK = "artifact_fork"
    ARTIFACT_DOWNLOAD = "artifact_download"
    ARTIFACT_EXECUTE = "artifact_execute"

    # Checkpoint actions
    CHECKPOINT_CREATE = "checkpoint_create"
    CHECKPOINT_RESTORE = "checkpoint_restore"
    CHECKPOINT_DELETE = "checkpoint_delete"

    # Memory actions
    MEMORY_CREATE = "memory_create"
    MEMORY_UPDATE = "memory_update"
    MEMORY_DELETE = "memory_delete"

    # Agent/Tool actions
    AGENT_INVOKE = "agent_invoke"
    AGENT_INTERRUPT_APPROVE = "agent_interrupt_approve"
    AGENT_INTERRUPT_REJECT = "agent_interrupt_reject"
    AGENT_INTERRUPT_EDIT = "agent_interrupt_edit"
    TOOL_EXECUTION = "tool_execution"

    # Subagent actions
    SUBAGENT_CREATE = "subagent_create"
    SUBAGENT_UPDATE = "subagent_update"
    SUBAGENT_DELETE = "subagent_delete"
    SUBAGENT_DELEGATION = "subagent_delegation"

    # MCP actions
    MCP_SERVER_ADD = "mcp_server_add"
    MCP_SERVER_UPDATE = "mcp_server_update"
    MCP_SERVER_DELETE = "mcp_server_delete"
    MCP_TOOL_USE = "mcp_tool_use"

    # Background task actions
    TASK_CREATE = "task_create"
    TASK_CANCEL = "task_cancel"
    TASK_COMPLETE = "task_complete"
    TASK_FAIL = "task_fail"

    # Sharing actions
    CONVERSATION_SHARE = "conversation_share"
    CONVERSATION_SHARE_UPDATE = "conversation_share_update"
    CONVERSATION_SHARE_REVOKE = "conversation_share_revoke"

    # Prompt library actions
    PROMPT_CREATE = "prompt_create"
    PROMPT_UPDATE = "prompt_update"
    PROMPT_DELETE = "prompt_delete"
    PROMPT_USE = "prompt_use"

    # Tag actions
    TAG_CREATE = "tag_create"
    TAG_UPDATE = "tag_update"
    TAG_DELETE = "tag_delete"

    # Settings actions
    SETTINGS_UPDATE = "settings_update"
    SETTINGS_CUSTOM_INSTRUCTIONS = "settings_custom_instructions"
    SETTINGS_PERMISSION_MODE = "settings_permission_mode"
    SETTINGS_API_KEY = "settings_api_key"

    # Authentication actions
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    USER_REGISTER = "user_register"
    USER_PASSWORD_CHANGE = "user_password_change"
    USER_PROFILE_UPDATE = "user_profile_update"

    # Data export & account actions
    DATA_EXPORT = "data_export"
    ACCOUNT_DELETION = "account_deletion"


class AuditLog(Base):
    """Model for auditing user actions and security events."""

    __tablename__ = "audit_logs"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    # User identification
    user_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Action details
    action: Mapped[AuditActionType] = mapped_column(SQLEnum(AuditActionType), nullable=False, index=True)
    resource_type: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
    resource_id: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)

    # Tool/HITL specific fields
    tool_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    tool_decision: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # approve, edit, reject

    # Additional context
    details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    def to_dict(self) -> dict:
        """Convert model to dictionary."""
        return {
            "id": str(self.id),
            "user_id": self.user_id,
            "action": self.action.value,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "tool_name": self.tool_name,
            "tool_decision": self.tool_decision,
            "details": self.details,
            "user_agent": self.user_agent,
            "ip_address": self.ip_address,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# Alias for backward compatibility
AuditAction = AuditActionType
