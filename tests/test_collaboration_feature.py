"""Test for Feature #158: Real-time collaboration shows other user's cursor.

This test verifies the collaboration API endpoints work correctly.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from src.core.database import Base, get_db
from src.main import app
from src.models import Conversation


TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture(scope="function")
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


@pytest_asyncio.fixture(scope="function")
async def client(test_db: AsyncSession):
    """Create an async HTTP client for testing."""
    async def override_get_db():
        yield test_db

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_collaboration_get_active_users(client: AsyncClient, test_db: AsyncSession):
    """Test getting active users in a conversation."""
    # Create a test conversation
    conv = Conversation(
        title="Test Collaboration Conversation",
        model="claude-sonnet-4-5-20250929"
    )
    test_db.add(conv)
    await test_db.commit()
    await test_db.refresh(conv)

    # Get active users (should be empty initially)
    response = await client.get(f"/api/collaboration/active/{conv.id}")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0


@pytest.mark.asyncio
async def test_collaboration_invalid_conversation(client: AsyncClient):
    """Test that invalid conversation ID returns 404."""
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = await client.get(f"/api/collaboration/active/{fake_id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_collaboration_api_structure(client: AsyncClient, test_db: AsyncSession):
    """Test that collaboration API is properly structured."""
    # Create a conversation
    conv = Conversation(
        title="API Structure Test",
        model="claude-sonnet-4-5-20250929"
    )
    test_db.add(conv)
    await test_db.commit()
    await test_db.refresh(conv)

    # Test active users endpoint
    response = await client.get(f"/api/collaboration/active/{conv.id}")
    assert response.status_code == 200
    assert response.headers.get("content-type") == "application/json"

    # The response should be a list
    data = response.json()
    assert isinstance(data, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
