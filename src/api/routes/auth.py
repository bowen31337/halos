"""Authentication endpoints with session timeout management."""

from datetime import timedelta
import time
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, status, Request, Body
from fastapi.security import OAuth2PasswordRequestForm

from src.core.config import settings
from src.core.session import (
    session_manager, TokenData, JWTBearer,
    pwd_context
)

router = APIRouter()


@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    request: Request = None
) -> dict:
    """User login endpoint with session management.

    Returns access token (30 min expiry) and refresh token (7 days expiry).
    """
    # For now, implement basic authentication (in production, use proper user database)
    # This is a simplified implementation for the demo

    # In a real application, you would:
    # 1. Verify username exists in database
    # 2. Verify password hash matches
    # 3. Create session

    # For demo purposes, accept any credentials
    if not form_data.username or not form_data.password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username and password required"
        )

    # Create full session with both access and refresh tokens
    session_tokens = session_manager.create_full_session(form_data.username)

    return {
        "access_token": session_tokens["access_token"],
        "refresh_token": session_tokens["refresh_token"],
        "token_type": "bearer",
        "username": form_data.username,
        "expires_in": settings.access_token_expire_minutes * 60,
        "session_id": session_tokens["session_id"],
    }


@router.post("/logout")
async def logout(token_data: TokenData = Depends(JWTBearer())):
    """User logout endpoint."""
    session_manager.end_session(token_data.session_id)
    return {"message": "Logout successful"}


@router.post("/refresh")
async def refresh_token(
    request: Request,
    refresh_token: Optional[str] = Body(None, embed=True)
) -> dict:
    """Refresh access token.

    Supports two modes:
    1. Using existing access token (automatic refresh)
    2. Using refresh token (when access token expired)
    """
    # Mode 2: Refresh using refresh token
    if refresh_token:
        new_access_token = session_manager.refresh_with_refresh_token(refresh_token)
        if not new_access_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token expired or invalid. Please log in again."
            )
        return {
            "access_token": new_access_token,
            "token_type": "bearer",
            "expires_in": settings.access_token_expire_minutes * 60
        }

    # Mode 1: Try to refresh using existing access token from header
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]  # Remove "Bearer " prefix
        token_data = session_manager.verify_token(token)
        if token_data:
            if session_manager.should_refresh_token(token_data):
                new_access_token = session_manager.refresh_token(token_data)
            else:
                # Token not ready for refresh yet
                new_access_token = session_manager.create_access_token({
                    "sub": token_data.username,
                    "session_id": token_data.session_id,
                    "last_activity": int(time.time())
                })

            return {
                "access_token": new_access_token,
                "token_type": "bearer",
                "expires_in": settings.access_token_expire_minutes * 60
            }

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Either provide refresh_token or valid access_token in Authorization header"
    )


@router.post("/register")
async def register(
    form_data: OAuth2PasswordRequestForm = Depends(),
    request: Request = None
):
    """User registration endpoint."""
    # For demo purposes, registration just creates a session
    # In production, this would create a user in the database

    if not form_data.username or not form_data.password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username and password required"
        )

    # Create full session for the new "user"
    session_tokens = session_manager.create_full_session(form_data.username)

    return {
        "access_token": session_tokens["access_token"],
        "refresh_token": session_tokens["refresh_token"],
        "token_type": "bearer",
        "username": form_data.username,
        "expires_in": settings.access_token_expire_minutes * 60,
        "session_id": session_tokens["session_id"],
    }


@router.get("/me")
async def get_current_user(token_data: TokenData = Depends(JWTBearer())) -> dict:
    """Get current user profile."""
    session_info = session_manager.get_session_info(token_data.session_id)

    if not session_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session not found or expired"
        )

    return {
        "username": token_data.username,
        "session_id": token_data.session_id,
        "session_info": session_info
    }


@router.get("/session-info")
async def get_session_info(token_data: TokenData = Depends(JWTBearer())) -> dict:
    """Get detailed session information."""
    session_info = session_manager.get_session_info(token_data.session_id)

    if not session_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session not found or expired"
        )

    # Add token expiration info
    current_time = int(time.time())
    remaining_time = token_data.exp - current_time if token_data.exp else 0

    return {
        "session_info": session_info,
        "token_expires_in": remaining_time,
        "should_refresh": session_manager.should_refresh_token(token_data)
    }


@router.get("/session/status")
async def check_session_status(token_data: TokenData = Depends(JWTBearer())) -> dict:
    """Check session status and return remaining time."""
    status_info = session_manager.get_session_status(token_data.session_id)

    if not status_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired"
        )

    return status_info


@router.post("/session/keep-alive")
async def keep_alive(token_data: TokenData = Depends(JWTBearer())) -> dict:
    """Keep session alive by updating activity timestamp."""
    session_manager._update_session_activity(token_data.session_id)

    session_info = session_manager.get_session_info(token_data.session_id)

    return {
        "message": "Session kept alive",
        "session_info": session_info
    }


@router.post("/session/revoke-all")
async def revoke_all_sessions(token_data: TokenData = Depends(JWTBearer())) -> dict:
    """Revoke all active sessions for the user."""
    # In a real implementation, this would revoke all sessions for the user
    # For now, we just end the current session
    session_manager.end_session(token_data.session_id)

    return {
        "message": "Session revoked"
    }


@router.get("/health")
async def auth_health_check():
    """Authentication system health check."""
    active_sessions = sum(
        1 for s in session_manager.sessions.values()
        if s.get("is_active", False)
    )
    return {
        "status": "auth_service_healthy",
        "sessions_active": active_sessions,
        "timeout_minutes": session_manager.timeout_minutes,
        "refresh_token_expiry_days": session_manager.refresh_token_expiry_days,
    }
