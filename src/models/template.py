"""Conversation template database model for storing reusable conversation starters."""

import uuid
from datetime import datetime

from sqlalchemy import String, Text, DateTime, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class Template(Base):
    """Conversation template model for quick starting points."""

    __tablename__ = "templates"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), default="default-user")

    # Template details
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Category for organization (e.g., "coding", "writing", "analysis", "creative")
    category: Mapped[str] = mapped_column(String(50), default="general")

    # Initial system prompt/context for the conversation
    system_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Initial user message to start the conversation
    initial_message: Mapped[str] = mapped_column(Text, nullable=False)

    # Model to use for this template
    model: Mapped[str] = mapped_column(String(100), default="claude-sonnet-4-5-20250929")

    # Tags for search/filtering
    tags: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Whether this is a built-in template (can't be deleted)
    is_builtin: Mapped[bool] = mapped_column(Boolean, default=False)

    # Whether the template is active/available
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Usage statistics
    usage_count: Mapped[int] = mapped_column(default=0)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self) -> dict:
        """Convert template to dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "description": self.description,
            "category": self.category,
            "system_prompt": self.system_prompt,
            "initial_message": self.initial_message,
            "model": self.model,
            "tags": self.tags or {},
            "is_builtin": self.is_builtin,
            "is_active": self.is_active,
            "usage_count": self.usage_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
