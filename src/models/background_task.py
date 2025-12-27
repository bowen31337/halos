"""Background Task model for tracking long-running operations."""

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import Column, String, Integer, DateTime, JSON, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base
import enum


class TaskStatus(enum.Enum):
    """Task status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class BackgroundTask(Base):
    """Model for tracking background task execution."""

    __tablename__ = "background_tasks"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    conversation_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("conversations.id"), nullable=True, index=True)

    task_type: Mapped[str] = mapped_column(String, nullable=False)  # e.g., "agent_invocation", "export", "file_processing"
    status: Mapped[TaskStatus] = mapped_column(SQLEnum(TaskStatus), default=TaskStatus.PENDING, nullable=False)
    progress: Mapped[int] = mapped_column(Integer, default=0)  # 0-100

    subagent_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    result: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    def to_dict(self) -> dict:
        """Convert model to dictionary."""
        return {
            "id": str(self.id),
            "user_id": self.user_id,
            "conversation_id": str(self.conversation_id) if self.conversation_id else None,
            "task_type": self.task_type,
            "status": self.status.value,
            "progress": self.progress,
            "subagent_name": self.subagent_name,
            "result": self.result,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }

    def update_progress(self, progress: int, status: Optional[TaskStatus] = None):
        """Update task progress."""
        self.progress = progress
        if status:
            self.status = status
            if status == TaskStatus.RUNNING and not self.started_at:
                self.started_at = datetime.utcnow()
            if status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
                self.completed_at = datetime.utcnow()

    def mark_running(self):
        """Mark task as running."""
        self.status = TaskStatus.RUNNING
        if not self.started_at:
            self.started_at = datetime.utcnow()

    def mark_completed(self, result: Optional[dict] = None):
        """Mark task as completed."""
        self.status = TaskStatus.COMPLETED
        self.progress = 100
        self.completed_at = datetime.utcnow()
        if result:
            self.result = result

    def mark_failed(self, error: str):
        """Mark task as failed."""
        self.status = TaskStatus.FAILED
        self.error_message = error
        self.completed_at = datetime.utcnow()

    def mark_cancelled(self):
        """Mark task as cancelled."""
        self.status = TaskStatus.CANCELLED
        self.completed_at = datetime.utcnow()
