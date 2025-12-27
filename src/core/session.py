"""Session management for timeout handling and refresh."""

import time
import secrets
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
from pydantic import BaseModel

from src.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class TokenData(BaseModel):
    """Token data model."""
    username: Optional[str] = None
    exp: Optional[int] = None
    session_id: Optional[str] = None
    last_activity: Optional[int] = None


class SessionManager:
    """Session management with timeout handling."""

    def __init__(self):
        """Initialize session manager."""
        self.sessions: Dict[str, Dict[str, Any]] = {}  # session_id -> session_data
        self.timeout_minutes = settings.access_token_expire_minutes
        self.refresh_buffer_minutes = 5  # Refresh tokens 5 minutes before expiry
        self.refresh_token_expiry_days = 7  # Refresh token valid for 7 days

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.timeout_minutes)

        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
        return encoded_jwt

    def create_refresh_token(self, session_id: str) -> str:
        """Create a long-lived refresh token."""
        # Generate a unique refresh token string
        refresh_token = f"refresh_{secrets.token_urlsafe(32)}"

        # Store refresh token in session data
        if session_id in self.sessions:
            self.sessions[session_id]["refresh_token"] = refresh_token
            self.sessions[session_id]["refresh_token_expires"] = int(time.time()) + (
                self.refresh_token_expiry_days * 24 * 60 * 60
            )

        return refresh_token

    def verify_token(self, token: str) -> Optional[TokenData]:
        """Verify and decode JWT token."""
        try:
            payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
            username: str = payload.get("sub")
            session_id: str = payload.get("session_id")
            last_activity: int = payload.get("last_activity")

            if username is None or session_id is None:
                return None

            token_data = TokenData(
                username=username,
                session_id=session_id,
                last_activity=last_activity,
                exp=payload.get("exp")
            )

            # Check if session exists and is active
            if not self._is_session_active(session_id, last_activity):
                return None

            return token_data
        except jwt.PyJWTError:
            return None

    def refresh_token(self, token_data: TokenData) -> str:
        """Refresh an existing token."""
        if not self._is_session_active(token_data.session_id, token_data.last_activity):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Update last activity
        self._update_session_activity(token_data.session_id)

        # Create new token with extended expiration
        data = {
            "sub": token_data.username,
            "session_id": token_data.session_id,
            "last_activity": int(time.time())
        }

        return self.create_access_token(data)

    def refresh_with_refresh_token(self, refresh_token: str) -> Optional[str]:
        """Refresh access token using refresh token."""
        # Find session with matching refresh token
        for session_id, session_data in self.sessions.items():
            if session_data.get("refresh_token") == refresh_token:
                # Check if refresh token is expired
                refresh_expiry = session_data.get("refresh_token_expires", 0)
                if int(time.time()) > refresh_expiry:
                    return None

                # Check if session is still active
                if not session_data.get("is_active", False):
                    return None

                # Update activity
                self._update_session_activity(session_id)

                # Create new access token
                data = {
                    "sub": session_data["username"],
                    "session_id": session_id,
                    "last_activity": int(time.time())
                }
                return self.create_access_token(data)

        return None

    def create_session(self, username: str) -> str:
        """Create a new session for a user."""
        session_id = f"session_{int(time.time())}_{username}"
        timestamp = int(time.time())

        session_data = {
            "username": username,
            "created_at": timestamp,
            "last_activity": timestamp,
            "is_active": True
        }

        self.sessions[session_id] = session_data

        # Create access token
        data = {
            "sub": username,
            "session_id": session_id,
            "last_activity": timestamp
        }

        return self.create_access_token(data)

    def create_full_session(self, username: str) -> Dict[str, str]:
        """Create a new session with both access and refresh tokens."""
        session_id = f"session_{int(time.time())}_{username}"
        timestamp = int(time.time())

        session_data = {
            "username": username,
            "created_at": timestamp,
            "last_activity": timestamp,
            "is_active": True
        }

        self.sessions[session_id] = session_data

        # Create access token
        data = {
            "sub": username,
            "session_id": session_id,
            "last_activity": timestamp
        }
        access_token = self.create_access_token(data)

        # Create refresh token
        refresh_token = self.create_refresh_token(session_id)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "session_id": session_id,
        }

    def _is_session_active(self, session_id: str, last_activity: int) -> bool:
        """Check if session is still active and not timed out."""
        if session_id not in self.sessions:
            return False

        session_data = self.sessions[session_id]

        if not session_data.get("is_active", False):
            return False

        current_time = int(time.time())
        timeout_seconds = self.timeout_minutes * 60

        # Check if session has timed out
        if current_time - last_activity > timeout_seconds:
            # Mark session as inactive
            session_data["is_active"] = False
            return False

        return True

    def _update_session_activity(self, session_id: str):
        """Update session last activity time."""
        if session_id in self.sessions:
            self.sessions[session_id]["last_activity"] = int(time.time())

    def end_session(self, session_id: str):
        """End a session."""
        if session_id in self.sessions:
            self.sessions[session_id]["is_active"] = False

    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session information."""
        if session_id in self.sessions:
            session_data = self.sessions[session_id].copy()
            # Calculate remaining time
            last_activity = session_data.get("last_activity", 0)
            timeout_seconds = self.timeout_minutes * 60
            current_time = int(time.time())
            remaining_seconds = max(0, timeout_seconds - (current_time - last_activity))

            session_data["remaining_minutes"] = remaining_seconds // 60
            session_data["remaining_seconds"] = remaining_seconds % 60
            session_data["expires_at"] = last_activity + timeout_seconds
            return session_data

        return None

    def cleanup_expired_sessions(self):
        """Clean up expired sessions."""
        current_time = int(time.time())
        timeout_seconds = self.timeout_minutes * 60

        expired_sessions = []

        for session_id, session_data in self.sessions.items():
            last_activity = session_data.get("last_activity", 0)
            if current_time - last_activity > timeout_seconds:
                expired_sessions.append(session_id)

        for session_id in expired_sessions:
            self.end_session(session_id)

    def should_refresh_token(self, token_data: TokenData) -> bool:
        """Check if token should be refreshed."""
        current_time = int(time.time())
        exp_time = token_data.exp
        buffer_seconds = self.refresh_buffer_minutes * 60

        return (exp_time - current_time) <= buffer_seconds

    def get_session_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed session status including timeout info."""
        if session_id not in self.sessions:
            return None

        session_data = self.sessions[session_id]
        if not session_data.get("is_active", False):
            return None

        last_activity = session_data.get("last_activity", 0)
        timeout_seconds = self.timeout_minutes * 60
        current_time = int(time.time())

        remaining_seconds = max(0, timeout_seconds - (current_time - last_activity))
        is_expired = remaining_seconds <= 0

        return {
            "is_active": True,
            "is_expired": is_expired,
            "remaining_seconds": remaining_seconds,
            "remaining_minutes": remaining_seconds // 60,
            "last_activity": last_activity,
            "expires_at": last_activity + timeout_seconds,
            "username": session_data.get("username"),
            "created_at": session_data.get("created_at"),
        }


class JWTBearer(HTTPBearer):
    """Custom JWT authentication scheme."""

    def __init__(self, auto_error: bool = True):
        super().__init__(auto_error=auto_error)

    async def __call__(self, request: Request) -> TokenData:
        credentials: Optional[HTTPAuthorizationCredentials] = await super().__call__(request)
        if credentials:
            if not credentials.scheme == "Bearer":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication scheme.",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            token_data = session_manager.verify_token(credentials.credentials)
            if token_data:
                # Update session activity on each request
                session_manager._update_session_activity(token_data.session_id)
                return token_data

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


# Global session manager instance
session_manager = SessionManager()