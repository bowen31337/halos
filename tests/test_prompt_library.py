#!/usr/bin/env python3
"""Test prompt library functionality - Feature #75

This test suite verifies:
- Feature #75: Prompt library stores and retrieves saved prompts
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from src.core.database import Base, get_db
from src.main import app


# Test database URL
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
async def test_create_prompt(client: AsyncClient):
    """Test creating a new prompt in the library"""
    response = await client.post(
        "/api/prompts",
        json={
            "title": "Email Response Template",
            "content": "Write a professional email response to: {query}",
            "category": "writing",
            "description": "Template for professional email responses",
            "tags": ["email", "professional", "work"]
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Email Response Template"
    assert data["content"] == "Write a professional email response to: {query}"
    assert data["category"] == "writing"
    assert data["description"] == "Template for professional email responses"
    assert data["tags"] == ["email", "professional", "work"]
    assert data["is_active"] is True
    assert data["usage_count"] == 0
    assert "id" in data


@pytest.mark.asyncio
async def test_list_prompts(client: AsyncClient):
    """Test listing all prompts"""
    # First create a prompt
    await client.post("/api/prompts", json={
        "title": "Email Response Template",
        "content": "Write a professional email response",
        "category": "writing"
    })

    response = await client.get("/api/prompts")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    titles = [p["title"] for p in data]
    assert "Email Response Template" in titles


@pytest.mark.asyncio
async def test_search_prompts(client: AsyncClient):
    """Test searching prompts by content"""
    await client.post("/api/prompts", json={
        "title": "Email Response Template",
        "content": "Write a professional email response",
        "category": "writing"
    })

    response = await client.get("/api/prompts/search?q=email")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0


@pytest.mark.asyncio
async def test_get_prompt(client: AsyncClient):
    """Test retrieving a specific prompt"""
    create_resp = await client.post("/api/prompts", json={
        "title": "Email Response Template",
        "content": "Write a professional email response",
        "category": "writing"
    })
    prompt_id = create_resp.json()["id"]

    response = await client.get(f"/api/prompts/{prompt_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == prompt_id
    assert data["title"] == "Email Response Template"


@pytest.mark.asyncio
async def test_update_prompt(client: AsyncClient):
    """Test updating an existing prompt"""
    create_resp = await client.post("/api/prompts", json={
        "title": "Email Response Template",
        "content": "Write a professional email response",
        "category": "writing"
    })
    prompt_id = create_resp.json()["id"]

    response = await client.put(
        f"/api/prompts/{prompt_id}",
        json={
            "title": "Updated Email Template",
            "description": "Updated description"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Email Template"
    assert data["description"] == "Updated description"


@pytest.mark.asyncio
async def test_delete_prompt(client: AsyncClient):
    """Test deleting a prompt"""
    create_resp = await client.post("/api/prompts", json={
        "title": "Email Response Template",
        "content": "Write a professional email response",
        "category": "writing"
    })
    prompt_id = create_resp.json()["id"]

    response = await client.delete(f"/api/prompts/{prompt_id}")
    assert response.status_code == 204

    # Verify it's gone
    response = await client.get(f"/api/prompts/{prompt_id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_use_prompt(client: AsyncClient):
    """Test marking a prompt as used (increments usage count)"""
    create_resp = await client.post("/api/prompts", json={
        "title": "Email Response Template",
        "content": "Write a professional email response",
        "category": "writing"
    })
    prompt_id = create_resp.json()["id"]

    # Get initial usage count
    response = await client.get(f"/api/prompts/{prompt_id}")
    initial_count = response.json()["usage_count"]
    assert initial_count == 0

    # Mark as used
    response = await client.post(f"/api/prompts/{prompt_id}/use")
    assert response.status_code == 200
    data = response.json()
    assert data["usage_count"] == 1

    # Use again
    response = await client.post(f"/api/prompts/{prompt_id}/use")
    data = response.json()
    assert data["usage_count"] == 2


@pytest.mark.asyncio
async def test_list_categories(client: AsyncClient):
    """Test listing all prompt categories"""
    await client.post("/api/prompts", json={
        "title": "Prompt 1",
        "content": "Content 1",
        "category": "writing"
    })
    await client.post("/api/prompts", json={
        "title": "Prompt 2",
        "content": "Content 2",
        "category": "coding"
    })
    await client.post("/api/prompts", json={
        "title": "Prompt 3",
        "content": "Content 3",
        "category": "writing"
    })

    response = await client.get("/api/prompts/categories/list")
    assert response.status_code == 200
    categories = response.json()
    assert isinstance(categories, list)
    assert "writing" in categories
    assert "coding" in categories
    assert len(categories) == len(set(categories))


@pytest.mark.asyncio
async def test_toggle_prompt_active(client: AsyncClient):
    """Test toggling prompt active/inactive status"""
    create_resp = await client.post("/api/prompts", json={
        "title": "Email Response Template",
        "content": "Write a professional email response",
        "category": "writing"
    })
    prompt_id = create_resp.json()["id"]

    # Deactivate
    response = await client.put(
        f"/api/prompts/{prompt_id}",
        json={"is_active": False}
    )
    assert response.status_code == 200
    assert response.json()["is_active"] is False

    # Reactivate
    response = await client.put(
        f"/api/prompts/{prompt_id}",
        json={"is_active": True}
    )
    assert response.status_code == 200
    assert response.json()["is_active"] is True


@pytest.mark.asyncio
async def test_inactive_prompts_not_in_default_list(client: AsyncClient):
    """Test that inactive prompts don't appear in default list"""
    create_resp = await client.post("/api/prompts", json={
        "title": "Email Response Template",
        "content": "Write a professional email response",
        "category": "writing"
    })
    prompt_id = create_resp.json()["id"]

    # Deactivate
    await client.put(f"/api/prompts/{prompt_id}", json={"is_active": False})

    # Default list (active_only=True)
    response = await client.get("/api/prompts")
    data = response.json()
    titles = [p["title"] for p in data]
    assert "Email Response Template" not in titles

    # With active_only=False
    response = await client.get("/api/prompts?active_only=false")
    data = response.json()
    titles = [p["title"] for p in data]
    assert "Email Response Template" in titles


