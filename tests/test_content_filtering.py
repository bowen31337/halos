"""Test content filtering functionality."""

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from src.core.database import Base, get_db
from src.main import app
from src.api.routes.settings import user_settings
from src.utils.content_filter import (
    get_content_filter_instructions,
    apply_content_filtering_to_message,
    should_filter_response,
)


# Test database
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_content_filter.db"


@pytest.fixture
async def test_db():
    """Create a test database."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        async def override_get_db():
            yield session

        app.dependency_overrides[get_db] = override_get_db
        yield session

    app.dependency_overrides.clear()
    await engine.dispose()


# Save original settings
original_settings = user_settings.copy()


@pytest.fixture(autouse=True)
def reset_settings():
    """Reset settings after each test."""
    yield
    user_settings.clear()
    user_settings.update(original_settings)


class TestContentFilteringUtility:
    """Test content filtering utility functions."""

    def test_get_filter_instructions_off(self):
        """Test filter instructions when level is off."""
        user_settings["content_filter_level"] = "off"
        user_settings["content_filter_categories"] = ["violence", "hate"]

        instructions = get_content_filter_instructions()
        assert instructions == ""

    def test_get_filter_instructions_low(self):
        """Test filter instructions at low level."""
        user_settings["content_filter_level"] = "low"
        user_settings["content_filter_categories"] = ["violence"]

        instructions = get_content_filter_instructions()
        assert "[CONTENT FILTERING: LOW LEVEL]" in instructions
        assert "basic content filtering" in instructions.lower()

    def test_get_filter_instructions_medium(self):
        """Test filter instructions at medium level."""
        user_settings["content_filter_level"] = "medium"
        user_settings["content_filter_categories"] = ["violence", "hate"]

        instructions = get_content_filter_instructions()
        assert "[CONTENT FILTERING: MEDIUM LEVEL]" in instructions
        assert "standard content filtering" in instructions.lower()

    def test_get_filter_instructions_high(self):
        """Test filter instructions at high level."""
        user_settings["content_filter_level"] = "high"
        user_settings["content_filter_categories"] = ["sexual"]

        instructions = get_content_filter_instructions()
        assert "[CONTENT FILTERING: HIGH LEVEL]" in instructions
        assert "strict content filtering" in instructions.lower()

    def test_get_filter_instructions_no_categories(self):
        """Test filter instructions with no categories selected."""
        user_settings["content_filter_level"] = "medium"
        user_settings["content_filter_categories"] = []

        instructions = get_content_filter_instructions()
        assert instructions == ""

    def test_apply_filtering_to_message(self):
        """Test that filtering is applied to message."""
        user_settings["content_filter_level"] = "high"
        user_settings["content_filter_categories"] = ["violence"]

        original_message = "Tell me a story"
        filtered_message = apply_content_filtering_to_message(original_message)

        assert "[CONTENT FILTERING" in filtered_message
        assert original_message in filtered_message

    def test_apply_filtering_off_no_change(self):
        """Test that message is unchanged when filtering is off."""
        user_settings["content_filter_level"] = "off"
        user_settings["content_filter_categories"] = ["violence"]

        original_message = "Tell me a story"
        filtered_message = apply_content_filtering_to_message(original_message)

        assert filtered_message == original_message

    def test_should_filter_response_off(self):
        """Test response filtering when level is off."""
        user_settings["content_filter_level"] = "off"
        user_settings["content_filter_categories"] = ["violence"]

        should_filter, reason = should_filter_response("This is violent content")
        assert should_filter is False
        assert reason is None


class TestContentFilteringAPI:
    """Test content filtering API endpoints."""

    @pytest.mark.asyncio
    async def test_settings_includes_content_filter_fields(self):
        """Test that user_settings includes content filtering."""
        assert "content_filter_level" in user_settings
        assert "content_filter_categories" in user_settings

    @pytest.mark.asyncio
    async def test_get_settings_returns_content_filter(self):
        """Test GET /api/settings returns content filtering settings."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/settings")

            assert response.status_code == 200
            data = response.json()
            assert "content_filter_level" in data
            assert "content_filter_categories" in data

    @pytest.mark.asyncio
    async def test_update_content_filter_level(self):
        """Test PUT /api/settings updates content filter level."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Set to high
            response = await client.put("/api/settings", json={
                "content_filter_level": "high"
            })

            assert response.status_code == 200
            data = response.json()
            assert data["content_filter_level"] == "high"

    @pytest.mark.asyncio
    async def test_update_content_filter_categories(self):
        """Test PUT /api/settings updates content filter categories."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Update categories
            new_categories = ["violence", "hate", "sexual"]
            response = await client.put("/api/settings", json={
                "content_filter_categories": new_categories
            })

            assert response.status_code == 200
            data = response.json()
            assert data["content_filter_categories"] == new_categories

    @pytest.mark.asyncio
    async def test_update_both_level_and_categories(self):
        """Test updating both level and categories together."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.put("/api/settings", json={
                "content_filter_level": "high",
                "content_filter_categories": ["violence", "hate", "sexual", "self-harm", "illegal"]
            })

            assert response.status_code == 200
            data = response.json()
            assert data["content_filter_level"] == "high"
            assert len(data["content_filter_categories"]) == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
