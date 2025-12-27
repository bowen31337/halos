"""Comment model for shared conversation annotations."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, Text, ForeignKey, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base


class Comment(Base):
    """Model for comments and annotations on messages in shared conversations."""

    __tablename__ = "comments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # The message being commented on
    message_id: Mapped[str] = mapped_column(String(36), ForeignKey("messages.id"), nullable=False)

    # The conversation this comment belongs to
    conversation_id: Mapped[str] = mapped_column(String(36), ForeignKey("conversations.id"), nullable=False)

    # The shared conversation context (for access control)
    # Null means it's a direct comment on the conversation (owner/authorized users)
    shared_conversation_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("shared_conversations.id"), nullable=True)

    # User who made the comment (None for anonymous shared viewers)
    user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)

    # For threaded replies
    parent_comment_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("comments.id"), nullable=True)

    # Comment content
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Annotation metadata (position, color, highlight text, etc.)
    # Stored as JSON for flexibility
    annotation_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # For shared conversations - anonymous commenter name
    anonymous_name: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Status flags
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    is_edited: Mapped[bool] = mapped_column(Boolean, default=False)
    edited_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Notification tracking
    notified_owner: Mapped[bool] = mapped_column(Boolean, default=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Relationships
    message = relationship("Message", back_populates="comments")
    conversation = relationship("Conversation", back_populates="comments")
    shared_conversation = relationship("SharedConversation", back_populates="comments")
    user = relationship("User", back_populates="comments")
    parent_comment = relationship("Comment", remote_side=[id], back_populates="replies")
    replies = relationship("Comment", back_populates="parent_comment", cascade="all, delete-orphan")
