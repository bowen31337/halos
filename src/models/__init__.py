"""SQLAlchemy database models."""

from sqlalchemy.orm import DeclarativeBase

# Create Base class here to avoid circular import
class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""
    pass

from src.models.conversation import Conversation
from src.models.message import Message
from src.models.project import Project
from src.models.project_file import ProjectFile
from src.models.artifact import Artifact
from src.models.checkpoint import Checkpoint
from src.models.memory import Memory
from src.models.shared_conversation import SharedConversation

__all__ = ["Base", "Conversation", "Message", "Project", "ProjectFile", "Artifact", "Checkpoint", "Memory", "SharedConversation"]
