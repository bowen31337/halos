"""Activity log model for tracking user actions."""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, DateTime, JSON, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base


class ActivityLog(Base):
    """Model for tracking user activities across the workspace."""

    __tablename__ = "activity_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # User who performed the action
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    user_name: Mapped[str] = mapped_column(String(255), nullable=True)

    # Action type
    action_type: Mapped[str] = mapped_column(String(50), nullable=False)
    # Examples: conversation_created, message_sent, file_uploaded, share_created, etc.

    # Target resource
    resource_type: Mapped[str] = mapped_column(String(50), nullable=True)
    # Examples: conversation, message, file, project, share

    resource_id: Mapped[str] = mapped_column(String(36), nullable=True)
    resource_name: Mapped[str] = mapped_column(String(255), nullable=True)

    # Additional context/data
    details: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Metadata
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Soft delete
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships
    user = relationship("User", back_populates="activity_logs")

    def to_dict(self) -> dict:
        """Convert activity log to dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "user_name": self.user_name,
            "action_type": self.action_type,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "resource_name": self.resource_name,
            "details": self.details,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
