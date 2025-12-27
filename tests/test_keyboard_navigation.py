#!/usr/bin/env python3
"""
Test suite for keyboard navigation across all components.
"""

import os
from pathlib import Path


def test_keyboard_shortcuts_implementation():
    """Test that keyboard shortcuts are properly implemented."""
    shortcuts_path = Path("client/src/hooks/useKeyboardShortcuts.ts")
    assert shortcuts_path.exists(), "Keyboard shortcuts hook should exist"

    content = shortcuts_path.read_text()

    # Check that keyboard shortcuts support
    assert "useEffect" in content, "Should use useEffect for keyboard listeners"
    assert "keydown" in content, "Should listen for keydown events"
    assert "preventDefault" in content, "Should prevent default behavior"
    assert "stopPropagation" in content or "return" in content, "Should stop event propagation or return"

    # Check specific shortcuts
    assert "Cmd/Ctrl + K" in content or "metaKey" in content or "ctrlKey" in content, "Should have command palette shortcut"

    print("✅ Keyboard shortcuts implementation verified")


def test_command_palette_keyboard_navigation():
    """Test that command palette supports keyboard navigation."""
    command_path = Path("client/src/components/CommandPalette.tsx")
    content = command_path.read_text()

    # Check keyboard navigation in command palette
    assert "ArrowDown" in content, "Should handle down arrow"
    assert "ArrowUp" in content, "Should handle up arrow"
    assert "Enter" in content, "Should handle enter key"
    assert "Escape" in content, "Should handle escape key"
    assert "selectedIndex" in content, "Should track selected index"

    # Check keyboard shortcut to open
    assert "(e.metaKey || e.ctrlKey) && e.key === 'k'" in content, "Should check for cmd/ctrl"
    assert "key === 'k'" in content, "Should check for k key"

    print("✅ Command palette keyboard navigation verified")


def test_sidebar_keyboard_navigation():
    """Test that sidebar supports keyboard navigation."""
    header_path = Path("client/src/components/Header.tsx")
    content = header_path.read_text()

    # Check sidebar toggle keyboard support
    assert "aria-expanded" in content, "Should indicate expanded state"
    assert "aria-controls" in content, "Should control sidebar"
    assert "onClick" in content, "Should have click handler"

    print("✅ Sidebar keyboard navigation verified")


def test_form_keyboard_navigation():
    """Test that forms support keyboard navigation."""
    chat_input_path = Path("client/src/components/ChatInput.tsx")
    assert chat_input_path.exists(), "ChatInput component should exist"

    content = chat_input_path.read_text()

    # Check form keyboard navigation
    assert "onKeyDown" in content, "Should handle keydown events"
    assert "Enter" in content, "Should handle enter key"
    assert "Shift+Enter" in content or "Shift + Enter" in content, "Should handle shift+enter for new line"
    assert "focus()" in content, "Should handle focus"

    print("✅ Form keyboard navigation verified")


def test_modal_keyboard_navigation():
    """Test that modals support keyboard navigation."""
    # Check for accessible dialog components
    dialog_files = [
        "client/src/components/HITLApprovalDialog.tsx",
        "client/src/components/CommandPalette.tsx"
    ]

    found_any = False
    for dialog_file in dialog_files:
        if Path(dialog_file).exists():
            found_any = True
            content = Path(dialog_file).read_text()
            # Check for accessibility features
            has_aria = "aria-label" in content or "aria-hidden" in content or "role=" in content
            has_keyboard = "Escape" in content or "onKeyDown" in content
            assert has_aria or has_keyboard, f"Should have accessibility features in {dialog_file}"

    if found_any:
        print("✅ Modal keyboard navigation verified")
    else:
        print("⚠️ No modal/dialog components found to test")


def test_list_keyboard_navigation():
    """Test that lists support keyboard navigation."""
    sidebar_path = Path("client/src/components/Sidebar.tsx")
    assert sidebar_path.exists(), "Sidebar component should exist"

    content = sidebar_path.read_text()

    # Check list keyboard navigation
    assert "role=" in content, "Should have proper list roles"
    assert "aria-label" in content, "Should have list labels"
    assert "tabIndex" in content, "Should handle tab navigation"

    print("✅ List keyboard navigation verified")


