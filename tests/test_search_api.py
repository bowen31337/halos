"""Tests for Search API Feature (Feature #90)."""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from src.core.database import Base, get_db
from src.main import app


TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def test_db():
    """Create a fresh database for each test."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.mark.asyncio
async def test_search_conversations_endpoint(test_db):
    """Test search conversations endpoint."""
    app.dependency_overrides[get_db] = lambda: test_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Test search conversations endpoint
        response = await client.get("/api/search/conversations?q=test")
        assert response.status_code == 200
        result = response.json()
        assert isinstance(result, list)

        # Test with project_id filter
        response = await client.get("/api/search/conversations?q=test&project_id=123")
        assert response.status_code == 200

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_search_messages_endpoint(test_db):
    """Test search messages endpoint."""
    app.dependency_overrides[get_db] = lambda: test_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Test search messages endpoint
        response = await client.get("/api/search/messages?q=test")
        assert response.status_code == 200
        result = response.json()
        assert isinstance(result, list)

        # Test with conversation_id filter
        response = await client.get("/api/search/messages?q=test&conversation_id=123")
        assert response.status_code == 200

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_search_files_endpoint(test_db):
    """Test search files endpoint."""
    app.dependency_overrides[get_db] = lambda: test_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Test search files endpoint
        response = await client.get("/api/search/files?q=test")
        assert response.status_code == 200
        result = response.json()
        assert isinstance(result, list)

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_global_search_endpoint(test_db):
    """Test global search endpoint."""
    app.dependency_overrides[get_db] = lambda: test_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Test global search endpoint
        response = await client.get("/api/search/global?q=test")
        assert response.status_code == 200
        result = response.json()
        assert "conversations" in result
        assert "messages" in result
        assert "files" in result
        assert "memories" in result

    app.dependency_overrides.clear()
