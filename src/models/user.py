"""User database model for authentication and session management."""

import uuid
from datetime import datetime, timedelta
from enum import Enum

from sqlalchemy import Boolean, DateTime, Integer, String, Text, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base


class UserStatus(str, Enum):
    """User account status."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    DELETED = "deleted"


class User(Base):
    """User model for authentication and profile management."""

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    hashed_password: Mapped[str] = mapped_column(String(512))

    # Profile
    avatar_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    status: Mapped[UserStatus] = mapped_column(SQLEnum(UserStatus), default=UserStatus.ACTIVE)

    # Settings (JSON storage)
    preferences: Mapped[dict] = mapped_column(JSON, default=dict)
    custom_instructions: Mapped[str] = mapped_column(Text, default="")
    permission_mode: Mapped[str] = mapped_column(String(50), default="default")
    backend_config: Mapped[dict] = mapped_column(JSON, default=dict)

    # Feature flags
    memory_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    extended_thinking_enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    # Session tracking
    last_login: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_activity: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    comments = relationship("Comment", back_populates="user", cascade="all, delete-orphan")


class Session(Base):
    """Session model for tracking user sessions and timeout management."""

    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)

    # Token information
    access_token: Mapped[str] = mapped_column(String(512), unique=True, index=True)
    refresh_token: Mapped[str] = mapped_column(String(512), unique=True, index=True)

    # Session metadata
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(512), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    last_refreshed: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    refreshed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False)


class PasswordResetToken(Base):
    """Password reset token model."""

    __tablename__ = "password_reset_tokens"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    token: Mapped[str] = mapped_column(String(512), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    is_used: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class APIKey(Base):
    """API key model for storing encrypted API keys."""

    __tablename__ = "api_keys"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)

    key_name: Mapped[str] = mapped_column(String(255))
    api_key_hash: Mapped[str] = mapped_column(String(512))  # Hashed/encrypted
    key_preview: Mapped[str] = mapped_column(String(50))  # e.g., "sk-ant-***abcd"

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    permissions: Mapped[dict] = mapped_column(JSON, default=dict)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


# Session timeout constants (in minutes)
SESSION_ACCESS_TOKEN_EXPIRE_MINUTES = 30  # Short-lived access token
SESSION_REFRESH_TOKEN_EXPIRE_DAYS = 7     # Long-lived refresh token


def create_session_tokens(user_id: str, ip_address: str = None, user_agent: str = None) -> dict:
    """Create new session tokens for a user.

    Args:
        user_id: The user ID
        ip_address: Client IP address
        user_agent: Client user agent string

    Returns:
        Dictionary with access_token, refresh_token, and expires_at
    """
    import secrets
    from datetime import datetime, timedelta

    # Generate cryptographically secure tokens
    access_token = f"access_{secrets.token_urlsafe(32)}"
    refresh_token = f"refresh_{secrets.token_urlsafe(32)}"

    now = datetime.utcnow()
    access_expires = now + timedelta(minutes=SESSION_ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_expires = now + timedelta(days=SESSION_REFRESH_TOKEN_EXPIRE_DAYS)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "access_expires_at": access_expires,
        "refresh_expires_at": refresh_expires,
    }
