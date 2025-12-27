"""Test suite for Keyboard Shortcuts feature.

This test suite verifies:
1. useKeyboardShortcuts hook exists and is properly implemented
2. Global keyboard shortcuts are registered
3. Shortcuts work when not typing in input fields
4. Shortcuts don't interfere with typing in inputs
5. All documented shortcuts are implemented
"""

import pytest
import os


@pytest.mark.asyncio
async def test_keyboard_shortcuts_hook_exists():
    """Test that useKeyboardShortcuts hook exists."""
    hook_path = "client/src/hooks/useKeyboardShortcuts.ts"

    assert os.path.exists(hook_path), "useKeyboardShortcuts.ts hook should exist"

    with open(hook_path, 'r') as f:
        content = f.read()

    # Verify hook structure
    assert "export function useKeyboardShortcuts" in content, \
        "Should export useKeyboardShortcuts function"
    assert "useEffect" in content, "Should use useEffect for event listeners"
    assert "addEventListener('keydown'" in content, \
        "Should register keyboard event listener"

    print("✓ useKeyboardShortcuts hook exists with proper structure")


@pytest.mark.asyncio
async def test_keyboard_shortcuts_has_shortcuts_defined():
    """Test that keyboard shortcuts are defined."""
    hook_path = "client/src/hooks/useKeyboardShortcuts.ts"

    with open(hook_path, 'r') as f:
        content = f.read()

    # Verify shortcuts array
    assert "shortcuts:" in content or "shortcuts =" in content, \
        "Should have shortcuts array"
    assert "KeyboardShortcut[]" in content or ": KeyboardShortcut" in content, \
        "Should have KeyboardShortcut type"

    # Verify essential shortcuts
    essential_shortcuts = [
        ('k', 'New conversation'),
        ('b', 'Toggle sidebar'),
        ('d', 'Toggle dark mode'),
        (',', 'Open settings'),
        ('1', 'Select Sonnet model'),
        ('2', 'Select Haiku model'),
        ('e', 'Toggle extended thinking'),
        ('m', 'Toggle memory'),
    ]

    for key, desc in essential_shortcuts:
        # Special handling for backslash which is escaped
        if key == '\\':
            assert "\\\\\\'" in content or '"\\\\"' in content or "key: '\\\\'" in content, \
                f"Should have shortcut for key: {key}"
        else:
            assert f"'{key}'" in content or f'"{key}"' in content, \
                f"Should have shortcut for key: {key}"
        assert desc in content, f"Should have shortcut: {desc}"

    # Also verify backslash shortcut separately
    assert "Toggle right panel" in content, "Should have toggle right panel shortcut"

    print(f"✓ All {len(essential_shortcuts)} essential shortcuts defined")


@pytest.mark.asyncio
async def test_keyboard_shortcuts_ignore_inputs():
    """Test that shortcuts don't trigger when typing in input fields."""
    hook_path = "client/src/hooks/useKeyboardShortcuts.ts"

    with open(hook_path, 'r') as f:
        content = f.read()

    # Verify input detection
    assert "tagName === 'INPUT'" in content or "target.tagName" in content, \
        "Should check if target is an input"
    assert "tagName === 'TEXTAREA'" in content, \
        "Should check if target is a textarea"
    assert "contentEditable" in content, \
        "Should check contentEditable attribute"

    print("✓ Input field detection implemented")


@pytest.mark.asyncio
async def test_keyboard_shortcuts_modifier_keys():
    """Test that shortcuts support modifier keys (Ctrl, Cmd, Shift, Alt)."""
    hook_path = "client/src/hooks/useKeyboardShortcuts.ts"

    with open(hook_path, 'r') as f:
        content = f.read()

    # Verify modifier key handling
    assert "ctrlKey" in content, "Should handle Ctrl key"
    assert "metaKey" in content, "Should handle Cmd (meta) key"
    assert "shiftKey" in content, "Should handle Shift key"
    assert "altKey" in content, "Should handle Alt key"

    print("✓ Modifier key support implemented")


@pytest.mark.asyncio
async def test_keyboard_shortcuts_prevent_default():
    """Test that shortcuts prevent default browser behavior."""
    hook_path = "client/src/hooks/useKeyboardShortcuts.ts"

    with open(hook_path, 'r') as f:
        content = f.read()

    # Verify preventDefault
    assert "preventDefault()" in content, \
        "Should prevent default behavior for shortcuts"

    print("✓ Default behavior prevention implemented")


@pytest.mark.asyncio
async def test_keyboard_shortcuts_help_hook():
    """Test that useKeyboardShortcutsHelp hook exists."""
    hook_path = "client/src/hooks/useKeyboardShortcuts.ts"

    with open(hook_path, 'r') as f:
        content = f.read()

    # Verify help hook
    assert "export function useKeyboardShortcutsHelp" in content, \
        "Should export useKeyboardShortcutsHelp hook"
    assert "formatShortcut" in content, \
        "Should have formatShortcut function"

    print("✓ Keyboard shortcuts help hook exists")


@pytest.mark.asyncio
async def test_keyboard_shortcuts_integration():
    """Test that keyboard shortcuts are integrated into Layout."""
    layout_path = "client/src/components/Layout.tsx"

    with open(layout_path, 'r') as f:
        content = f.read()

    # Verify hook usage
    assert "useKeyboardShortcuts" in content, \
        "Layout should use useKeyboardShortcuts hook"

    print("✓ Keyboard shortcuts integrated into Layout")


@pytest.mark.asyncio
async def test_keyboard_shortcuts_action_execution():
    """Test that shortcuts execute their actions."""
    hook_path = "client/src/hooks/useKeyboardShortcuts.ts"

    with open(hook_path, 'r') as f:
        content = f.read()

    # Verify action execution
    assert ".action(" in content or "action(e)" in content, \
        "Should call action function on shortcut match"

    print("✓ Action execution implemented")


@pytest.mark.asyncio
async def test_keyboard_shortcuts_cleanup():
    """Test that keyboard event listeners are cleaned up."""
    hook_path = "client/src/hooks/useKeyboardShortcuts.ts"

    with open(hook_path, 'r') as f:
        content = f.read()

    # Verify cleanup
    assert "removeEventListener('keydown'" in content, \
        "Should remove event listener on cleanup"

    print("✓ Event listener cleanup implemented")


@pytest.mark.asyncio
async def test_keyboard_shortcuts_navigator_integration():
    """Test that shortcuts use React Router navigation."""
    hook_path = "client/src/hooks/useKeyboardShortcuts.ts"

    with open(hook_path, 'r') as f:
        content = f.read()

    # Verify navigation hook usage
    assert "useNavigate" in content, \
        "Should use React Router's useNavigate hook"
    assert "navigate(" in content, \
        "Should call navigate function for navigation shortcuts"

    print("✓ React Router navigation integrated")


@pytest.mark.asyncio
async def test_keyboard_shortcuts_store_integration():
    """Test that shortcuts use UI and conversation stores."""
    hook_path = "client/src/hooks/useKeyboardShortcuts.ts"

    with open(hook_path, 'r') as f:
        content = f.read()

    # Verify store usage
    assert "useUIStore" in content, \
        "Should use useUIStore hook"
    assert "useConversationStore" in content, \
        "Should use useConversationStore hook"

    # Verify store actions are called
    assert "toggleSidebar" in content, \
        "Should call toggleSidebar action"
    assert "togglePanel" in content, \
        "Should call togglePanel action"
    assert "createConversation" in content, \
        "Should call createConversation action"

    print("✓ Store integration implemented")


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