@pytest.mark.asyncio
async def test_404_for_nonexistent_prompt(client: AsyncClient):
    """Test 404 responses for non-existent prompts"""
    fake_id = "00000000-0000-0000-0000-000000000000"

    response = await client.get(f"/api/prompts/{fake_id}")
    assert response.status_code == 404

    response = await client.put(
        f"/api/prompts/{fake_id}",
        json={"title": "Test"}
    )
    assert response.status_code == 404

    response = await client.delete(f"/api/prompts/{fake_id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_prompt_usage_count_ordering(client: AsyncClient):
    """Test that prompts are ordered by usage count"""
    # Create prompts
    prompt1 = await client.post("/api/prompts", json={
        "title": "Least Used",
        "content": "Content 1",
        "category": "general"
    })
    prompt1_data = prompt1.json()

    prompt2 = await client.post("/api/prompts", json={
        "title": "Most Used",
        "content": "Content 2",
        "category": "general"
    })
    prompt2_data = prompt2.json()

    # Mark prompt2 as used multiple times
    for _ in range(3):
        await client.post(f"/api/prompts/{prompt2_data['id']}/use")

    # List and verify ordering
    response = await client.get("/api/prompts")
    data = response.json()

    # Most used should come first
    assert data[0]["title"] == "Most Used"
    assert data[0]["usage_count"] == 3
    assert data[1]["usage_count"] == 0


@pytest.mark.asyncio
async def test_prompt_with_tags(client: AsyncClient):
    """Test creating and retrieving prompts with tags"""
    response = await client.post("/api/prompts", json={
        "title": "Tagged Prompt",
        "content": "Content with tags",
        "category": "general",
        "tags": ["tag1", "tag2", "tag3"]
    })
    assert response.status_code == 201
    data = response.json()
    assert data["tags"] == ["tag1", "tag2", "tag3"]

    # Retrieve and verify tags persist
    response = await client.get(f"/api/prompts/{data['id']}")
    assert response.json()["tags"] == ["tag1", "tag2", "tag3"]
