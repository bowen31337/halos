"""Usage tracking database model."""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, String, DateTime, ForeignKey, Float, Integer
from sqlalchemy.orm import relationship

from src.models import Base


class UsageTracking(Base):
    """Model for tracking API usage and token consumption."""

    __tablename__ = "usage_tracking"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=True)
    message_id = Column(String, ForeignKey("messages.id"), nullable=True)
    project_id = Column(String, ForeignKey("projects.id"), nullable=True)

    # Model information
    model = Column(String(100), nullable=False)

    # Token usage
    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    cache_read_tokens = Column(Integer, default=0)
    cache_write_tokens = Column(Integer, default=0)
    thinking_tokens = Column(Integer, default=0)

    # Cost estimation
    cost_estimate = Column(Float, nullable=True)

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    user = relationship("User", back_populates="usage_tracking")
    conversation = relationship("Conversation", back_populates="usage_tracking")
    message = relationship("Message", back_populates="usage_tracking")
    project = relationship("Project", back_populates="usage_tracking")

    def to_dict(self) -> dict:
        """Convert usage tracking to dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "conversation_id": self.conversation_id,
            "message_id": self.message_id,
            "project_id": self.project_id,
            "model": self.model,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cache_read_tokens": self.cache_read_tokens,
            "cache_write_tokens": self.cache_write_tokens,
            "thinking_tokens": self.thinking_tokens,
            "total_tokens": self.input_tokens + self.output_tokens + self.cache_read_tokens + self.cache_write_tokens + self.thinking_tokens,
            "cost_estimate": self.cost_estimate,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
