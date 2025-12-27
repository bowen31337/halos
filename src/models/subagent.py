"""SubAgent database model for storing custom and built-in sub-agent configurations."""

import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import DateTime, String, Text, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class SubAgent(Base):
    """SubAgent model for storing custom and built-in sub-agent configurations.

    This model stores sub-agent definitions that can be used for task delegation
    via the SubAgentMiddleware in DeepAgents.
    """

    __tablename__ = "subagents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), nullable=False)  # 'default' for global subagents

    # SubAgent configuration
    name: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g., "research-agent"
    description: Mapped[str] = mapped_column(Text, nullable=True)
    system_prompt: Mapped[str] = mapped_column(Text, nullable=False)

    # Model and tools
    model: Mapped[str] = mapped_column(String(100), default="claude-sonnet-4-5-20250929")
    tools: Mapped[List[str]] = mapped_column(JSON, default=list)  # List of tool names

    # Built-in vs Custom
    is_builtin: Mapped[bool] = mapped_column(Boolean, default=False)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)

    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "description": self.description,
            "system_prompt": self.system_prompt,
            "model": self.model,
            "tools": self.tools,
            "is_builtin": self.is_builtin,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


# Built-in sub-agent definitions
BUILTIN_SUBAGENTS = [
    {
        "name": "research-agent",
        "description": "Specialized agent for web research and information gathering using search tools",
        "system_prompt": "You are a research specialist. Use web search tools to find accurate, up-to-date information. Provide citations and be thorough.",
        "model": "claude-sonnet-4-5-20250929",
        "tools": ["search", "read_file", "write_file"],
        "is_builtin": True,
    },
    {
        "name": "code-review-agent",
        "description": "Specialized agent for code review, security analysis, and best practices",
        "system_prompt": "You are a senior code reviewer. Analyze code for bugs, security vulnerabilities, performance issues, and adherence to best practices. Be constructive and specific.",
        "model": "claude-sonnet-4-5-20250929",
        "tools": ["read_file", "glob", "grep"],
        "is_builtin": True,
    },
    {
        "name": "documentation-agent",
        "description": "Specialized agent for creating and maintaining documentation",
        "system_prompt": "You are a documentation specialist. Create clear, comprehensive documentation including READMEs, API docs, and user guides. Follow standard documentation formats.",
        "model": "claude-sonnet-4-5-20250929",
        "tools": ["read_file", "write_file", "edit_file"],
        "is_builtin": True,
    },
    {
        "name": "test-writing-agent",
        "description": "Specialized agent for writing unit tests and integration tests",
        "system_prompt": "You are a testing specialist. Write comprehensive unit tests and integration tests. Follow testing best practices and ensure good coverage.",
        "model": "claude-sonnet-4-5-20250929",
        "tools": ["read_file", "write_file", "edit_file", "execute"],
        "is_builtin": True,
    },
]
