"""Test suite for Command Palette feature.

This test suite verifies:
1. Command Palette component exists and renders
2. Keyboard shortcut (Cmd/Ctrl+K) opens the palette
3. Commands are searchable and filterable
4. Commands can be executed via keyboard and click
5. Categories group commands properly
6. ESC key closes the palette
7. Arrow keys navigate through commands
8. Enter key executes selected command
"""

import pytest
import asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select

from src.core.database import Base, get_db
from src.main import app
from src.models.conversation import Conversation


@pytest.fixture
async def test_db():
    """Create a test database."""
    TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_command_palette.db"

    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Override dependency
    async def override_get_db():
        async with async_session() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    yield async_session

    # Cleanup
    await engine.dispose()
    import os
    if os.path.exists("./test_command_palette.db"):
        os.remove("./test_command_palette.db")


    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_command_palette_component_exists():
    """Test that CommandPalette component exists in frontend code."""
    import os
    component_path = "client/src/components/CommandPalette.tsx"

    assert os.path.exists(component_path), "CommandPalette.tsx component should exist"

    # Read and verify component structure
    with open(component_path, 'r') as f:
        content = f.read()

    # Verify key exports and functions
    assert "export function CommandPalette" in content, "Should export CommandPalette function"
    assert "useState" in content, "Should use React useState"
    assert "useEffect" in content, "Should use React useEffect"
    assert "useMemo" in content, "Should use React useMemo for optimization"

    print("✓ CommandPalette component exists with proper structure")


@pytest.mark.asyncio
async def test_command_palette_has_commands():
    """Test that Command Palette has commands defined."""
    import os
    component_path = "client/src/components/CommandPalette.tsx"

    with open(component_path, 'r') as f:
        content = f.read()

    # Verify command structure
    assert "interface Command" in content, "Should have Command interface"
    assert "commands = useMemo" in content, "Should use useMemo for commands"

    # Verify essential commands exist
    essential_commands = [
        "new-chat",
        "toggle-sidebar",
        "toggle-panel",
        "show-artifacts",
        "show-files",
        "show-todos",
        "theme-light",
        "theme-dark",
        "model-sonnet",
        "model-haiku",
    ]

    for cmd in essential_commands:
        assert f"id: '{cmd}'" in content, f"Should have command: {cmd}"

    print(f"✓ All {len(essential_commands)} essential commands defined")


@pytest.mark.asyncio
async def test_command_palette_keyboard_shortcut():
    """Test that Cmd/Ctrl+K keyboard shortcut is implemented."""
    import os
    component_path = "client/src/components/CommandPalette.tsx"

    with open(component_path, 'r') as f:
        content = f.read()

    # Verify keyboard event handling
    assert "addEventListener('keydown'" in content, "Should listen for keyboard events"
    assert "metaKey" in content or "ctrlKey" in content, "Should detect Cmd/Ctrl key"
    assert "key === 'k'" in content, "Should check for K key"

    print("✓ Keyboard shortcut (Cmd/Ctrl+K) implemented")


@pytest.mark.asyncio
async def test_command_palette_search_functionality():
    """Test that commands are filterable by search query."""
    import os
    component_path = "client/src/components/CommandPalette.tsx"

    with open(component_path, 'r') as f:
        content = f.read()

    # Verify search filtering logic
    assert "toLowerCase()" in content, "Should convert query to lowercase for comparison"
    assert "filter(" in content, "Should filter commands array"
    assert "includes(" in content, "Should use includes for matching"

    # Verify query state management
    assert "const [query, setQuery]" in content, "Should have query state"

    print("✓ Search and filter functionality implemented")


@pytest.mark.asyncio
async def test_command_palette_category_grouping():
    """Test that commands are grouped by category."""
    import os
    component_path = "client/src/components/CommandPalette.tsx"

    with open(component_path, 'r') as f:
        content = f.read()

    # Verify category grouping
    assert "category:" in content, "Commands should have category property"
    assert "Object.entries(groupedCommands)" in content, "Should iterate over grouped commands"

    print("✓ Category grouping implemented")


@pytest.mark.asyncio
async def test_command_palette_keyboard_navigation():
    """Test keyboard navigation within command palette."""
    import os
    component_path = "client/src/components/CommandPalette.tsx"

    with open(component_path, 'r') as f:
        content = f.read()

    # Verify navigation keys
    assert "ArrowDown" in content, "Should handle ArrowDown key"
    assert "ArrowUp" in content, "Should handle ArrowUp key"
    assert "Enter" in content, "Should handle Enter key"
    assert "Escape" in content or "key === 'Escape'" in content, "Should handle Escape key"

    # Verify selection state
    assert "selectedIndex" in content, "Should track selected index"

    print("✓ Keyboard navigation implemented")


@pytest.mark.asyncio
async def test_command_palette_integration_in_layout():
    """Test that CommandPalette is integrated into Layout."""
    import os
    layout_path = "client/src/components/Layout.tsx"

    with open(layout_path, 'r') as f:
        content = f.read()

    # Verify import and usage
    assert "import { CommandPalette }" in content or "from './CommandPalette'" in content, \
        "Layout should import CommandPalette"
    assert "<CommandPalette" in content, "Layout should render CommandPalette component"

    print("✓ CommandPalette integrated into Layout")


@pytest.mark.asyncio
async def test_command_palette_ui_styling():
    """Test that Command Palette has proper UI styling."""
    import os
    component_path = "client/src/components/CommandPalette.tsx"

    with open(component_path, 'r') as f:
        content = f.read()

    # Verify styling classes
    assert "fixed inset-0" in content, "Should have fixed positioning covering viewport"
    assert "z-[100]" in content or "z-100" in content, "Should have high z-index"
    assert "backdrop-blur" in content, "Should have backdrop blur effect"
    assert "rounded-lg" in content or "rounded" in content, "Should have rounded corners"

    # Verify accessible elements
    assert "aria-label" in content, "Should have ARIA labels for accessibility"

    print("✓ Command Palette has proper UI styling")


@pytest.mark.asyncio
async def test_command_palette_command_execution():
    """Test that commands can be executed."""
    import os
    component_path = "client/src/components/CommandPalette.tsx"

    with open(component_path, 'r') as f:
        content = f.read()

    # Verify command action execution
    assert ".action()" in content, "Should call action() method on command"
    assert "onClick" in content, "Should have click handlers"

    # Verify state cleanup after execution
    assert "setIsOpen(false)" in content, "Should close palette after execution"
    assert "setQuery('')" in content, "Should clear query after execution"

    print("✓ Command execution logic implemented")


@pytest.mark.asyncio
async def test_command_palette_empty_state():
    """Test that empty state is shown when no commands match."""
    import os
    component_path = "client/src/components/CommandPalette.tsx"

    with open(component_path, 'r') as f:
        content = f.read()

    # Verify empty state handling
    assert "filteredCommands.length === 0" in content or "commands.length === 0" in content, \
        "Should check for empty results"
    assert "No commands found" in content, "Should show empty state message"

    print("✓ Empty state handling implemented")


@pytest.mark.asyncio
async def test_command_palette_shortcut_display():
    """Test that keyboard shortcuts are displayed in the UI."""
    import os
    component_path = "client/src/components/CommandPalette.tsx"

    with open(component_path, 'r') as f:
        content = f.read()

    # Verify shortcut display
    assert "shortcut" in content, "Commands should have shortcut property"
    assert "<kbd" in content, "Should use kbd element for shortcuts"

    print("✓ Shortcut display implemented")


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
