"""Test prompt library functionality - Feature #75"""

import pytest
from fastapi.testclient import TestClient
from src.main import app
from src.core.database import get_db
from tests.conftest import override_get_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    """Ensure clean state for tests"""
    # Database is handled by conftest
    pass


def test_create_prompt():
    """Test creating a new prompt in the library"""
    response = client.post(
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
    return data["id"]


def test_list_prompts():
    """Test listing all prompts"""
    # First create a prompt
    test_create_prompt()

    response = client.get("/api/prompts")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    # Verify the prompt we created is in the list
    titles = [p["title"] for p in data]
    assert "Email Response Template" in titles


def test_list_prompts_by_category():
    """Test filtering prompts by category"""
    # Create prompts in different categories
    client.post("/api/prompts", json={
        "title": "Code Review",
        "content": "Review this code for bugs",
        "category": "coding"
    })
    client.post("/api/prompts", json={
        "title": "Story Writing",
        "content": "Write a creative story",
        "category": "creative"
    })

    response = client.get("/api/prompts?category=coding")
    assert response.status_code == 200
    data = response.json()
    assert all(p["category"] == "coding" for p in data)


def test_search_prompts():
    """Test searching prompts by content"""
    # Create a prompt
    test_create_prompt()

    response = client.get("/api/prompts/search?q=email")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert "email" in data[0]["title"].lower() or "email" in data[0]["content"].lower()


def test_get_prompt():
    """Test retrieving a specific prompt"""
    prompt_id = test_create_prompt()

    response = client.get(f"/api/prompts/{prompt_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == prompt_id
    assert data["title"] == "Email Response Template"


def test_update_prompt():
    """Test updating an existing prompt"""
    prompt_id = test_create_prompt()

    response = client.put(
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
    # Original content should remain unchanged
    assert data["content"] == "Write a professional email response to: {query}"


def test_delete_prompt():
    """Test deleting a prompt"""
    prompt_id = test_create_prompt()

    response = client.delete(f"/api/prompts/{prompt_id}")
    assert response.status_code == 204

    # Verify it's gone
    response = client.get(f"/api/prompts/{prompt_id}")
    assert response.status_code == 404


def test_use_prompt():
    """Test marking a prompt as used (increments usage count)"""
    prompt_id = test_create_prompt()

    # Get initial usage count
    response = client.get(f"/api/prompts/{prompt_id}")
    initial_count = response.json()["usage_count"]
    assert initial_count == 0

    # Mark as used
    response = client.post(f"/api/prompts/{prompt_id}/use")
    assert response.status_code == 200
    data = response.json()
    assert data["usage_count"] == 1

    # Use again
    response = client.post(f"/api/prompts/{prompt_id}/use")
    data = response.json()
    assert data["usage_count"] == 2


def test_list_categories():
    """Test listing all prompt categories"""
    # Create prompts in different categories
    client.post("/api/prompts", json={
        "title": "Prompt 1",
        "content": "Content 1",
        "category": "writing"
    })
    client.post("/api/prompts", json={
        "title": "Prompt 2",
        "content": "Content 2",
        "category": "coding"
    })
    client.post("/api/prompts", json={
        "title": "Prompt 3",
        "content": "Content 3",
        "category": "writing"  # Duplicate category
    })

    response = client.get("/api/prompts/categories/list")
    assert response.status_code == 200
    categories = response.json()
    assert isinstance(categories, list)
    assert "writing" in categories
    assert "coding" in categories
    # Should be unique
    assert len(categories) == len(set(categories))


def test_toggle_prompt_active():
    """Test toggling prompt active/inactive status"""
    prompt_id = test_create_prompt()

    # Deactivate
    response = client.put(
        f"/api/prompts/{prompt_id}",
        json={"is_active": False}
    )
    assert response.status_code == 200
    assert response.json()["is_active"] is False

    # Reactivate
    response = client.put(
        f"/api/prompts/{prompt_id}",
        json={"is_active": True}
    )
    assert response.status_code == 200
    assert response.json()["is_active"] is True


def test_inactive_prompts_not_in_default_list():
    """Test that inactive prompts don't appear in default list"""
    prompt_id = test_create_prompt()

    # Deactivate
    client.put(f"/api/prompts/{prompt_id}", json={"is_active": False})

    # Default list (active_only=True)
    response = client.get("/api/prompts")
    data = response.json()
    titles = [p["title"] for p in data]
    assert "Email Response Template" not in titles

    # With active_only=False
    response = client.get("/api/prompts?active_only=false")
    data = response.json()
    titles = [p["title"] for p in data]
    assert "Email Response Template" in titles


def test_404_for_nonexistent_prompt():
    """Test 404 responses for non-existent prompts"""
    response = client.get("/api/prompts/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404

    response = client.put(
        "/api/prompts/00000000-0000-0000-0000-000000000000",
        json={"title": "Test"}
    )
    assert response.status_code == 404

    response = client.delete("/api/prompts/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


def test_prompt_usage_count_ordering():
    """Test that prompts are ordered by usage count"""
    # Create prompts
    prompt1 = client.post("/api/prompts", json={
        "title": "Least Used",
        "content": "Content 1",
        "category": "general"
    }).json()

    prompt2 = client.post("/api/prompts", json={
        "title": "Most Used",
        "content": "Content 2",
        "category": "general"
    }).json()

    # Mark prompt2 as used multiple times
    for _ in range(3):
        client.post(f"/api/prompts/{prompt2['id']}/use")

    # List and verify ordering
    response = client.get("/api/prompts")
    data = response.json()

    # Most used should come first
    assert data[0]["title"] == "Most Used"
    assert data[0]["usage_count"] == 3
    assert data[1]["usage_count"] == 0


def test_prompt_with_tags():
    """Test creating and retrieving prompts with tags"""
    response = client.post("/api/prompts", json={
        "title": "Tagged Prompt",
        "content": "Content with tags",
        "category": "general",
        "tags": ["tag1", "tag2", "tag3"]
    })
    assert response.status_code == 201
    data = response.json()
    assert data["tags"] == ["tag1", "tag2", "tag3"]

    # Retrieve and verify tags persist
    response = client.get(f"/api/prompts/{data['id']}")
    assert response.json()["tags"] == ["tag1", "tag2", "tag3"]
