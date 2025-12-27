"""Test activity feed feature."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.activity import ActivityLog


@pytest.mark.asyncio
async def test_log_activity(async_client: AsyncClient, test_db: AsyncSession):
    """Test logging an activity."""
    response = await async_client.post(
        "/api/activity",
        json={
            "action_type": "conversation_created",
            "resource_type": "conversation",
            "resource_name": "Test Conversation",
            "details": {"model": "claude-sonnet"}
        },
        params={"user_id": "test-user", "user_name": "Test User"}
    )

    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["action_type"] == "conversation_created"
    assert data["user_name"] == "Test User"
    assert data["resource_name"] == "Test Conversation"


@pytest.mark.asyncio
async def test_get_activity_feed(async_client: AsyncClient, test_db: AsyncSession):
    """Test getting activity feed."""
    # First, create some activities
    for i in range(3):
        await async_client.post(
            "/api/activity",
            json={
                "action_type": f"action_{i}",
                "resource_type": "conversation",
                "resource_name": f"Conversation {i}",
            },
            params={"user_id": "test-user", "user_name": "Test User"}
        )

    # Get activity feed
    response = await async_client.get("/api/activity", params={"time_range": "7d", "limit": 50})

    assert response.status_code == 200
    data = response.json()
    assert "activities" in data
    assert len(data["activities"]) >= 3
    assert data["total"] >= 3
    assert data["has_more"] is False


@pytest.mark.asyncio
async def test_get_activity_types(async_client: AsyncClient, test_db: AsyncSession):
    """Test getting activity types."""
    # Create activities with different types
    await async_client.post(
        "/api/activity",
        json={"action_type": "conversation_created", "resource_type": "conversation"},
        params={"user_id": "test-user", "user_name": "Test User"}
    )
    await async_client.post(
        "/api/activity",
        json={"action_type": "message_sent", "resource_type": "message"},
        params={"user_id": "test-user", "user_name": "Test User"}
    )

    response = await async_client.get("/api/activity/types")

    assert response.status_code == 200
    data = response.json()
    assert "action_types" in data
    assert "resource_types" in data
    # Should have at least the two types we created
    action_types = [t["type"] for t in data["action_types"]]
    assert "conversation_created" in action_types
    assert "message_sent" in action_types


@pytest.mark.asyncio
async def test_get_activity_summary(async_client: AsyncClient, test_db: AsyncSession):
    """Test getting activity summary."""
    # Create some activities
    for i in range(5):
        await async_client.post(
            "/api/activity",
            json={
                "action_type": "conversation_created",
                "resource_type": "conversation",
            },
            params={"user_id": "test-user", "user_name": "Test User"}
        )

    response = await async_client.get("/api/activity/summary", params={"days": 7})

    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 5
    assert "by_user" in data
    assert "by_type" in data


@pytest.mark.asyncio
async def test_activity_feed_filters(async_client: AsyncClient, test_db: AsyncSession):
    """Test activity feed filtering."""
    # Create activities with different types and users
    await async_client.post(
        "/api/activity",
        json={"action_type": "conversation_created", "resource_type": "conversation"},
        params={"user_id": "user1", "user_name": "User 1"}
    )
    await async_client.post(
        "/api/activity",
        json={"action_type": "message_sent", "resource_type": "message"},
        params={"user_id": "user2", "user_name": "User 2"}
    )

    # Filter by action type
    response = await async_client.get(
        "/api/activity",
        params={"action_type": "conversation_created"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["activities"]) == 1
    assert data["activities"][0]["action_type"] == "conversation_created"

    # Filter by user
    response = await async_client.get(
        "/api/activity",
        params={"user_id": "user1"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["activities"]) == 1
    assert data["activities"][0]["user_id"] == "user1"


@pytest.mark.asyncio
async def test_delete_activity(async_client: AsyncClient, test_db: AsyncSession):
    """Test soft deleting an activity."""
    # Create an activity
    response = await async_client.post(
        "/api/activity",
        json={"action_type": "test", "resource_type": "test"},
        params={"user_id": "test-user", "user_name": "Test User"}
    )
    activity_id = response.json()["id"]

    # Delete it
    delete_response = await async_client.delete(
        f"/api/activity/{activity_id}",
        params={"user_id": "test-user"}
    )
    assert delete_response.status_code == 204

    # Verify it's soft deleted (not returned in feed)
    feed_response = await async_client.get("/api/activity")
    assert feed_response.status_code == 200
    data = feed_response.json()
    assert activity_id not in [a["id"] for a in data["activities"]]
