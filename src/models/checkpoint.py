"""Checkpoint database model for conversation state preservation."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, Text, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base


class Checkpoint(Base):
    """Checkpoint model for storing conversation state snapshots.

    Checkpoints allow users to save the state of a conversation at a specific point
    and restore it later. This is useful for:
    - Saving before making major changes
    - Creating restore points during complex tasks
    - Comparing different conversation states
    - Rolling back to previous states
    """

    __tablename__ = "checkpoints"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id: Mapped[str] = mapped_column(String(36), ForeignKey("conversations.id"), nullable=False)

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # State snapshot contains:
    # - messages: List of message IDs and content up to this point
    # - metadata: Conversation settings, model, etc.
    # - artifacts: Associated artifact IDs
    state_snapshot: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    conversation = relationship("Conversation", back_populates="checkpoints")

    def __repr__(self) -> str:
        return f"<Checkpoint(id={self.id}, name='{self.name}', conversation_id={self.conversation_id})>"