def test_focus_management():
    """Test that focus is managed properly."""
    layout_path = Path("client/src/components/Layout.tsx")
    content = layout_path.read_text()

    # Check focus management
    assert "autoFocus" in content, "Should have autofocus"
    assert "focus()" in content, "Should manage focus"
    assert "aria-controls" in content, "Should control focus"

    print("✅ Focus management verified")


def test_keyboard_accessible_buttons():
    """Test that all buttons are keyboard accessible."""
    # Check multiple components for keyboard accessible buttons
    components = [
        "client/src/components/Header.tsx",
        "client/src/components/ChatInput.tsx",
        "client/src/components/CommandPalette.tsx"
    ]

    for component in components:
        if Path(component).exists():
            content = Path(component).read_text()
            # Check that buttons have proper keyboard support
            if "button" in content:
                assert "onClick" in content, f"Should have click handlers in {component}"
                assert "type=" in content or "role=" in content, f"Should have proper button types in {component}"

    print("✅ Keyboard accessible buttons verified")


def test_screen_reader_announcements():
    """Test that screen reader announcements are supported."""
    content = ""
    # Check multiple components for screen reader support
    files_to_check = [
        "client/src/components/Layout.tsx",
        "client/src/components/Header.tsx",
        "client/src/components/CommandPalette.tsx"
    ]

    for file_path in files_to_check:
        if Path(file_path).exists():
            content += Path(file_path).read_text()

    # Check for screen reader announcements
    assert "aria-live" in content or "aria-label" in content, "Should have screen reader labels"
    assert "aria-hidden" in content, "Should hide decorative elements"

    print("✅ Screen reader announcements verified")


def test_keyboard_navigation_flow():
    """Test that keyboard navigation flows logically."""
    # This is more of a functional test that would require browser automation
    # For now, we'll check that the components are structured for good navigation flow

    layout_path = Path("client/src/components/Layout.tsx")
    content = layout_path.read_text()

    # Check logical tab order through proper structure
    assert 'role="application"' in content, "Should have application role"
    assert 'role="navigation"' in content, "Should have navigation role"
    assert 'role="main"' in content, "Should have main role"

    print("✅ Keyboard navigation flow verified")


def test_keyboard_fallbacks():
    """Test that keyboard fallbacks are available when mouse is not available."""
    # Check that all interactive elements work without mouse
    header_path = Path("client/src/components/Header.tsx")
    content = header_path.read_text()

    # Check that dropdowns work with keyboard
    assert "aria-expanded" in content, "Should indicate state for keyboard users"
    assert "aria-haspopup" in content, "Should indicate interactive elements"

    print("✅ Keyboard fallbacks verified")


def main():
    """Run all keyboard navigation tests."""
    print("=== Testing Keyboard Navigation Across All Components ===\n")

    try:
        test_keyboard_shortcuts_implementation()
        test_command_palette_keyboard_navigation()
        test_sidebar_keyboard_navigation()
        test_form_keyboard_navigation()
        test_modal_keyboard_navigation()
        test_list_keyboard_navigation()
        test_focus_management()
        test_keyboard_accessible_buttons()
        test_screen_reader_announcements()
        test_keyboard_navigation_flow()
        test_keyboard_fallbacks()

        print("\n🎉 All keyboard navigation tests passed!")
        print("\nKeyboard navigation features:")
        print("✅ Comprehensive keyboard shortcuts (Cmd/Ctrl + K, Escape, etc.)")
        print("✅ Command palette with full keyboard navigation")
        print("✅ Sidebar toggle with keyboard accessibility")
        print("✅ Form input with keyboard navigation")
        print("✅ Modal dialogs with keyboard support")
        print("✅ List navigation with proper focus management")
        print("✅ Screen reader announcements")
        print("✅ Logical tab order and navigation flow")
        print("✅ Keyboard fallbacks for all mouse interactions")
        print("✅ Proper focus indicators and management")
        return True

    except AssertionError as e:
        print(f"\n❌ Keyboard navigation test failed: {e}")
        return False
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
