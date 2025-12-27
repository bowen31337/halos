"""SQLAlchemy database models."""

from sqlalchemy.orm import DeclarativeBase

# Create Base class here to avoid circular import
class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""
    pass

# Import tag models first (needed for the conversation_tags association table used by Conversation)
from src.models.tag import Tag, conversation_tags
# Import User first (needed by Comment)
from src.models.user import User, Session, PasswordResetToken, APIKey, UserStatus
# Import Comment before Conversation and Message (they reference Comment in relationships)
from src.models.comment import Comment
from src.models.conversation import Conversation
from src.models.message import Message
from src.models.project import Project
from src.models.project_file import ProjectFile
from src.models.artifact import Artifact
from src.models.checkpoint import Checkpoint
from src.models.memory import Memory
from src.models.shared_conversation import SharedConversation
from src.models.prompt import Prompt
from src.models.mcp_server import MCPServer
from src.models.folder import Folder, FolderItem
from src.models.background_task import BackgroundTask, TaskStatus
from src.models.audit_log import AuditLog, AuditActionType, AuditAction
from src.models.template import Template

__all__ = [
    "Base", "Conversation", "Message", "Comment", "Project", "ProjectFile", "Artifact",
    "Checkpoint", "Memory", "SharedConversation", "Prompt", "MCPServer",
    "Folder", "FolderItem", "BackgroundTask", "TaskStatus", "AuditLog",
    "AuditActionType", "AuditAction", "User", "Session", "PasswordResetToken",
    "APIKey", "UserStatus", "Tag", "conversation_tags", "Template"
]
