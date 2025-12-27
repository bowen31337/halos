"""Application configuration settings."""

import os
from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Server Configuration
    app_name: str = "Claude.ai Clone"
    app_version: str = "1.0.0"
    debug: bool = False
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    frontend_port: int = 5173

    # Database
    database_url: str = "sqlite+aiosqlite:///./data/app.db"

    # Security
    secret_key: str = "change-me-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Anthropic API
    anthropic_api_key: Optional[str] = None

    # DeepAgents Configuration
    deepagents_backend: str = "state"
    deepagents_memory_path: str = "/memories/"
    default_model: str = "claude-sonnet-4-5-20250929"

    # Feature Flags
    extended_thinking_enabled: bool = True
    mcp_enabled: bool = True
    prompt_caching_enabled: bool = True

    # Paths
    project_root: Path = Path(__file__).parent.parent.parent

    class Config:
        """Pydantic settings configuration."""

        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    def get_anthropic_api_key(self) -> Optional[str]:
        """Get Anthropic API key from settings or /tmp/api-key file."""
        if self.anthropic_api_key:
            return self.anthropic_api_key

        # Try to read from /tmp/api-key
        api_key_path = Path("/tmp/api-key")
        if api_key_path.exists():
            try:
                return api_key_path.read_text().strip()
            except Exception:
                pass

        return None

    @property
    def cors_origins(self) -> list[str]:
        """Get CORS allowed origins."""
        return [
            f"http://localhost:{self.frontend_port}",
            f"http://127.0.0.1:{self.frontend_port}",
            "http://localhost:3000",
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ]


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()
