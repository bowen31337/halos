"""Prompt library database model for storing reusable prompt templates."""

import uuid
from datetime import datetime

from sqlalchemy import String, Text, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class Prompt(Base):
    """Prompt template model for the prompt library."""

    __tablename__ = "prompts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), default="default-user")

    # Prompt details
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Category for organization (e.g., "writing", "coding", "analysis", "creative")
    category: Mapped[str] = mapped_column(String(50), default="general")

    # Optional description
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Tags for search/filtering (stored as JSON string)
    tags: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Whether the prompt is active/available
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Usage statistics
    usage_count: Mapped[int] = mapped_column(default=0)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self) -> dict:
        """Convert prompt to dictionary."""
        import json
        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "content": self.content,
            "category": self.category,
            "description": self.description,
            "tags": json.loads(self.tags) if self.tags else [],
            "is_active": self.is_active,
            "usage_count": self.usage_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
