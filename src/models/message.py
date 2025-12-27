"""Message database model."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base


class Message(Base):
    """Message model for storing chat messages."""

    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id: Mapped[str] = mapped_column(String(36), ForeignKey("conversations.id"), nullable=False)
    role: Mapped[str] = mapped_column(String(20))  # user, assistant, system, tool
    content: Mapped[str] = mapped_column(Text, default="")

    # Token tracking
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    cache_read_tokens: Mapped[int] = mapped_column(Integer, default=0)
    cache_write_tokens: Mapped[int] = mapped_column(Integer, default=0)

    # Additional data
    attachments: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # Images, files
    tool_calls: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # Tool use information
    tool_results: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Extended thinking
    thinking_content: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    edited_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
