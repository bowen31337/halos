"""Collaboration session model for real-time collaboration."""

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship

from src.models import Base
from src.models.user import User
from src.models.conversation import Conversation


class CollaborationSession(Base):
    """Model for tracking active collaboration sessions."""

    __tablename__ = "collaboration_sessions"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)

    # Session metadata
    session_token = Column(String, unique=True, nullable=False, default=lambda: str(uuid4()))
    is_active = Column(Boolean, default=True)

    # Cursor position tracking
    cursor_position = Column(JSON, default=lambda: {"line": 0, "column": 0})

    # User presence info
    user_name = Column(String, nullable=False)
    user_color = Column(String, default="#CC785C")  # Claude orange

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)

    # Relationships
    conversation = relationship("Conversation", back_populates="collaboration_sessions")
    user = relationship("User", back_populates="collaboration_sessions")

    def to_dict(self) -> dict:
        """Convert session to dictionary."""
        return {
            "id": self.id,
            "conversation_id": self.conversation_id,
            "user_id": self.user_id,
            "user_name": self.user_name,
            "user_color": self.user_color,
            "cursor_position": self.cursor_position,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
        }


class CollaborationEdit(Base):
    """Model for tracking collaborative edits to detect conflicts."""

    __tablename__ = "collaboration_edits"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    session_id = Column(String, ForeignKey("collaboration_sessions.id"), nullable=False)
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)

    # Edit details
    content = Column(String, nullable=False)  # The edited content
    cursor_before = Column(JSON, default=lambda: {"line": 0, "column": 0})
    cursor_after = Column(JSON, default=lambda: {"line": 0, "column": 0})

    # Conflict detection
    is_conflict = Column(Boolean, default=False)
    conflict_with = Column(String, nullable=True)  # ID of conflicting edit

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    session = relationship("CollaborationSession")
    conversation = relationship("Conversation")
    user = relationship("User")

    def to_dict(self) -> dict:
        """Convert edit to dictionary."""
        return {
            "id": self.id,
            "session_id": self.session_id,
            "conversation_id": self.conversation_id,
            "user_id": self.user_id,
            "content": self.content,
            "cursor_before": self.cursor_before,
            "cursor_after": self.cursor_after,
            "is_conflict": self.is_conflict,
            "conflict_with": self.conflict_with,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class CollaborationMessage(Base):
    """Model for real-time messages between collaborators."""

    __tablename__ = "collaboration_messages"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    session_id = Column(String, ForeignKey("collaboration_sessions.id"), nullable=False)
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=False)
    sender_id = Column(String, ForeignKey("users.id"), nullable=False)

    # Message content
    message_type = Column(String, nullable=False)  # cursor, edit, join, leave, chat
    content = Column(JSON, nullable=False)  # Flexible message payload

    # Delivery status
    is_delivered = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    session = relationship("CollaborationSession")
    conversation = relationship("Conversation")
    sender = relationship("User")

    def to_dict(self) -> dict:
        """Convert message to dictionary."""
        return {
            "id": self.id,
            "session_id": self.session_id,
            "conversation_id": self.conversation_id,
            "sender_id": self.sender_id,
            "message_type": self.message_type,
            "content": self.content,
            "is_delivered": self.is_delivered,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
