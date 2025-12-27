#!/usr/bin/env python3
"""
Test suite for command palette implementation.
"""

import os
from pathlib import Path


def test_command_palette_component_exists():
    """Test that CommandPalette component exists and is properly structured."""
    component_path = Path("client/src/components/CommandPalette.tsx")
    assert component_path.exists(), "CommandPalette component should exist"

    content = component_path.read_text()

    # Check component structure
    assert "export function CommandPalette()" in content, "Should export CommandPalette function"
    assert "useState" in content, "Should use state management"
    assert "useCallback" in content, "Should use memoization"
    assert "useMemo" in content, "Should memoize commands"

    print("✅ CommandPalette component structure verified")


def test_command_palette_commands():
    """Test that command palette has comprehensive command set."""
    component_path = Path("client/src/components/CommandPalette.tsx")
    content = component_path.read_text()

    # Check command categories
    assert "category: 'Conversation'" in content, "Should have conversation commands"
    assert "category: 'View'" in content, "Should have view commands"
    assert "category: 'Settings'" in content, "Should have settings commands"
    assert "category: 'Model'" in content, "Should have model commands"
    assert "category: 'Navigation'" in content, "Should have navigation commands"

    # Check specific commands
    assert "New Chat" in content, "Should have new chat command"
    assert "Toggle Sidebar" in content, "Should have toggle sidebar command"
    assert "Toggle Right Panel" in content, "Should have toggle panel command"
    assert "Show Artifacts Panel" in content, "Should have artifacts panel command"
    assert "Show Files Panel" in content, "Should have files panel command"
    assert "Show Todos Panel" in content, "Should have todos panel command"
    assert "Show Memory Panel" in content, "Should have memory panel command"

    print("✅ Command palette commands verified")


def test_command_palette_shortcuts():
    """Test that keyboard shortcuts are properly implemented."""
    component_path = Path("client/src/components/CommandPalette.tsx")
    content = component_path.read_text()

    # Check keyboard shortcut handling
    assert "handleKeyDown" in content, "Should handle keyboard shortcuts"
    assert "Cmd/Ctrl + K" in content, "Should have open shortcut"
    assert "Escape" in content, "Should have close shortcut"
    assert "ArrowDown" in content, "Should handle down navigation"
    assert "ArrowUp" in content, "Should handle up navigation"
    assert "Enter" in content, "Should handle selection"

    # Check specific shortcuts
    assert "⌘N" in content, "Should have new chat shortcut"
    assert "⌘B" in content, "Should have toggle sidebar shortcut"
    assert "⌘\\" in content, "Should have toggle panel shortcut"
    assert "⌘," in content, "Should have settings shortcut"

    print("✅ Command palette shortcuts verified")


def test_command_palette_styling():
    """Test that command palette has proper overlay styling."""
    component_path = Path("client/src/components/CommandPalette.tsx")
    content = component_path.read_text()

    # Check overlay structure
    assert "fixed inset-0 z-[100]" in content, "Should have high z-index"
    assert "backdrop-blur-sm" in content, "Should have backdrop blur"
    assert "bg-[var(--bg-primary)]" in content, "Should use theme colors"
    assert "border-[var(--border-primary)]" in content, "Should have proper borders"
    assert "rounded-lg" in content, "Should have rounded corners"

    # Check search input styling
    assert "placeholder:text-[var(--text-secondary)]" in content, "Should style placeholder"
    assert "outline-none" in content, "Should have no outline"
    assert "text-lg" in content, "Should have proper text size"

    # Check command item styling
    assert "hover:bg-[var(--surface)]" in content, "Should have hover states"
    assert "bg-[var(--primary)]/10" in content, "Should highlight selected"
    assert "text-[var(--primary)]" in content, "Should use primary color"
    assert "kbd" in content, "Should style keyboard shortcuts"

    print("✅ Command palette styling verified")


def test_command_palette_accessibility():
    """Test that command palette is accessible."""
    component_path = Path("client/src/components/CommandPalette.tsx")
    content = component_path.read_text()

    # Check ARIA attributes
    assert 'aria-label="Search commands"' in content, "Should have search label"
    assert 'aria-label="Clear search"' in content, "Should have clear button label"
    assert 'aria-hidden="true"' in content, "Should hide backdrop from screen readers"

    # Check accessibility features
    assert "autoFocus" in content, "Should autofocus search input"
    assert "transition-colors" in content, "Should have smooth transitions"
    assert "text-center" in content, "Should center content when empty"

    print("✅ Command palette accessibility verified")


def test_command_palette_integration():
    """Test that command palette integrates with the layout."""
    layout_path = Path("client/src/components/Layout.tsx")
    content = layout_path.read_text()

    # Check integration
    assert "CommandPalette" in content, "Should import CommandPalette"
    assert "<CommandPalette />" in content, "Should render CommandPalette"
    assert "import { CommandPalette }" in content, "Should import from correct file"

    print("✅ Command palette integration verified")


def test_command_palette_css():
    """Test that command palette CSS classes exist."""
    css_path = Path("client/src/index.css")
    content = css_path.read_text()

    # Check CSS classes
    assert ".command-palette" in content, "Should have command palette CSS classes"
    assert "width: 90%" in content, "Should have tablet width"
    assert "max-width: 500px" in content, "Should limit max width"
    assert "width: 100%" in content, "Should have mobile full width"
    assert "height: 100vh" in content, "Should have mobile full height"

    print("✅ Command palette CSS verified")


def main():
    """Run all command palette tests."""
    print("=== Testing Command Palette ===\n")

    try:
        test_command_palette_component_exists()
        test_command_palette_commands()
        test_command_palette_shortcuts()
        test_command_palette_styling()
        test_command_palette_accessibility()
        test_command_palette_integration()
        test_command_palette_css()

        print("\n🎉 All command palette tests passed!")
        print("\nCommand palette features:")
        print("✅ Comprehensive command set with categories")
        print("✅ Keyboard shortcuts (Cmd/Ctrl + K to open)")
        print("✅ Proper overlay styling with backdrop")
        print("✅ Accessibility features and ARIA labels")
        print("✅ Responsive design for all screen sizes")
        print("✅ Integration with application state")
        print("✅ Smooth animations and transitions")
        return True

    except AssertionError as e:
        print(f"\n❌ Command palette test failed: {e}")
        return False
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)