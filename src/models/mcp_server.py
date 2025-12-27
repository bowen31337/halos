"""MCP server database model for managing external tool integrations."""

import uuid
from datetime import datetime

from sqlalchemy import String, Text, DateTime, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class MCPServer(Base):
    """MCP (Model Context Protocol) server configuration model."""

    __tablename__ = "mcp_servers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), default="default-user")

    # Server identification
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    server_type: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g., "filesystem", "brave-search", "github"

    # Server configuration (stored as JSON)
    # Example: {"endpoint": "http://localhost:3000", "api_key": "..."}
    config: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    # Optional description
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Server status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_health_check: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    health_status: Mapped[str | None] = mapped_column(String(50), nullable=True)  # "healthy", "unhealthy", "unknown"

    # Available tools from this server (cached)
    # Example: ["read_file", "write_file", "search_web"]
    available_tools: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)

    # Usage statistics
    usage_count: Mapped[int] = mapped_column(default=0)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self) -> dict:
        """Convert MCP server to dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "server_type": self.server_type,
            "config": self.config,
            "description": self.description,
            "is_active": self.is_active,
            "last_health_check": self.last_health_check.isoformat() if self.last_health_check else None,
            "health_status": self.health_status,
            "available_tools": self.available_tools or [],
            "usage_count": self.usage_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
