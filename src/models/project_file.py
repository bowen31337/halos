"""Project file database model for knowledge base."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base


class ProjectFile(Base):
    """File model for project knowledge base."""

    __tablename__ = "project_files"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), default="default-user")
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id"), nullable=False)

    # File metadata
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)  # Storage path
    file_url: Mapped[str] = mapped_column(String(512), nullable=False)   # URL for access
    file_size: Mapped[int] = mapped_column(Integer, default=0)  # Size in bytes
    content_type: Mapped[str] = mapped_column(String(100), nullable=True)

    # Content extraction
    content: Mapped[str | None] = mapped_column(Text, nullable=True)  # Extracted text content

    # Organization
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)

    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    project = relationship("Project", back_populates="files")


# Add relationship to Project model
Project.files = relationship("ProjectFile", back_populates="project", cascade="all, delete-orphan")
