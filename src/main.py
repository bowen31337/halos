"""FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
import os

from src.core.config import settings
from src.core.database import init_db
from src.core.rate_limiter import RateLimitMiddleware
from src.api import router as api_router

# Configure logging
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan events."""
    # Startup
    await init_db()
    yield
    # Shutdown
    pass


app = FastAPI(
    title=settings.app_name,
    description="Claude.ai Clone - Advanced AI Chat Interface with Deep Agents",
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add rate limiting middleware
app.add_middleware(
    RateLimitMiddleware,
    requests_per_minute=settings.rate_limit_per_minute,
    requests_per_hour=settings.rate_limit_per_hour,
    block_duration_seconds=settings.rate_limit_block_duration,
    skip_paths=["/health", "/docs", "/openapi.json", "/redoc"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="src/static"), name="static")

# Include API routes
app.include_router(api_router, prefix="/api")


# ==================== Exception Handlers ====================


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors (400 Bad Request).

    Returns structured error messages for validation failures.
    """
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })

    logger.warning(f"Validation error on {request.url.path}: {errors}")

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": "Validation Error",
            "message": "Request body or parameters failed validation",
            "details": errors
        }
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions (404, 403, etc.).

    Returns structured error responses for HTTP errors.
    """
    logger.warning(f"HTTP error {exc.status_code} on {request.url.path}: {exc.detail}")

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "message": exc.detail
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected internal errors (500 Internal Server Error).

    Returns generic error message without leaking internal details.
    """
    logger.error(f"Internal error on {request.url.path}: {exc}", exc_info=True)

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred. Please try again later."
        }
    )


# ==================== API Endpoints ====================


@app.get("/", response_class=HTMLResponse)
async def root() -> HTMLResponse:
    """Root endpoint - serves the frontend HTML."""
    html_path = os.path.join(os.path.dirname(__file__), "static", "index.html")
    if os.path.exists(html_path):
        with open(html_path, "r") as f:
            return HTMLResponse(content=f.read())
    # Fallback if HTML doesn't exist
    return HTMLResponse(content="""
    <html>
        <head>
            <title>Claude AI Clone</title>
            <style>
                body { font-family: sans-serif; padding: 40px; text-align: center; }
                h1 { color: #CC785C; }
            </style>
        </head>
        <body>
            <h1>Claude AI Clone</h1>
            <p>Frontend not yet built. Backend is running.</p>
            <p>API Docs: <a href="/docs">/docs</a></p>
        </body>
    </html>
    """)


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": settings.app_version,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host=settings.backend_host,
        port=settings.backend_port,
        reload=settings.debug,
    )
