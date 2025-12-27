"""SQLAlchemy database models."""

from sqlalchemy.orm import DeclarativeBase

# Create Base class here to avoid circular import
class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""
    pass

from src.models.conversation import Conversation
from src.models.message import Message
from src.models.project import Project

__all__ = ["Base", "Conversation", "Message", "Project"]
