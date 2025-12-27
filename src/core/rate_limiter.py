"""Rate limiting middleware for API abuse prevention."""

import time
from collections import defaultdict, deque
from typing import Dict, Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class RateLimiter:
    """In-memory rate limiter using sliding window algorithm."""

    def __init__(
        self,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
        block_duration_seconds: int = 60
    ):
        """Initialize rate limiter.

        Args:
            requests_per_minute: Max requests allowed per minute
            requests_per_hour: Max requests allowed per hour
            block_duration_seconds: How long to block after limit exceeded
        """
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.block_duration_seconds = block_duration_seconds

        # {client_id: deque of timestamps}
        self.request_history: Dict[str, deque] = defaultdict(deque)
        # {client_id: block_until_timestamp}
        self.blocked_clients: Dict[str, float] = {}

    def get_client_id(self, request: Request) -> str:
        """Extract client identifier from request.

        Uses X-Forwarded-For header, then X-Real-IP, then client IP.
        """
        # Check for forwarded headers first (for reverse proxies)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take the first IP in case of multiple proxies
            client_ip = forwarded_for.split(",")[0].strip()
        else:
            # Fall back to real IP header
            client_ip = request.headers.get("X-Real-IP", "")

        # If no forwarded headers, use direct client IP
        if not client_ip:
            client_ip = request.client.host if request.client else "unknown"

        # Include User-Agent for more granular tracking
        user_agent = request.headers.get("User-Agent", "unknown")
        return f"{client_ip}:{user_agent[:100]}"  # Limit user agent length

    def is_allowed(self, client_id: str) -> tuple[bool, Optional[Dict]]:
        """Check if request is allowed and return rate limit info.

        Returns:
            tuple: (is_allowed, rate_limit_headers)
        """
        current_time = time.time()

        # Check if client is currently blocked
        if client_id in self.blocked_clients:
            block_until = self.blocked_clients[client_id]
            if current_time < block_until:
                # Still blocked
                return False, {
                    "X-RateLimit-Limit-Minute": str(self.requests_per_minute),
                    "X-RateLimit-Remaining-Minute": "0",
                    "X-RateLimit-Reset-Minute": str(int(block_until)),
                    "X-RateLimit-Limit-Hour": str(self.requests_per_hour),
                    "X-RateLimit-Remaining-Hour": "0",
                    "X-RateLimit-Reset-Hour": str(int(block_until)),
                    "X-RateLimit-Blocked-Until": str(int(block_until)),
                }
            else:
                # Block expired, remove from blocked list
                del self.blocked_clients[client_id]

        # Clean up old requests (cleanup only when needed)
        history = self.request_history[client_id]
        cutoff_minute = current_time - 60
        cutoff_hour = current_time - 3600

        # Remove requests older than 1 hour (keeps memory bounded)
        while history and history[0] < cutoff_hour:
            history.popleft()

        # Count requests in current window
        recent_minute_requests = sum(1 for t in history if t >= cutoff_minute)
        recent_hour_requests = len(history)

        # Check limits
        minute_limit_exceeded = recent_minute_requests >= self.requests_per_minute
        hour_limit_exceeded = recent_hour_requests >= self.requests_per_hour

        if minute_limit_exceeded or hour_limit_exceeded:
            # Block the client
            block_until = current_time + self.block_duration_seconds
            self.blocked_clients[client_id] = block_until

            return False, {
                "X-RateLimit-Limit-Minute": str(self.requests_per_minute),
                "X-RateLimit-Remaining-Minute": "0",
                "X-RateLimit-Reset-Minute": str(int(block_until)),
                "X-RateLimit-Limit-Hour": str(self.requests_per_hour),
                "X-RateLimit-Remaining-Hour": "0",
                "X-RateLimit-Reset-Hour": str(int(block_until)),
                "X-RateLimit-Blocked-Until": str(int(block_until)),
            }

        # Add current request to history
        history.append(current_time)

        # Calculate remaining requests
        remaining_minute = max(0, self.requests_per_minute - recent_minute_requests - 1)
        remaining_hour = max(0, self.requests_per_hour - recent_hour_requests - 1)

        # Calculate reset times
        next_minute_reset = int(current_time + 60)
        next_hour_reset = int(current_time + 3600)

        return True, {
            "X-RateLimit-Limit-Minute": str(self.requests_per_minute),
            "X-RateLimit-Remaining-Minute": str(remaining_minute),
            "X-RateLimit-Reset-Minute": str(next_minute_reset),
            "X-RateLimit-Limit-Hour": str(self.requests_per_hour),
            "X-RateLimit-Remaining-Hour": str(remaining_hour),
            "X-RateLimit-Reset-Hour": str(next_hour_reset),
        }

    def reset_client(self, client_id: str):
        """Reset rate limit for a specific client (for testing)."""
        if client_id in self.request_history:
            del self.request_history[client_id]
        if client_id in self.blocked_clients:
            del self.blocked_clients[client_id]


class RateLimitMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for rate limiting."""

    def __init__(
        self,
        app,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
        block_duration_seconds: int = 60,
        skip_paths: Optional[list] = None
    ):
        """Initialize rate limiting middleware.

        Args:
            app: FastAPI app instance
            requests_per_minute: Max requests per minute per client
            requests_per_hour: Max requests per hour per client
            block_duration_seconds: Block duration in seconds after limit exceeded
            skip_paths: List of paths to skip rate limiting (e.g., health checks)
        """
        super().__init__(app)
        self.rate_limiter = RateLimiter(
            requests_per_minute=requests_per_minute,
            requests_per_hour=requests_per_hour,
            block_duration_seconds=block_duration_seconds
        )
        self.skip_paths = skip_paths or ["/health", "/docs", "/openapi.json"]

    async def dispatch(self, request: Request, call_next):
        """Process request through rate limiter."""
        # Skip rate limiting for certain paths
        if any(request.url.path.startswith(path) for path in self.skip_paths):
            return await call_next(request)

        # Check rate limit
        client_id = self.rate_limiter.get_client_id(request)
        is_allowed, headers = self.rate_limiter.is_allowed(client_id)

        if not is_allowed:
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Too Many Requests",
                    "message": "Rate limit exceeded. Please try again later.",
                    "blocked_until": headers.get("X-RateLimit-Blocked-Until"),
                },
                headers=headers
            )

        # Process request
        response = await call_next(request)

        # Add rate limit headers to response
        if headers:
            for key, value in headers.items():
                response.headers[key] = value

        return response


# Global rate limiter instance
rate_limiter = RateLimiter()