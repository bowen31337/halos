"""Tests for API Key Management Feature (Feature #81)."""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from src.core.database import Base, get_db
from src.main import app


TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
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


@pytest.mark.asyncio
async def test_validate_api_key_endpoint(test_db):
    """Test API key validation endpoint."""
    app.dependency_overrides[get_db] = lambda: test_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Test 1: Valid Anthropic API key format
        response = await client.post(
            "/api/settings/api-key/validate",
            json={"api_key": "sk-ant-1234567890abcdef1234567890abcdef1234567890abcdef1234567890"}
        )
        assert response.status_code == 200
        result = response.json()
        assert result["valid"] is True
        assert "sk-ant-" in result["key_preview"]
        assert "valid" in result["message"].lower()

        # Test 2: Invalid key - too short
        response = await client.post(
            "/api/settings/api-key/validate",
            json={"api_key": "short"}
        )
        assert response.status_code == 200
        result = response.json()
        assert result["valid"] is False
        assert "too short" in result["message"].lower()

        # Test 3: Invalid key - wrong format
        response = await client.post(
            "/api/settings/api-key/validate",
            json={"api_key": "wrong-format-key"}
        )
        assert response.status_code == 200
        result = response.json()
        assert result["valid"] is False
        assert "format" in result["message"].lower()

        # Test 4: Empty key
        response = await client.post(
            "/api/settings/api-key/validate",
            json={"api_key": ""}
        )
        assert response.status_code == 200
        result = response.json()
        assert result["valid"] is False

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_save_api_key_endpoint(test_db):
    """Test API key saving endpoint."""
    app.dependency_overrides[get_db] = lambda: test_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Test 1: Save valid key
        response = await client.post(
            "/api/settings/api-key/save",
            json={"api_key": "sk-ant-1234567890abcdef1234567890abcdef1234567890abcdef1234567890"}
        )
        assert response.status_code == 200
        result = response.json()
        assert "saved successfully" in result["message"]
        assert "sk-ant-" in result["key_preview"]

        # Test 2: Try to save invalid key
        response = await client.post(
            "/api/settings/api-key/save",
            json={"api_key": "invalid"}
        )
        assert response.status_code == 400  # Should fail validation

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_api_key_status_endpoint(test_db):
    """Test API key status endpoint."""
    app.dependency_overrides[get_db] = lambda: test_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Test 1: Get status before saving
        response = await client.get("/api/settings/api-key/status")
        assert response.status_code == 200
        result = response.json()
        assert "configured" in result
        assert "has_saved_key" in result
        assert "key_preview" in result

        # Test 2: Save a key and check status
        await client.post(
            "/api/settings/api-key/save",
            json={"api_key": "sk-ant-1234567890abcdef1234567890abcdef1234567890abcdef1234567890"}
        )
        response = await client.get("/api/settings/api-key/status")
        assert response.status_code == 200
        result = response.json()
        assert result["has_saved_key"] is True

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_remove_api_key_endpoint(test_db):
    """Test API key removal endpoint."""
    app.dependency_overrides[get_db] = lambda: test_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # First save a key
        await client.post(
            "/api/settings/api-key/save",
            json={"api_key": "sk-ant-1234567890abcdef1234567890abcdef1234567890abcdef1234567890"}
        )

        # Verify it's saved
        status = await client.get("/api/settings/api-key/status")
        assert status.json()["has_saved_key"] is True

        # Remove the key
        response = await client.delete("/api/settings/api-key")
        assert response.status_code == 200
        result = response.json()
        assert "removed" in result["message"].lower()

        # Verify it's gone
        status = await client.get("/api/settings/api-key/status")
        assert status.json()["has_saved_key"] is False

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_api_key_workflow(test_db):
    """Test complete API key management workflow."""
    app.dependency_overrides[get_db] = lambda: test_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Step 1: Check initial status
        status = await client.get("/api/settings/api-key/status")
        assert status.json()["has_saved_key"] is False

        # Step 2: Validate a key
        valid_key = "sk-ant-1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
        validation = await client.post(
            "/api/settings/api-key/validate",
            json={"api_key": valid_key}
        )
        assert validation.json()["valid"] is True

        # Step 3: Save the key
        save = await client.post(
            "/api/settings/api-key/save",
            json={"api_key": valid_key}
        )
        assert save.status_code == 200

        # Step 4: Verify status shows key saved
        status = await client.get("/api/settings/api-key/status")
        assert status.json()["has_saved_key"] is True
        assert "sk-ant-" in status.json()["key_preview"]

        # Step 5: Remove the key
        remove = await client.delete("/api/settings/api-key")
        assert remove.status_code == 200

        # Step 6: Verify status shows no key
        status = await client.get("/api/settings/api-key/status")
        assert status.json()["has_saved_key"] is False

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_api_key_ui_integration():
    """Test that API key UI components exist and have correct structure."""
    import os
    client_dir = "/media/DATA/projects/autonomous-coding-clone-cc/talos/client/src/components"

    settings_modal_path = os.path.join(client_dir, "SettingsModal.tsx")
    assert os.path.exists(settings_modal_path), "SettingsModal.tsx should exist"

    with open(settings_modal_path, 'r') as f:
        content = f.read()

    # Check for API key state management
    assert "apiKeyInput" in content, "apiKeyInput state should exist"
    assert "apiKeyStatus" in content, "apiKeyStatus state should exist"
    assert "validationResult" in content, "validationResult state should exist"

    # Check for API key functions
    assert "validateAPIKey" in content, "validateAPIKey function should exist"
    assert "saveAPIKey" in content, "saveAPIKey function should exist"
    assert "removeAPIKey" in content, "removeAPIKey function should exist"

    # Check for renderAPITab function
    assert "renderAPITab" in content, "renderAPITab function should exist"

    # Check for API service calls
    api_service_path = "/media/DATA/projects/autonomous-coding-clone-cc/talos/client/src/services/api.ts"
    with open(api_service_path, 'r') as f:
        api_content = f.read()

    assert "validateAPIKey" in api_content, "validateAPIKey method in api.ts"
    assert "saveAPIKey" in api_content, "saveAPIKey method in api.ts"
    assert "getAPIKeyStatus" in api_content, "getAPIKeyStatus method in api.ts"
    assert "removeAPIKey" in api_content, "removeAPIKey method in api.ts"
