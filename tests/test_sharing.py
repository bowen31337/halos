"""Tests for conversation sharing feature."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_share_link(async_client: AsyncClient, test_conversation_id: str):
    """Test creating a share link for a conversation."""

    response = await async_client.post(
        f"/api/conversations/{test_conversation_id}/share",
        json={
            "access_level": "read",
            "allow_comments": False,
            "expires_in_days": None
        }
    )

    assert response.status_code == 201
    data = response.json()

    assert "id" in data
    assert "share_token" in data
    assert data["access_level"] == "read"
    assert data["allow_comments"] is False
    assert data["is_public"] is True
    assert "created_at" in data
    assert data["view_count"] == 0


@pytest.mark.asyncio
async def test_create_share_link_with_expiration(async_client: AsyncClient, test_conversation_id: str):
    """Test creating a share link with expiration."""

    response = await async_client.post(
        f"/api/conversations/{test_conversation_id}/share",
        json={
            "access_level": "comment",
            "allow_comments": True,
            "expires_in_days": 7
        }
    )

    assert response.status_code == 201
    data = response.json()

    assert data["access_level"] == "comment"
    assert data["allow_comments"] is True
    assert data["expires_at"] is not None


@pytest.mark.asyncio
async def test_create_share_link_invalid_conversation(async_client: AsyncClient):
    """Test creating a share link for non-existent conversation."""

    response = await async_client.post(
        "/api/conversations/invalid-conversation-id/share",
        json={
            "access_level": "read",
            "allow_comments": False
        }
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_share_links(async_client: AsyncClient, test_conversation_id: str):
    """Test listing all share links for a conversation."""

    # Create two share links
    await async_client.post(
        f"/api/conversations/{test_conversation_id}/share",
        json={"access_level": "read", "allow_comments": False}
    )

    await async_client.post(
        f"/api/conversations/{test_conversation_id}/share",
        json={"access_level": "comment", "allow_comments": True}
    )

    # List shares
    response = await async_client.get(f"/api/conversations/{test_conversation_id}/shares")

    assert response.status_code == 200
    shares = response.json()

    assert isinstance(shares, list)
    assert len(shares) >= 2


@pytest.mark.asyncio
async def test_revoke_share_link(async_client: AsyncClient, test_conversation_id: str):
    """Test revoking a share link."""

    # Create share
    create_resp = await async_client.post(
        f"/api/conversations/{test_conversation_id}/share",
        json={"access_level": "read", "allow_comments": False}
    )

    share_token = create_resp.json()["share_token"]

    # Revoke share
    response = await async_client.delete(f"/api/conversations/share/{share_token}")

    assert response.status_code == 204

    # Verify it's revoked (should return 403 or 404)
    view_resp = await async_client.get(f"/api/conversations/share/{share_token}")
    assert view_resp.status_code in [403, 404]


@pytest.mark.asyncio
async def test_revoke_all_shares(async_client: AsyncClient, test_conversation_id: str):
    """Test revoking all share links for a conversation."""

    # Create multiple shares
    await async_client.post(
        f"/api/conversations/{test_conversation_id}/share",
        json={"access_level": "read", "allow_comments": False}
    )

    await async_client.post(
        f"/api/conversations/{test_conversation_id}/share",
        json={"access_level": "comment", "allow_comments": True}
    )

    # Revoke all
    response = await async_client.delete(f"/api/conversations/{test_conversation_id}/shares")

    assert response.status_code == 204
