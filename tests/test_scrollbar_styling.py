#!/usr/bin/env python3
"""
Test suite for scrollbar styling that matches the application theme.
"""

import os
from pathlib import Path


def test_scrollbar_webkit_styling():
    """Test that WebKit scrollbar styling is properly implemented."""
    css_path = Path("client/src/index.css")
    assert css_path.exists(), "Main CSS file should exist"

    content = css_path.read_text()

    # Check WebKit scrollbar selectors
    assert "::-webkit-scrollbar" in content, "Should have WebKit scrollbar selector"
    assert "::-webkit-scrollbar-track" in content, "Should have WebKit scrollbar track"
    assert "::-webkit-scrollbar-thumb" in content, "Should have WebKit scrollbar thumb"
    assert "::-webkit-scrollbar-thumb:hover" in content, "Should have hover state"

    # Check scrollbar dimensions
    assert "width: 10px" in content, "Should have 10px width"
    assert "height: 10px" in content, "Should have 10px height"
    assert "border-radius: 6px" in content, "Should have rounded corners"

    # Check theme integration
    assert "background: var(--border)" in content, "Should use border variable"
    assert "background: var(--text-secondary)" in content, "Should use text-secondary for hover"
    assert "cursor: pointer" in content, "Should have pointer cursor on hover"

    print("✅ WebKit scrollbar styling verified")


def test_firefox_scrollbar_styling():
    """Test that Firefox scrollbar styling is properly implemented."""
    css_path = Path("client/src/index.css")
    content = css_path.read_text()

    # Check Firefox scrollbar properties
    assert "scrollbar-width: thin" in content, "Should have thin scrollbar width"
    assert "scrollbar-color: var(--border) transparent" in content, "Should use theme colors"
    assert "* {" in content, "Should apply to all elements"

    print("✅ Firefox scrollbar styling verified")


def test_specific_area_scrollbar_styling():
    """Test that specific areas have proper scrollbar styling."""
    css_path = Path("client/src/index.css")
    content = css_path.read_text()

    # Check message list scrollbar
    assert ".message-list" in content, "Should have message list styling"
    assert ".message-list::-webkit-scrollbar" in content, "Should have message list scrollbar"
    assert ".message-list::-webkit-scrollbar-thumb" in content, "Should style message list thumb"

    # Check panel content scrollbar
    assert ".panel-content" in content, "Should have panel content styling"
    assert ".panel-content::-webkit-scrollbar" in content, "Should have panel scrollbar"
    assert ".panel-content::-webkit-scrollbar-thumb" in content, "Should style panel thumb"

    print("✅ Specific area scrollbar styling verified")


def test_scrollbar_theme_integration():
    """Test that scrollbar styling integrates with theme system."""
    css_path = Path("client/src/index.css")
    content = css_path.read_text()

    # Check that scrollbars use CSS variables
    assert "var(--border)" in content, "Should use border color variable"
    assert "var(--text-secondary)" in content, "Should use secondary text color"
    assert "var(--text-primary)" in content, "Should use primary text color"

    print("✅ Scrollbar theme integration verified")


def test_scrollbar_states():
    """Test that scrollbar states are properly styled."""
    css_path = Path("client/src/index.css")
    content = css_path.read_text()

    # Check scrollbar states
    assert "::-webkit-scrollbar-thumb:hover" in content, "Should have hover state"
    assert "::-webkit-scrollbar-thumb:active" in content, "Should have active state"
    assert "cursor: pointer" in content, "Should have pointer cursor"
    assert "background-clip: padding-box" in content, "Should have proper background clipping"

    print("✅ Scrollbar states verified")


def test_scrollbar_dimensions():
    """Test that scrollbar dimensions are appropriate."""
    css_path = Path("client/src/index.css")
    content = css_path.read_text()

    # Check dimensions
    assert "width: 10px" in content, "Main scrollbar should be 10px wide"
    assert "height: 10px" in content, "Main scrollbar should be 10px tall"
    assert "width: 8px" in content, "Specific areas should be 8px wide"

    print("✅ Scrollbar dimensions verified")


def main():
    """Run all scrollbar styling tests."""
    print("=== Testing Scrollbar Styling ===\n")

    try:
        test_scrollbar_webkit_styling()
        test_firefox_scrollbar_styling()
        test_specific_area_scrollbar_styling()
        test_scrollbar_theme_integration()
        test_scrollbar_states()
        test_scrollbar_dimensions()

        print("\n🎉 All scrollbar styling tests passed!")
        print("\nScrollbar styling features:")
        print("✅ WebKit scrollbar styling (Chrome, Safari, Edge)")
        print("✅ Firefox scrollbar styling")
        print("✅ Theme integration with CSS variables")
        print("✅ Proper hover and active states")
        print("✅ Dimensions optimized for UX")
        print("✅ Specific styling for message lists and panels")
        return True

    except AssertionError as e:
        print(f"\n❌ Scrollbar styling test failed: {e}")
        return False
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)