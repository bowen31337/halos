"""Memory database model for long-term memory persistence."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base


class Memory(Base):
    """Long-term memory model for storing user preferences and facts across conversations."""

    __tablename__ = "memories"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), default="default-user")

    # Content of the memory
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Category: fact, preference, context, or custom
    category: Mapped[str] = mapped_column(String(50), default="fact")

    # Source conversation for provenance
    source_conversation_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("conversations.id"), nullable=True)

    # Whether the memory is currently active
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Optional metadata for richer memory storage
    memory_metadata: Mapped[dict | None] = mapped_column("metadata", Text, nullable=True)  # JSON string

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    source_conversation = relationship("Conversation", back_populates="memories")

    def to_dict(self) -> dict:
        """Convert memory to dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "content": self.content,
            "category": self.category,
            "source_conversation_id": self.source_conversation_id,
            "is_active": self.is_active,
            "metadata": self.memory_metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
