"""Tests for Settings API Feature (Feature #91)."""

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
async def test_get_settings(test_db):
    """Test getting user settings."""
    app.dependency_overrides[get_db] = lambda: test_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/settings")
        assert response.status_code == 200
        settings = response.json()
        assert "theme" in settings
        assert "font_size" in settings
        assert "permission_mode" in settings

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_update_settings(test_db):
    """Test updating user settings."""
    app.dependency_overrides[get_db] = lambda: test_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Update settings
        update_data = {
            "theme": "dark",
            "font_size": 18,
            "font_family": "monospace",
            "permission_mode": "auto"
        }
        response = await client.put("/api/settings", json=update_data)
        assert response.status_code == 200
        settings = response.json()
        assert settings["theme"] == "dark"
        assert settings["font_size"] == 18
        assert settings["font_family"] == "monospace"
        assert settings["permission_mode"] == "auto"

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_custom_instructions(test_db):
    """Test custom instructions endpoints."""
    app.dependency_overrides[get_db] = lambda: test_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Get custom instructions (should be empty initially)
        response = await client.get("/api/settings/custom-instructions")
        assert response.status_code == 200
        assert response.json()["instructions"] == ""

        # Update custom instructions
        response = await client.put("/api/settings/custom-instructions", json={
            "instructions": "Be concise and helpful"
        })
        assert response.status_code == 200
        assert response.json()["instructions"] == "Be concise and helpful"

        # Verify update persisted
        response = await client.get("/api/settings/custom-instructions")
        assert response.json()["instructions"] == "Be concise and helpful"

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_system_prompt(test_db):
    """Test system prompt override endpoints."""
    app.dependency_overrides[get_db] = lambda: test_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Update system prompt
        response = await client.put("/api/settings/system-prompt", json={
            "prompt": "You are a helpful coding assistant"
        })
        assert response.status_code == 200
        assert response.json()["prompt"] == "You are a helpful coding assistant"

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_permission_mode(test_db):
    """Test permission mode update."""
    app.dependency_overrides[get_db] = lambda: test_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Update permission mode - the endpoint expects mode as query param
        response = await client.put("/api/settings/permission-mode", params={"mode": "default"})
        assert response.status_code == 200
        assert response.json()["permission_mode"] == "default"

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_models_list(test_db):
    """Test models list endpoint."""
    app.dependency_overrides[get_db] = lambda: test_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/settings/models")
        assert response.status_code == 200
        models = response.json()
        assert isinstance(models, list)
        assert len(models) > 0
        assert "id" in models[0]
        assert "name" in models[0]

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_effective_instructions(test_db):
    """Test effective custom instructions endpoint."""
    app.dependency_overrides[get_db] = lambda: test_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Set global instructions
        await client.put("/api/settings/custom-instructions", json={
            "instructions": "Global instructions"
        })

        # Get effective instructions (without conversation)
        response = await client.get("/api/settings/instructions/effective")
        assert response.status_code == 200
        result = response.json()
        assert result["global_instructions"] == "Global instructions"
        assert result["effective_instructions"] == "Global instructions"

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_content_filtering_settings(test_db):
    """Test content filtering settings (Feature #137)."""
    app.dependency_overrides[get_db] = lambda: test_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Get initial settings - should include content filtering defaults
        response = await client.get("/api/settings")
        assert response.status_code == 200
        settings = response.json()
        assert "content_filter_level" in settings
        assert "content_filter_categories" in settings

        # Update content filtering level
        update_data = {
            "content_filter_level": "high",
            "content_filter_categories": ["violence", "hate", "sexual", "self-harm"]
        }
        response = await client.put("/api/settings", json=update_data)
        assert response.status_code == 200
        settings = response.json()
        assert settings["content_filter_level"] == "high"
        assert settings["content_filter_categories"] == ["violence", "hate", "sexual", "self-harm"]

        # Verify the settings persisted
        response = await client.get("/api/settings")
        assert response.status_code == 200
        settings = response.json()
        assert settings["content_filter_level"] == "high"
        assert settings["content_filter_categories"] == ["violence", "hate", "sexual", "self-harm"]

        # Test turning off content filtering
        update_data = {
            "content_filter_level": "off",
            "content_filter_categories": []
        }
        response = await client.put("/api/settings", json=update_data)
        assert response.status_code == 200
        settings = response.json()
        assert settings["content_filter_level"] == "off"
        assert settings["content_filter_categories"] == []

    app.dependency_overrides.clear()
