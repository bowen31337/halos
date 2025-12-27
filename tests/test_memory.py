"""Tests for long-term memory functionality."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from src.main import app
from src.core.database import get_db, Base
from src.models.memory import Memory


# Create test database engine
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestAsyncSession = sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


async def override_get_db():
    """Override get_db for tests."""
    async with TestAsyncSession() as session:
        yield session


@pytest.fixture
async def db_session():
    """Create a test database session with tables created."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestAsyncSession() as session:
        yield session
        await session.rollback()

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
def client():
    """Create a test client with db override."""
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


class TestMemoryAPI:
    """Test memory API endpoints."""

    @pytest.mark.asyncio
    async def test_create_memory(self, client: TestClient, db_session: AsyncSession):
        """Test creating a new memory."""
        response = client.post(
            "/api/memory",
            json={"content": "User prefers dark mode", "category": "preference"}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["content"] == "User prefers dark mode"
        assert data["category"] == "preference"
        assert data["is_active"] is True
        assert "id" in data

    @pytest.mark.asyncio
    async def test_list_memories(self, client: TestClient, db_session: AsyncSession):
        """Test listing memories."""
        # Create test memories directly in db
        memory1 = Memory(content="User likes Python", category="preference")
        memory2 = Memory(content="User works at Anthropic", category="fact")
        db_session.add_all([memory1, memory2])
        await db_session.commit()

        response = client.get("/api/memory")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert any(m["content"] == "User likes Python" for m in data)

    @pytest.mark.asyncio
    async def test_get_memory(self, client: TestClient, db_session: AsyncSession):
        """Test getting a specific memory."""
        memory = Memory(content="Test memory", category="fact")
        db_session.add(memory)
        await db_session.commit()
        await db_session.refresh(memory)

        response = client.get(f"/api/memory/{memory.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["content"] == "Test memory"

    @pytest.mark.asyncio
    async def test_update_memory(self, client: TestClient, db_session: AsyncSession):
        """Test updating a memory."""
        memory = Memory(content="Original", category="fact")
        db_session.add(memory)
        await db_session.commit()
        await db_session.refresh(memory)

        response = client.put(
            f"/api/memory/{memory.id}",
            json={"content": "Updated", "is_active": False}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["content"] == "Updated"
        assert data["is_active"] is False

    @pytest.mark.asyncio
    async def test_delete_memory(self, client: TestClient, db_session: AsyncSession):
        """Test deleting a memory."""
        memory = Memory(content="To delete", category="fact")
        db_session.add(memory)
        await db_session.commit()
        await db_session.refresh(memory)

        response = client.delete(f"/api/memory/{memory.id}")
        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_search_memories(self, client: TestClient, db_session: AsyncSession):
        """Test searching memories."""
        memory1 = Memory(content="Python programming", category="fact")
        memory2 = Memory(content="Java development", category="fact")
        memory3 = Memory(content="Python is great", category="preference")
        db_session.add_all([memory1, memory2, memory3])
        await db_session.commit()

        response = client.get("/api/memory/search?q=python")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    @pytest.mark.asyncio
    async def test_extract_memory(self, client: TestClient, db_session: AsyncSession):
        """Test extracting memory from conversation."""
        response = client.post(
            "/api/memory/extract",
            params={"content": "User mentioned they like TypeScript", "conversation_id": "test-conv-123"}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["content"] == "User mentioned they like TypeScript"
        assert data["source_conversation_id"] == "test-conv-123"

    @pytest.mark.asyncio
    async def test_filter_by_category(self, client: TestClient, db_session: AsyncSession):
        """Test filtering memories by category."""
        memory1 = Memory(content="Fact 1", category="fact")
        memory2 = Memory(content="Preference 1", category="preference")
        db_session.add_all([memory1, memory2])
        await db_session.commit()

        response = client.get("/api/memory?category=fact")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["category"] == "fact"

    @pytest.mark.asyncio
    async def test_active_only_filter(self, client: TestClient, db_session: AsyncSession):
        """Test filtering by active status."""
        memory1 = Memory(content="Active", category="fact", is_active=True)
        memory2 = Memory(content="Inactive", category="fact", is_active=False)
        db_session.add_all([memory1, memory2])
        await db_session.commit()

        # Get all
        response = client.get("/api/memory?active_only=false")
        assert response.status_code == 200
        assert len(response.json()) == 2

        # Get active only
        response = client.get("/api/memory?active_only=true")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["is_active"] is True


class TestMemoryIntegration:
    """Integration tests for memory with agent."""

    @pytest.mark.asyncio
    async def test_memory_in_agent_context(self, client: TestClient, db_session: AsyncSession):
        """Test that memories are included in agent context."""
        # Create a memory
        memory = Memory(content="User prefers dark mode", category="preference")
        db_session.add(memory)
        await db_session.commit()

        response = client.get("/api/memory")
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        assert data[0]["content"] == "User prefers dark mode"

    def test_memory_toggle_setting(self, client: TestClient):
        """Test memory enabled/disabled setting."""
        # Get initial settings
        response = client.get("/api/settings")
        assert response.status_code == 200
        initial_memory = response.json().get("memory_enabled", True)

        # Toggle memory
        response = client.put(
            "/api/settings",
            json={"memory_enabled": not initial_memory}
        )
        assert response.status_code == 200
        assert response.json()["memory_enabled"] == (not initial_memory)

        # Verify it persisted
        response = client.get("/api/settings")
        assert response.status_code == 200
        assert response.json()["memory_enabled"] == (not initial_memory)
