"""Tests for conversation sharing feature (Feature #72)."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from src.main import app
from src.core.database import get_db, Base
from src.models import Conversation, Message


# Test database setup
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestAsyncSession = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


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


class TestSharingAPI:
    """Test sharing API endpoints."""

    @pytest.mark.asyncio
    async def test_create_share_link(self, client: TestClient, db_session: AsyncSession):
        """Test creating a share link for a conversation."""
        # Create a test conversation
        conv = Conversation(
            title="Test Conversation",
            model="claude-sonnet-4-5-20250929"
        )
        db_session.add(conv)
        await db_session.commit()
        await db_session.refresh(conv)

        # Create share link
        response = client.post(
            f"/api/conversations/{conv.id}/share",
            json={
                "access_level": "read",
                "allow_comments": False,
                "expires_in_days": 7
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert "share_token" in data
        assert data["access_level"] == "read"
        assert data["allow_comments"] is False
        assert data["expires_at"] is not None

    @pytest.mark.asyncio
    async def test_view_shared_conversation(self, client: TestClient, db_session: AsyncSession):
        """Test viewing a shared conversation by token."""
        # Create conversation with messages
        conv = Conversation(
            title="Shared Conversation",
            model="claude-sonnet-4-5-20250929"
        )
        db_session.add(conv)
        await db_session.commit()
        await db_session.refresh(conv)

        # Add messages
        msg1 = Message(
            conversation_id=conv.id,
            role="user",
            content="Hello, this is a test"
        )
        msg2 = Message(
            conversation_id=conv.id,
            role="assistant",
            content="Hi there!"
        )
        db_session.add_all([msg1, msg2])
        await db_session.commit()

        # Create share link
        share_response = client.post(
            f"/api/conversations/{conv.id}/share",
            json={"access_level": "read"}
        )
        share_token = share_response.json()["share_token"]

        # View shared conversation
        response = client.get(f"/api/conversations/share/{share_token}")

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Shared Conversation"
        assert data["model"] == "claude-sonnet-4-5-20250929"
        assert len(data["messages"]) == 2
        assert data["access_level"] == "read"

    @pytest.mark.asyncio
    async def test_revoke_share_link(self, client: TestClient, db_session: AsyncSession):
        """Test revoking a share link."""
        # Create conversation
        conv = Conversation(
            title="Test Conversation",
            model="claude-sonnet-4-5-20250929"
        )
        db_session.add(conv)
        await db_session.commit()
        await db_session.refresh(conv)

        # Create share link
        share_response = client.post(
            f"/api/conversations/{conv.id}/share",
            json={"access_level": "read"}
        )
        share_token = share_response.json()["share_token"]

        # Verify it works
        view_response = client.get(f"/api/conversations/share/{share_token}")
        assert view_response.status_code == 200

        # Revoke the link
        revoke_response = client.delete(f"/api/conversations/share/{share_token}")
        assert revoke_response.status_code == 204

        # Verify it no longer works
        view_response = client.get(f"/api/conversations/share/{share_token}")
        assert view_response.status_code == 403

    @pytest.mark.asyncio
    async def test_list_conversation_shares(self, client: TestClient, db_session: AsyncSession):
        """Test listing all share links for a conversation."""
        # Create conversation
        conv = Conversation(
            title="Test Conversation",
            model="claude-sonnet-4-5-20250929"
        )
        db_session.add(conv)
        await db_session.commit()
        await db_session.refresh(conv)

        # Create multiple share links
        client.post(
            f"/api/conversations/{conv.id}/share",
            json={"access_level": "read"}
        )
        client.post(
            f"/api/conversations/{conv.id}/share",
            json={"access_level": "comment"}
        )

        # List shares
        response = client.get(f"/api/conversations/{conv.id}/shares")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    @pytest.mark.asyncio
    async def test_share_with_different_access_levels(self, client: TestClient, db_session: AsyncSession):
        """Test different access levels for sharing."""
        conv = Conversation(
            title="Test Conversation",
            model="claude-sonnet-4-5-20250929"
        )
        db_session.add(conv)
        await db_session.commit()
        await db_session.refresh(conv)

        # Test read access
        response = client.post(
            f"/api/conversations/{conv.id}/share",
            json={"access_level": "read"}
        )
        assert response.json()["access_level"] == "read"

        # Test comment access
        response = client.post(
            f"/api/conversations/{conv.id}/share",
            json={"access_level": "comment", "allow_comments": True}
        )
        assert response.json()["access_level"] == "comment"
        assert response.json()["allow_comments"] is True

        # Test edit access
        response = client.post(
            f"/api/conversations/{conv.id}/share",
            json={"access_level": "edit"}
        )
        assert response.json()["access_level"] == "edit"
