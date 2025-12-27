"""Artifact database model for storing code artifacts from conversations."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base


class Artifact(Base):
    """Artifact model for storing code artifacts from AI responses."""

    __tablename__ = "artifacts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id: Mapped[str] = mapped_column(String(36), ForeignKey("conversations.id"), nullable=False)

    # Artifact content and metadata
    title: Mapped[str] = mapped_column(String(255), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[str] = mapped_column(String(50), nullable=True)  # python, javascript, html, svg, mermaid, etc.
    artifact_type: Mapped[str] = mapped_column(String(50), default="code")  # code, html, svg, mermaid, latex

    # Versioning
    version: Mapped[int] = mapped_column(default=1)
    parent_artifact_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("artifacts.id"), nullable=True)

    # Status
    is_archived: Mapped[bool] = mapped_column(default=False)
    is_deleted: Mapped[bool] = mapped_column(default=False)

    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    conversation = relationship("Conversation", back_populates="artifacts")
    parent = relationship(
        "Artifact",
        back_populates="versions",
        remote_side=[id],
        foreign_keys=[parent_artifact_id]
    )
    versions = relationship(
        "Artifact",
        back_populates="parent",
        foreign_keys=[parent_artifact_id],
        cascade="all, delete-orphan"
    )
