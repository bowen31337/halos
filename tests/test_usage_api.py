"""Tests for Usage API Feature (Feature #92)."""

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
async def test_daily_usage(test_db):
    """Test daily usage endpoint."""
    app.dependency_overrides[get_db] = lambda: test_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/usage/daily")
        assert response.status_code == 200
        usage = response.json()
        assert "date" in usage
        assert "total_tokens" in usage
        assert "input_tokens" in usage
        assert "output_tokens" in usage
        assert "estimated_cost" in usage

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_monthly_usage(test_db):
    """Test monthly usage endpoint."""
    app.dependency_overrides[get_db] = lambda: test_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/usage/monthly")
        assert response.status_code == 200
        usage = response.json()
        assert "month" in usage
        assert "total_tokens" in usage
        assert "daily_breakdown" in usage
        assert isinstance(usage["daily_breakdown"], list)

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_usage_by_model(test_db):
    """Test usage by model endpoint."""
    app.dependency_overrides[get_db] = lambda: test_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/usage/by-model")
        assert response.status_code == 200
        usage = response.json()
        assert isinstance(usage, list)
        if len(usage) > 0:
            assert "model" in usage[0]
            assert "total_tokens" in usage[0]

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_cache_stats(test_db):
    """Test cache statistics endpoint."""
    app.dependency_overrides[get_db] = lambda: test_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/usage/cache-stats")
        assert response.status_code == 200
        stats = response.json()
        assert "cache_hits" in stats
        assert "cache_misses" in stats
        assert "hit_rate" in stats
        assert "tokens_saved" in stats
        assert "cost_saved" in stats

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_conversation_usage(test_db):
    """Test conversation-specific usage endpoint."""
    app.dependency_overrides[get_db] = lambda: test_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        test_conversation_id = "test-conversation-123"
        response = await client.get(f"/api/usage/conversations/{test_conversation_id}")
        assert response.status_code == 200
        usage = response.json()
        assert usage["conversation_id"] == test_conversation_id
        assert "total_tokens" in usage
        assert "estimated_cost" in usage

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_export_usage(test_db):
    """Test usage export endpoint."""
    app.dependency_overrides[get_db] = lambda: test_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/usage/export")
        assert response.status_code == 200
        export = response.json()
        assert "format" in export
        assert "data" in export
        assert "daily" in export["data"]
        assert "monthly" in export["data"]
        assert "by_model" in export["data"]

    app.dependency_overrides.clear()
