"""Test SubAgent API endpoints.

This test verifies that:
1. Built-in subagents are accessible via GET /api/subagents/builtin
2. Custom subagents can be created via POST /api/subagents
3. Custom subagents can be retrieved via GET /api/subagents/:id
4. Custom subagents can be updated via PUT /api/subagents/:id
5. Custom subagents can be deleted via DELETE /api/subagents/:id
6. Subagent tools can be retrieved via GET /api/subagents/:id/tools
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from src.main import app
from src.core.database import get_db


@pytest_asyncio.fixture(scope="function")
async def client(test_db) -> AsyncClient:
    """Create an async HTTP client for testing with follow_redirects."""
    from sqlalchemy.ext.asyncio import AsyncSession

    async def override_get_db():
        yield test_db

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        follow_redirects=True
    ) as ac:
        yield ac

    app.dependency_overrides.clear()



@pytest.mark.asyncio
async def test_get_builtin_subagents(client: AsyncClient):
    """Test GET /api/subagents/builtin returns all built-in subagents."""
    response = await client.get("/api/subagents/builtin")
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)

    assert len(data) > 0

    # Verify expected built-in subagents exist
    names = [s["name"] for s in data]
    expected = ["research-agent", "code-review-agent", "documentation-agent", "test-writing-agent"]
    for exp in expected:
        assert exp in names, f"Expected subagent '{exp}' not found"


@pytest.mark.asyncio
async def test_create_custom_subagent(client: AsyncClient):
    """Test POST /api/subagents creates a custom subagent."""
    subagent_data = {
        "name": "test-custom-agent",
        "description": "A test custom subagent",
        "system_prompt": "You are a helpful test agent.",
        "model": "claude-sonnet-4-5-20250929",
        "tools": ["read_file", "write_file"]
    }

    response = await client.post("/api/subagents", json=subagent_data)
    assert response.status_code == 201

    data = response.json()
    assert data["name"] == "test-custom-agent"
    assert data["description"] == "A test custom subagent"
    assert data["system_prompt"] == "You are a helpful test agent."
    assert data["model"] == "claude-sonnet-4-5-20250929"
    assert data["tools"] == ["read_file", "write_file"]
    assert data["is_builtin"] == False
    assert data["is_active"] == True
    assert "id" in data
    assert data["id"] is not None

    return data["id"]  # Return ID for other tests


@pytest.mark.asyncio
async def test_get_custom_subagent(client: AsyncClient):
    """Test GET /api/subagents/:id retrieves a custom subagent."""
    # First create a subagent
    create_data = {
        "name": "test-get-agent",
        "description": "Agent for GET test",
        "system_prompt": "Test prompt",
        "model": "claude-sonnet-4-5-20250929",
        "tools": ["search"]
    }

    create_response = await client.post("/api/subagents", json=create_data)
    subagent_id = create_response.json()["id"]

    # Now retrieve it
    response = await client.get(f"/api/subagents/{subagent_id}")
    assert response.status_code == 200

    data = response.json()
    assert data["id"] == subagent_id
    assert data["name"] == "test-get-agent"
    assert data["description"] == "Agent for GET test"


@pytest.mark.asyncio
async def test_update_custom_subagent(client: AsyncClient):
    """Test PUT /api/subagents/:id updates a custom subagent."""
    # First create a subagent
    create_data = {
        "name": "test-update-agent",
        "description": "Original description",
        "system_prompt": "Original prompt",
        "model": "claude-sonnet-4-5-20250929",
        "tools": ["read_file"]
    }

    create_response = await client.post("/api/subagents", json=create_data)
    subagent_id = create_response.json()["id"]

    # Update it
    update_data = {
        "description": "Updated description",
        "system_prompt": "Updated prompt",
        "tools": ["read_file", "write_file", "edit_file"]
    }

    response = await client.put(f"/api/subagents/{subagent_id}", json=update_data)
    assert response.status_code == 200

    data = response.json()
    assert data["description"] == "Updated description"
    assert data["system_prompt"] == "Updated prompt"
    assert data["tools"] == ["read_file", "write_file", "edit_file"]
    # Name should remain unchanged
    assert data["name"] == "test-update-agent"


@pytest.mark.asyncio
async def test_delete_custom_subagent(client: AsyncClient):
    """Test DELETE /api/subagents/:id deletes a custom subagent."""
    # First create a subagent
    create_data = {
        "name": "test-delete-agent",
        "description": "To be deleted",
        "system_prompt": "Delete me",
        "model": "claude-sonnet-4-5-20250929",
        "tools": []
    }

    create_response = await client.post("/api/subagents", json=create_data)
    subagent_id = create_response.json()["id"]

    # Delete it
    response = await client.delete(f"/api/subagents/{subagent_id}")
    assert response.status_code == 204

    # Verify it's gone (should not appear in list)
    list_response = await client.get("/api/subagents/")
    subagents = list_response.json()
    deleted_found = any(s["id"] == subagent_id for s in subagents)
    assert not deleted_found, "Deleted subagent should not appear in list"


@pytest.mark.asyncio
async def test_get_subagent_tools(client: AsyncClient):
    """Test GET /api/subagents/:id/tools retrieves tools for a subagent."""
    # First create a subagent with specific tools
    create_data = {
        "name": "test-tools-agent",
        "description": "Agent with tools",
        "system_prompt": "Tool user",
        "model": "claude-sonnet-4-5-20250929",
        "tools": ["read_file", "write_file", "grep"]
    }

    create_response = await client.post("/api/subagents", json=create_data)
    subagent_id = create_response.json()["id"]

    # Get tools
    response = await client.get(f"/api/subagents/{subagent_id}/tools")
    assert response.status_code == 200

    tools = response.json()
    assert isinstance(tools, list)
    assert "read_file" in tools
    assert "write_file" in tools
    assert "grep" in tools


@pytest.mark.asyncio
async def test_builtin_subagent_tools(client: AsyncClient):
    """Test GET /api/subagents/builtin-{name}/tools for built-in subagents."""
    # Research agent should have search tool
    response = await client.get("/api/subagents/builtin-research-agent/tools")
    assert response.status_code == 200
    tools = response.json()
    assert "search" in tools

    # Code review agent should have read_file
    response = await client.get("/api/subagents/builtin-code-review-agent/tools")
    assert response.status_code == 200
    tools = response.json()
    assert "read_file" in tools


@pytest.mark.asyncio
async def test_list_subagents(client: AsyncClient):
    """Test GET /api/subagents/ lists all subagents (built-in + custom)."""
    # Create a custom subagent
    create_data = {
        "name": "test-list-agent",
        "description": "For listing test",
        "system_prompt": "List me",
        "model": "claude-sonnet-4-5-20250929",
        "tools": []
    }

    await client.post("/api/subagents", json=create_data)

    # List all subagents
    response = await client.get("/api/subagents/")
    assert response.status_code == 200

    subagents = response.json()
    assert len(subagents) > 0

    # Should include built-in subagents
    names = [s["name"] for s in subagents]
    assert "research-agent" in names
    assert "code-review-agent" in names

    # Should include our custom subagent
    assert "test-list-agent" in names


@pytest.mark.asyncio
async def test_create_duplicate_name_fails(client: AsyncClient):
    """Test that creating a subagent with duplicate name fails."""
    create_data = {
        "name": "duplicate-agent",
        "description": "First one",
        "system_prompt": "First",
        "model": "claude-sonnet-4-5-20250929",
        "tools": []
    }

    # Create first
    response1 = await client.post("/api/subagents", json=create_data)
    assert response1.status_code == 201

    # Try to create duplicate
    response2 = await client.post("/api/subagents", json=create_data)
    assert response2.status_code == 400  # Should fail


@pytest.mark.asyncio
async def test_cannot_modify_builtin_subagents(client: AsyncClient):
    """Test that built-in subagents cannot be modified or deleted."""
    # Try to update built-in
    update_data = {"description": "Trying to modify"}
    response = await client.put("/api/subagents/builtin-research-agent", json=update_data)
    assert response.status_code == 400

    # Try to delete built-in
    response = await client.delete("/api/subagents/builtin-research-agent")
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_get_nonexistent_subagent(client: AsyncClient):
    """Test GET /api/subagents/:id with non-existent ID returns 404."""
    response = await client.get("/api/subagents/nonexistent-id-12345")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_builtin_subagent_details(client: AsyncClient):
    """Test that built-in subagent details are correct."""
    response = await client.get("/api/subagents/builtin-research-agent")
    assert response.status_code == 200

    data = response.json()
    assert data["name"] == "research-agent"
    assert data["is_builtin"] == True
    assert data["is_active"] == True
    assert "description" in data
    assert "system_prompt" in data
    assert "tools" in data
    assert isinstance(data["tools"], list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
