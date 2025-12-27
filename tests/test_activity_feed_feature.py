"""Test for Feature #160: Activity feed shows recent actions across workspace.

This test verifies the activity feed API endpoints work correctly.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from src.core.database import Base, get_db
from src.main import app
from src.models.activity import ActivityLog


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


class TestActivityFeedFeature:
    """QA tests for activity feed feature."""

    @pytest.mark.asyncio
    async def test_log_activity(self, client: AsyncClient, test_db: AsyncSession):
        """Test logging an activity."""
        response = await client.post(
            "/api/activity",
            params={"user_id": "user123", "user_name": "Test User"},
            json={
                "action_type": "conversation_created",
                "resource_type": "conversation",
                "resource_id": "conv-123",
                "resource_name": "My Test Conversation",
                "details": {"model": "claude-sonnet-4-5"}
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["user_id"] == "user123"
        assert data["action_type"] == "conversation_created"
        assert data["resource_name"] == "My Test Conversation"

    @pytest.mark.asyncio
    async def test_get_activity_feed(self, client: AsyncClient, test_db: AsyncSession):
        """Test getting activity feed."""
        # First, log some activities
        for i in range(5):
            await client.post(
                "/api/activity",
                params={"user_id": f"user{i}", "user_name": f"User{i}"},
                json={
                    "action_type": "message_sent",
                    "resource_type": "message",
                    "resource_id": f"msg-{i}",
                    "resource_name": f"Message {i}"
                }
            )

        # Get activity feed
        response = await client.get("/api/activity")
        assert response.status_code == 200
        data = response.json()
        assert "activities" in data
        assert len(data["activities"]) == 5

    @pytest.mark.asyncio
    async def test_activity_types(self, client: AsyncClient, test_db: AsyncSession):
        """Test getting activity types."""
        # Log some activities
        await client.post(
            "/api/activity",
            params={"user_id": "user1", "user_name": "User1"},
            json={"action_type": "conversation_created", "resource_type": "conversation"}
        )
        await client.post(
            "/api/activity",
            params={"user_id": "user1", "user_name": "User1"},
            json={"action_type": "message_sent", "resource_type": "message"}
        )

        # Get types
        response = await client.get("/api/activity/types")
        assert response.status_code == 200
        data = response.json()
        assert "action_types" in data
        assert "resource_types" in data

    @pytest.mark.asyncio
    async def test_activity_summary(self, client: AsyncClient, test_db: AsyncSession):
        """Test getting activity summary."""
        # Log some activities
        for i in range(3):
            await client.post(
                "/api/activity",
                params={"user_id": "user1", "user_name": "User1"},
                json={"action_type": "conversation_created", "resource_type": "conversation"}
            )

        # Get summary
        response = await client.get("/api/activity/summary?days=7")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert "by_user" in data
        assert "by_type" in data

    @pytest.mark.asyncio
    async def test_activity_filtering(self, client: AsyncClient, test_db: AsyncSession):
        """Test activity feed filtering."""
        # Log different types of activities
        await client.post(
            "/api/activity",
            params={"user_id": "user1", "user_name": "User1"},
            json={"action_type": "conversation_created", "resource_type": "conversation"}
        )
        await client.post(
            "/api/activity",
            params={"user_id": "user1", "user_name": "User1"},
            json={"action_type": "message_sent", "resource_type": "message"}
        )

        # Filter by action type
        response = await client.get("/api/activity?action_type=conversation_created")
        assert response.status_code == 200
        data = response.json()
        assert len(data["activities"]) == 1
        assert data["activities"][0]["action_type"] == "conversation_created"

        # Filter by resource type
        response = await client.get("/api/activity?resource_type=message")
        assert response.status_code == 200
        data = response.json()
        assert len(data["activities"]) == 1
        assert data["activities"][0]["resource_type"] == "message"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
