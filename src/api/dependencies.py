"""FastAPI dependencies for dependency injection."""

from typing import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db


async def get_database_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for database session."""
    async for session in get_db():
        yield session


# Alias for cleaner imports
DatabaseSession = Depends(get_database_session)
