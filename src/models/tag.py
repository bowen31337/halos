"""Conversation tags/labels database model."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, ForeignKey, Table, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base

# Association table for many-to-many relationship between conversations and tags
conversation_tags = Table(
    'conversation_tags',
    Base.metadata,
    Column('conversation_id', String(36), ForeignKey('conversations.id'), primary_key=True),
    Column('tag_id', String(36), ForeignKey('tags.id'), primary_key=True)
)


class Tag(Base):
    """Tag model for categorizing conversations."""

    __tablename__ = "tags"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    color: Mapped[str] = mapped_column(String(7), default="#3b82f6")  # Hex color code
    user_id: Mapped[str] = mapped_column(String(36), default="default-user")
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    conversations = relationship("Conversation", secondary=conversation_tags, back_populates="tags")