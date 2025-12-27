"""Folder database model for organizing conversations hierarchically."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base


class Folder(Base):
    """Folder model for organizing conversations hierarchically."""

    __tablename__ = "folders"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), default="default-user")
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Hierarchical support - folders can contain other folders
    parent_folder_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("folders.id"), nullable=True)

    # Position in the folder list for ordering
    position: Mapped[int] = mapped_column(Integer, default=0)

    # Metadata
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    parent_folder = relationship("Folder", remote_side=[id], backref="child_folders")
    folder_items = relationship("FolderItem", back_populates="folder", cascade="all, delete-orphan")


class FolderItem(Base):
    """Association table for conversations in folders."""

    __tablename__ = "folder_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    folder_id: Mapped[str] = mapped_column(String(36), ForeignKey("folders.id"), nullable=False)
    conversation_id: Mapped[str] = mapped_column(String(36), ForeignKey("conversations.id"), nullable=False)

    # Position within the folder
    position: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    folder = relationship("Folder", back_populates="folder_items")
    conversation = relationship("Conversation", backref="folder_items")
