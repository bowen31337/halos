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
async def test_list_mcp_server_types(client: AsyncClient):
    """Test listing available MCP server types"""
    response = await client.get("/api/mcp/types/list")
    assert response.status_code == 200
    types = response.json()
    assert isinstance(types, list)
    assert len(types) > 0
    # Check for expected server types
    types_list = [t["type"] for t in types]
    assert "filesystem" in types_list
    assert "github" in types_list


@pytest.mark.asyncio
async def test_create_mcp_server(client: AsyncClient):
    """Test creating a new MCP server"""
    response = await client.post(
        "/api/mcp",
        json={
            "name": "Test Filesystem Server",
            "server_type": "filesystem",
            "config": {"root_path": "/tmp", "permissions": "read"},
            "description": "Test server for filesystem access"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Filesystem Server"
    assert data["server_type"] == "filesystem"
    assert data["config"]["root_path"] == "/tmp"
    assert data["is_active"] is True
    assert "id" in data
    return data["id"]


@pytest.mark.asyncio
async def test_list_mcp_servers(client: AsyncClient):
    """Test listing MCP servers"""
    # Create a server first
    await client.post("/api/mcp", json={
        "name": "Test Server",
        "server_type": "filesystem",
        "config": {"root_path": "/tmp"}
    })

    response = await client.get("/api/mcp")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert data[0]["name"] == "Test Server"


@pytest.mark.asyncio
async def test_get_mcp_server(client: AsyncClient):
    """Test getting a specific MCP server"""
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
        "name": "Test Server",
        "server_type": "filesystem",
        "config": {"root_path": "/tmp"}
    })
    server_id = create_resp.json()["id"]

    response = await client.put(
        f"/api/mcp/{server_id}",
        json={
            "name": "Updated Server",
            "description": "Updated description",
            "config": {"root_path": "/var/tmp"}
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Server"
    assert data["description"] == "Updated description"


@pytest.mark.asyncio
async def test_delete_mcp_server(client: AsyncClient):
    """Test deleting an MCP server"""
    create_resp = await client.post("/api/mcp", json={
        "name": "Test Server",
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
async def test_test_mcp_server(client: AsyncClient):
    """Test testing an MCP server connection"""
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
    assert data["health_status"] == "healthy"
    assert "last_check" in data


@pytest.mark.asyncio
async def test_test_connection_before_save(client: AsyncClient):
    """Test testing connection before saving a server"""
    response = await client.post(
        "/api/mcp/test-connection",
        json={
            "server_type": "filesystem",
            "config": {"root_path": "/tmp"}
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "available_tools" in data


@pytest.mark.asyncio
async def test_get_server_tools(client: AsyncClient):
    """Test getting available tools from a server"""
    create_resp = await client.post("/api/mcp", json={
        "name": "Test Server",
        "server_type": "filesystem",
        "config": {"root_path": "/tmp"}
    })
    server_id = create_resp.json()["id"]

    # Update to add tools
    await client.put(
        f"/api/mcp/{server_id}",
        json={"available_tools": ["read_file", "write_file", "list_files"]}
    )

    response = await client.post(f"/api/mcp/{server_id}/tools")
    assert response.status_code == 200
    data = response.json()
    assert data["server_id"] == server_id
    assert len(data["tools"]) == 3


@pytest.mark.asyncio
async def test_toggle_mcp_server_active(client: AsyncClient):
    """Test toggling MCP server active status"""
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
async def test_filter_active_servers(client: AsyncClient):
    """Test filtering servers by active status"""
    # Create active server
    await client.post("/api/mcp", json={
        "name": "Active Server",
        "server_type": "filesystem",
        "config": {"root_path": "/tmp"},
        "is_active": True
    })
    # Create inactive server
    inactive_resp = await client.post("/api/mcp", json={
        "name": "Inactive Server",
        "server_type": "filesystem",
        "config": {"root_path": "/tmp"},
        "is_active": False
    })
    inactive_id = inactive_resp.json()["id"]
    # Set it to inactive via update
    await client.put(f"/api/mcp/{inactive_id}", json={"is_active": False})

    # List with filter
    response = await client.get("/api/mcp?active_only=true")
    assert response.status_code == 200
    data = response.json()
    # Should only see active servers
    for server in data:
        assert server["is_active"] is True


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

    response = await client.post(f"/api/mcp/{fake_id}/tools")
    assert response.status_code == 404
