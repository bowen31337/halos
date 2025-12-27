"""Session timeout middleware for automatic handling of expired sessions."""

import time
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from src.core.session import session_manager, TokenData, JWTBearer
from src.core.config import settings


class SessionTimeoutMiddleware(BaseHTTPMiddleware):
    """Middleware to handle session timeouts and automatic refresh prompts."""

    def __init__(self, app, refresh_endpoint: str = "/api/auth/refresh"):
        """Initialize session timeout middleware."""
        super().__init__(app)
        self.refresh_endpoint = refresh_endpoint

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request through session timeout handler."""
        # Skip middleware for auth endpoints to avoid infinite loops
        if request.url.path in [
            "/api/auth/login",
            "/api/auth/register",
            "/api/auth/refresh",
            "/api/auth/logout",
            "/api/auth/health"
        ]:
            return await call_next(request)

        # Try to get token from Authorization header
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]  # Remove "Bearer " prefix

            try:
                # Verify token without dependency injection to avoid conflicts
                token_data = session_manager.verify_token(token)

                if token_data:
                    # Check if session is about to expire (within 5 minutes)
                    current_time = int(time.time())
                    exp_time = token_data.exp
                    buffer_seconds = 5 * 60  # 5 minutes

                    if exp_time - current_time <= buffer_seconds:
                        # Add session warning headers
                        response = await call_next(request)
                        response.headers["X-Session-Warning"] = "token_expiring_soon"
                        response.headers["X-Session-Expires-In"] = str(exp_time - current_time)
                        response.headers["X-Session-Refresh-Endpoint"] = self.refresh_endpoint
                        return response

                    # Check if session has timed out based on last activity
                    session_info = session_manager.get_session_info(token_data.session_id)
                    if session_info and not session_manager._is_session_active(
                        token_data.session_id,
                        session_info.get("last_activity", 0)
                    ):
                        # Session has timed out - return 401 with timeout info
                        return JSONResponse(
                            status_code=401,
                            content={
                                "error": "Session Timeout",
                                "message": "Your session has timed out due to inactivity. Please refresh your token or log in again.",
                                "code": "SESSION_TIMEOUT",
                                "session_id": token_data.session_id
                            },
                            headers={
                                "X-Session-Status": "timeout",
                                "X-Session-Expired": "true"
                            }
                        )

            except Exception:
                # Token verification failed, let the next middleware handle it
                pass

        # Process request normally
        return await call_next(request)


def create_session_timeout_middleware(app):
    """Create and add session timeout middleware to app."""
    app.add_middleware(
        SessionTimeoutMiddleware,
        refresh_endpoint="/api/auth/refresh"
    )
    return app