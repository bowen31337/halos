#!/usr/bin/env python3
"""
Test suite for keyboard navigation focus states.
"""

import os
from pathlib import Path


def test_focus_css_variables():
    """Test that focus states use proper CSS variables."""
    css_path = Path("client/src/index.css")
    assert css_path.exists(), "Main CSS file should exist"

    content = css_path.read_text()

    # Check that focus states use CSS variables
    assert "var(--primary)" in content, "Should use primary color variable"
    assert "var(--error)" in content, "Should use error color for destructive actions"
    assert "outline: 3px solid" in content, "Should have strong focus indicators"
    assert "outline-offset: 2px" in content, "Should have proper offset"

    print("✅ Focus CSS variables verified")


def test_focus_visible_polyfill():
    """Test that focus-visible polyfill is included."""
    html_path = Path("client/index.html")
    assert html_path.exists(), "HTML file should exist"

    content = html_path.read_text()

    # Check for focus-visible polyfill
    assert "focus-visible.min.js" in content, "Should include focus-visible polyfill"
    assert "unpkg.com" in content, "Should load from CDN"

    print("✅ Focus-visible polyfill verified")


def test_keyboard_only_focus():
    """Test that keyboard-only focus indicators are implemented."""
    css_path = Path("client/src/index.css")
    content = css_path.read_text()

    # Check for keyboard-only focus behavior
    assert ".js-focus-visible" in content, "Should have js-focus-visible class"
    assert "*:focus:not(.focus-visible)" in content, "Should hide mouse focus"
    assert "*:focus-visible" in content, "Should show keyboard focus"

    print("✅ Keyboard-only focus indicators verified")


def test_focus_states_for_interactive_elements():
    """Test that focus states are defined for all interactive elements."""
    css_path = Path("client/src/index.css")
    content = css_path.read_text()

    # Check that focus states are defined for all interactive elements
    assert "button:focus-visible" in content, "Should have button focus"
    assert "input:focus-visible" in content, "Should have input focus"
    assert "textarea:focus-visible" in content, "Should have textarea focus"
    assert "select:focus-visible" in content, "Should have select focus"
    assert "a:focus-visible" in content, "Should have link focus"

    print("✅ Interactive element focus states verified")


def test_focus_states_for_navigation():
    """Test that navigation-specific focus states are defined."""
    css_path = Path("client/src/index.css")
    content = css_path.read_text()

    # Check navigation-specific focus states
    assert ".nav-item:focus-visible" in content, "Should have nav item focus"
    assert ".conversation-item:focus-visible" in content, "Should have conversation focus"
    assert ".message-bubble:focus-visible" in content, "Should have message bubble focus"

    print("✅ Navigation focus states verified")


def test_focus_states_for_modals():
    """Test that modal-specific focus states are defined."""
    css_path = Path("client/src/index.css")
    content = css_path.read_text()

    # Check modal-specific focus states
    assert ".modal-close:focus-visible" in content, "Should have modal close focus"
    assert "var(--error)" in content, "Should use error color for close buttons"

    print("✅ Modal focus states verified")


def test_high_contrast_focus():
    """Test that high contrast focus states are implemented."""
    css_path = Path("client/src/index.css")
    content = css_path.read_text()

    # Check high contrast support
    assert "@media (prefers-contrast: high)" in content, "Should have high contrast media query"
    assert "outline-width: 4px" in content, "Should have thicker outline in high contrast"
    assert "outline-offset: 3px" in content, "Should have larger offset in high contrast"

    print("✅ High contrast focus states verified")


def test_skip_navigation_focus():
    """Test that skip navigation link has proper focus."""
    css_path = Path("client/src/index.css")
    content = css_path.read_text()

    # Check skip navigation focus
    assert ".skip-nav:focus-visible" in content, "Should have skip nav focus"
    assert "z-index: 9999" in content, "Should have high z-index"
    assert "position: fixed" in content, "Should be fixed position"

    print("✅ Skip navigation focus verified")


def test_focus_transition_animations():
    """Test that focus transitions are smooth."""
    css_path = Path("client/src/index.css")
    content = css_path.read_text()

    # Check transition animations
    assert "transition: outline-color 0.2s ease" in content, "Should have outline transition"
    assert "transition: all 0.2s ease" in content, "Should have all property transition"
    assert "box-shadow 0.2s ease" in content, "Should have shadow transition"

    print("✅ Focus transition animations verified")


def main():
    """Run all focus state tests."""
    print("=== Testing Keyboard Navigation Focus States ===\n")

    try:
        test_focus_css_variables()
        test_focus_visible_polyfill()
        test_keyboard_only_focus()
        test_focus_states_for_interactive_elements()
        test_focus_states_for_navigation()
        test_focus_states_for_modals()
        test_high_contrast_focus()
        test_skip_navigation_focus()
        test_focus_transition_animations()

        print("\n🎉 All focus state tests passed!")
        print("\nFocus state features:")
        print("✅ Comprehensive focus indicators with 3px outline")
        print("✅ Keyboard-only focus behavior (hides for mouse users)")
        print("✅ Focus-visible polyfill for better browser support")
        print("✅ High contrast mode support")
        print("✅ Smooth transition animations")
        print("✅ Specialized focus states for different UI elements")
        print("✅ Skip navigation link with proper focus")
        print("✅ Error color for destructive actions")
        return True

    except AssertionError as e:
        print(f"\n❌ Focus state test failed: {e}")
        return False
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)