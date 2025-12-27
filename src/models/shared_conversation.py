"""Shared conversation model for conversation sharing feature."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base


class SharedConversation(Base):
    """Model for shared conversation links."""

    __tablename__ = "shared_conversations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id: Mapped[str] = mapped_column(String(36), ForeignKey("conversations.id"), nullable=False)
    share_token: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)

    # Access control
    is_public: Mapped[bool] = mapped_column(Boolean, default=True)
    access_level: Mapped[str] = mapped_column(String(20), default="read")  # read, comment, edit
    allow_comments: Mapped[bool] = mapped_column(Boolean, default=False)

    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    view_count: Mapped[int] = mapped_column(Integer, default=0)
    last_viewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Relationships
    conversation = relationship("Conversation", back_populates="shares")
    comments = relationship("Comment", back_populates="shared_conversation", cascade="all, delete-orphan")
