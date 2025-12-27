"""Saved search database model for storing and reusing complex search queries."""

import uuid
from datetime import datetime

from sqlalchemy import String, Text, DateTime, Boolean, Integer
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class SavedSearch(Base):
    """Saved search model for storing reusable search queries."""

    __tablename__ = "saved_searches"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), default="default-user")

    # Search details
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Search query (the main search term)
    query: Mapped[str] = mapped_column(String(500), nullable=False)

    # Search filters (stored as JSON string)
    # Example: {"project_id": "xxx", "date_range": "7d", "model": "claude-sonnet-4-5"}
    filters: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Search type: conversations, messages, files, global
    search_type: Mapped[str] = mapped_column(String(50), default="global")

    # Optional description
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Whether the search is active/available
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Usage statistics
    usage_count: Mapped[int] = mapped_column(default=0)

    # Display order (for custom sorting)
    display_order: Mapped[int] = mapped_column(default=0)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    def to_dict(self) -> dict:
        """Convert saved search to dictionary."""
        import json
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "query": self.query,
            "filters": json.loads(self.filters) if self.filters else {},
            "search_type": self.search_type,
            "description": self.description,
            "is_active": self.is_active,
            "usage_count": self.usage_count,
            "display_order": self.display_order,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
        }

    def increment_usage(self):
        """Increment usage count and update last_used_at timestamp."""
        self.usage_count += 1
        self.last_used_at = datetime.utcnow()
