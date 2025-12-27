"""Activity log model for tracking user actions across the workspace."""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship

from src.models import Base


class ActivityLog(Base):
    """Model for tracking user activities across the workspace."""

    __tablename__ = "activity_logs"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)

    # Activity type: conversation_create, message_send, file_upload, share_create, etc.
    activity_type = Column(String(100), nullable=False)

    # Human-readable description
    description = Column(String(500), nullable=False)

    # Related entity (conversation_id, file_id, etc.)
    entity_id = Column(String, nullable=True)
    entity_type = Column(String(50), nullable=True)  # conversation, file, project, etc.

    # Additional metadata as JSON
    extra_data = Column(JSON, default=dict)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    # Read status
    is_read = Column(Boolean, default=False)

    # Relationships
    user = relationship("User", back_populates="activity_logs")

    def to_dict(self) -> dict:
        """Convert activity to dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "activity_type": self.activity_type,
            "description": self.description,
            "entity_id": self.entity_id,
            "entity_type": self.entity_type,
            "extra_data": self.extra_data,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "is_read": self.is_read,
        }
