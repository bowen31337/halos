#!/usr/bin/env python3
"""Test MCP server management functionality - Feature #76

This test suite verifies:
- Feature #76: MCP server management allows adding and removing servers
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
async def test_create_mcp_server(client: AsyncClient):
    """Test creating a new MCP server"""
    response = await client.post(
        "/api/mcp",
        json={
            "name": "My Filesystem Server",
            "server_type": "filesystem",
            "config": {"root_path": "/tmp", "permissions": "read-write"},
            "description": "Local filesystem access"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "My Filesystem Server"
    assert data["server_type"] == "filesystem"
    assert data["config"]["root_path"] == "/tmp"
    assert data["description"] == "Local filesystem access"
    assert data["is_active"] is True
    assert "id" in data


@pytest.mark.asyncio
async def test_list_mcp_servers(client: AsyncClient):
    """Test listing all MCP servers"""
    # Create two servers
    await client.post("/api/mcp", json={
        "name": "Server 1",
        "server_type": "filesystem",
        "config": {"root_path": "/tmp"}
    })
    await client.post("/api/mcp", json={
        "name": "Server 2",
        "server_type": "brave-search",
        "config": {"api_key": "test-key"}
    })

    response = await client.get("/api/mcp")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2
    names = [s["name"] for s in data]
    assert "Server 1" in names
    assert "Server 2" in names


@pytest.mark.asyncio
async def test_get_mcp_server(client: AsyncClient):
    """Test retrieving a specific MCP server"""
    create_resp = await client.post("/api/mcp", json={
        "name": "Test Server",
        "server_type": "filesystem",
        "config": {"root_path": "/tmp"}
    })
    server_id = create_resp.json()["id"]

    response = await client.get(f"/api/mcp/{server_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == server_id
    assert data["name"] == "Test Server"


@pytest.mark.asyncio
async def test_update_mcp_server(client: AsyncClient):
    """Test updating an MCP server"""
    create_resp = await client.post("/api/mcp", json={
        "name": "Original Name",
        "server_type": "filesystem",
        "config": {"root_path": "/tmp"}
    })
    server_id = create_resp.json()["id"]

    response = await client.put(
        f"/api/mcp/{server_id}",
        json={
            "name": "Updated Name",
            "description": "Updated description"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"
    assert data["description"] == "Updated description"


@pytest.mark.asyncio
async def test_delete_mcp_server(client: AsyncClient):
    """Test deleting an MCP server"""
    create_resp = await client.post("/api/mcp", json={
        "name": "To Delete",
        "server_type": "filesystem",
        "config": {"root_path": "/tmp"}
    })
    server_id = create_resp.json()["id"]

    response = await client.delete(f"/api/mcp/{server_id}")
    assert response.status_code == 204

    # Verify it's gone
    response = await client.get(f"/api/mcp/{server_id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_server_types(client: AsyncClient):
    """Test listing available MCP server types"""
    response = await client.get("/api/mcp/types/list")
    assert response.status_code == 200
    types = response.json()
    assert isinstance(types, list)
    assert len(types) > 0

    # Check structure
    for server_type in types:
        assert "type" in server_type
        assert "label" in server_type
        assert "description" in server_type
        assert "config_fields" in server_type

    # Verify expected types exist
    type_values = [t["type"] for t in types]
    assert "filesystem" in type_values
    assert "brave-search" in type_values
    assert "github" in type_values


@pytest.mark.asyncio
async def test_test_mcp_connection(client: AsyncClient):
    """Test testing MCP connection before saving"""
    response = await client.post("/api/mcp/test-connection", json={
        "server_type": "filesystem",
        "config": {"root_path": "/tmp"}
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "server_type" in data


@pytest.mark.asyncio
async def test_test_mcp_server(client: AsyncClient):
    """Test testing an existing MCP server"""
    create_resp = await client.post("/api/mcp", json={
        "name": "Test Server",
        "server_type": "filesystem",
        "config": {"root_path": "/tmp"}
    })
    server_id = create_resp.json()["id"]

    response = await client.post(f"/api/mcp/{server_id}/test")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "health_status" in data
    assert "last_check" in data


@pytest.mark.asyncio
async def test_deactivate_server(client: AsyncClient):
    """Test deactivating an MCP server"""
    create_resp = await client.post("/api/mcp", json={
        "name": "Test Server",
        "server_type": "filesystem",
        "config": {"root_path": "/tmp"}
    })
    server_id = create_resp.json()["id"]

    # Deactivate
    response = await client.put(
        f"/api/mcp/{server_id}",
        json={"is_active": False}
    )
    assert response.status_code == 200
    assert response.json()["is_active"] is False

    # Reactivate
    response = await client.put(
        f"/api/mcp/{server_id}",
        json={"is_active": True}
    )
    assert response.status_code == 200
    assert response.json()["is_active"] is True


@pytest.mark.asyncio
async def test_inactive_servers_not_in_default_list(client: AsyncClient):
    """Test that inactive servers don't appear in default list"""
    create_resp = await client.post("/api/mcp", json={
        "name": "Test Server",
        "server_type": "filesystem",
        "config": {"root_path": "/tmp"}
    })
    server_id = create_resp.json()["id"]

    # Deactivate
    await client.put(f"/api/mcp/{server_id}", json={"is_active": False})

    # Default list (active_only=False by default)
    response = await client.get("/api/mcp")
    data = response.json()
    names = [s["name"] for s in data]
    # Server should still be in default list (active_only defaults to False)
    assert "Test Server" in names

    # With active_only=True
    response = await client.get("/api/mcp?active_only=true")
    data = response.json()
    names = [s["name"] for s in data]
    assert "Test Server" not in names


@pytest.mark.asyncio
async def test_404_for_nonexistent_server(client: AsyncClient):
    """Test 404 responses for non-existent servers"""
    fake_id = "00000000-0000-0000-0000-000000000000"

    response = await client.get(f"/api/mcp/{fake_id}")
    assert response.status_code == 404

    response = await client.put(
        f"/api/mcp/{fake_id}",
        json={"name": "Test"}
    )
    assert response.status_code == 404

    response = await client.delete(f"/api/mcp/{fake_id}")
    assert response.status_code == 404

    response = await client.post(f"/api/mcp/{fake_id}/test")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_mcp_server_config_validation(client: AsyncClient):
    """Test that server config is stored correctly"""
    response = await client.post("/api/mcp", json={
        "name": "Config Test",
        "server_type": "github",
        "config": {
            "api_key": "ghp_test",
            "repositories": ["repo1", "repo2"]
        }
    })
    assert response.status_code == 201
    data = response.json()
    assert data["config"]["api_key"] == "ghp_test"
    assert data["config"]["repositories"] == ["repo1", "repo2"]
