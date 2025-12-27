"""Collaboration models for real-time collaboration features."""

from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base


class CollaborationSession(Base):
    """Represents a real-time collaboration session for a conversation."""

    __tablename__ = "collaboration_sessions"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
        comment="Unique session ID"
    )
    conversation_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        comment="Conversation being collaborated on"
    )
    session_token: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        comment="Token for joining the session"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether the session is active"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        comment="Session creation time"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        comment="Last update time"
    )

    # Relationships
    conversation = relationship("Conversation", back_populates="collaboration_sessions")
    participants = relationship("CollaborationParticipant", back_populates="session", cascade="all, delete-orphan")


class CollaborationParticipant(Base):
    """Represents a participant in a collaboration session."""

    __tablename__ = "collaboration_participants"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
        comment="Unique participant ID"
    )
    session_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("collaboration_sessions.id", ondelete="CASCADE"),
        nullable=False,
        comment="Session the participant belongs to"
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="User ID of the participant"
    )
    username: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Display name for the participant"
    )
    color: Mapped[str] = mapped_column(
        String(7),
        nullable=False,
        comment="Color code for cursor/selection indicators"
    )
    cursor_position: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Current cursor position JSON"
    )
    selection_range: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Current selection range JSON"
    )
    is_typing: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether participant is currently typing"
    )
    last_activity: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        comment="Last activity timestamp"
    )

    # Relationships
    session = relationship("CollaborationSession", back_populates="participants")
    user = relationship("User")


class CollaborationEvent(Base):
    """Represents real-time collaboration events for audit trail."""

    __tablename__ = "collaboration_events"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
        comment="Unique event ID"
    )
    session_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("collaboration_sessions.id", ondelete="CASCADE"),
        nullable=False,
        comment="Session the event belongs to"
    )
    participant_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("collaboration_participants.id", ondelete="CASCADE"),
        nullable=False,
        comment="Participant who triggered the event"
    )
    event_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Type of collaboration event"
    )
    event_data: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Event data as JSON"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        comment="Event creation time"
    )

    # Relationships
    session = relationship("CollaborationSession")
    participant = relationship("CollaborationParticipant")