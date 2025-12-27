"""Pytest configuration and shared fixtures."""

import asyncio
import os
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from httpx import AsyncClient
from httpx import ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from playwright.sync_api import Page, BrowserContext

from src.main import app
from src.core.database import Base, get_db


# Test database URL - use in-memory database for tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session", autouse=True)
def use_mock_agent() -> Generator[None, None, None]:
    """Force use of MockAgent by temporarily removing API keys during tests."""
    import os
    from src.core.config import get_settings, settings as global_settings

    # Save original API key
    original_api_key = os.environ.get("ANTHROPIC_API_KEY")
    original_base_url = os.environ.get("ANTHROPIC_BASE_URL")

    # Remove API key to force MockAgent
    if "ANTHROPIC_API_KEY" in os.environ:
        del os.environ["ANTHROPIC_API_KEY"]
    if "ANTHROPIC_BASE_URL" in os.environ:
        del os.environ["ANTHROPIC_BASE_URL"]

    # Also clear any other API key variants
    for key in list(os.environ.keys()):
        if key.startswith("ANTHROPIC_API_KEY"):
            del os.environ[key]

    # Clear the cached settings
    get_settings.cache_clear()

    # Update the module-level settings variable to use new settings without API key
    new_settings = get_settings()
    global_settings.anthropic_api_key = None
    global_settings.__dict__.update(new_settings.__dict__)

    # Clear the agent_service cache and reset api_key
    # Also update the settings reference to the new instance
    from src.services.agent_service import agent_service as agent_service_instance
    agent_service_instance.agents.clear()
    agent_service_instance.api_key = None
    agent_service_instance.settings = global_settings

    yield

    # Restore original API key
    if original_api_key:
        os.environ["ANTHROPIC_API_KEY"] = original_api_key
    if original_base_url:
        os.environ["ANTHROPIC_BASE_URL"] = original_base_url

    # Clear cache again
    get_settings.cache_clear()


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def test_db() -> AsyncGenerator[AsyncSession, None]:
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
async def client(test_db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create an async HTTP client for testing."""

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield test_db

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def browser_context():
    """Create a browser context for testing."""
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1280, "height": 720},
            locale="en-US",
            timezone_id="America/New_York"
        )
        page = context.new_page()
        yield page
        context.close()
        browser.close()


@pytest.fixture(scope="function")
def page(browser_context):
    """Provide a page fixture from browser context."""
    return browser_context
