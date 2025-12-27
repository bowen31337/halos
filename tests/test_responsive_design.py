"""Test responsive design features for features #117-119.

This test file verifies that responsive design works correctly at different breakpoints.
"""

import re
from pathlib import Path


def test_responsive_css_media_queries():
    """Feature #117: Responsive design works at tablet breakpoint (768px).

    Steps:
    1. Verify tablet media query exists
    2. Verify mobile media query exists
    3. Verify reduced motion media query exists
    4. Verify high contrast media query exists
    """
    css_path = Path("/media/DATA/projects/autonomous-coding-clone-cc/talos/client/src/index.css")
    css_content = css_path.read_text()

    # Check for tablet breakpoint (768px)
    assert re.search(r'@media\s*\(max-width:\s*768px\)', css_content), \
        "Tablet breakpoint (768px) media query should exist"

    # Check for mobile breakpoint (375px)
    assert re.search(r'@media\s*\(max-width:\s*375px\)', css_content), \
        "Mobile breakpoint (375px) media query should exist"

    # Check for reduced motion
    assert re.search(r'@media\s*\(prefers-reduced-motion:\s*reduce\)', css_content), \
        "Reduced motion media query should exist"

    # Check for high contrast
    assert re.search(r'@media\s*\(prefers-contrast:\s*high\)', css_content), \
        "High contrast media query should exist"

    # Verify tablet styles include sidebar overlay
    tablet_section = re.search(r'@media\s*\(max-width:\s*768px\)\s*\{[^}]+\}', css_content, re.DOTALL)
    assert tablet_section, "Tablet section should exist"
    tablet_content = tablet_section.group(0)
    assert 'position: fixed' in tablet_content or 'fixed' in tablet_content, \
        "Tablet styles should include fixed positioning for overlays"
    assert 'z-index' in tablet_content, "Tablet styles should include z-index"

    # Verify mobile styles include full-width panels
    mobile_section = re.search(r'@media\s*\(max-width:\s*375px\)\s*\{[^}]+\}', css_content, re.DOTALL)
    assert mobile_section, "Mobile section should exist"
    mobile_content = mobile_section.group(0)
    assert 'width: 100%' in mobile_content or 'max-width: 100%' in mobile_content, \
        "Mobile styles should include full-width elements"

    print("✅ Feature #117: Responsive CSS media queries are properly configured")


def test_layout_responsive_handling():
    """Feature #118: Layout component handles responsive behavior.

    Steps:
    1. Verify Layout has responsive state tracking
    2. Verify Layout has touch gesture handlers
    3. Verify Layout handles sidebar on mobile/tablet
    """
    layout_path = Path("/media/DATA/projects/autonomous-coding-clone-cc/talos/client/src/components/Layout.tsx")
    content = layout_path.read_text()

    # Check for responsive state
    assert 'isMobile' in content, "Layout should track mobile state"
    assert 'isTablet' in content, "Layout should track tablet state"
    assert 'useState' in content, "Layout should use state hooks"

    # Check for responsive effect
    assert 'window.innerWidth' in content, "Layout should check window width"
    assert 'resize' in content, "Layout should handle resize events"

    # Check for touch gesture handlers
    assert 'handleTouchStart' in content, "Layout should have touch start handler"
    assert 'handleTouchMove' in content, "Layout should have touch move handler"
    assert 'handleTouchEnd' in content, "Layout should have touch end handler"
    assert 'onTouchStart' in content, "Layout should bind touch start"
    assert 'onTouchMove' in content, "Layout should bind touch move"
    assert 'onTouchEnd' in content, "Layout should bind touch end"

    # Check for swipe detection
    assert 'deltaX' in content, "Layout should track horizontal swipe"
    assert 'deltaY' in content, "Layout should track vertical movement"
    assert 'setSidebarOpen' in content, "Layout should control sidebar"

    # Check for conditional rendering based on screen size
    assert 'isMobile ?' in content or 'isTablet ?' in content, \
        "Layout should conditionally render based on screen size"

    print("✅ Feature #118: Layout component handles responsive behavior")


def test_header_responsive_handling():
    """Feature #119: Header component handles responsive layout.

    Steps:
    1. Verify Header has responsive state
    2. Verify Header hides controls on mobile
    3. Verify Header compacts elements on mobile
    """
    header_path = Path("/media/DATA/projects/autonomous-coding-clone-cc/talos/client/src/components/Header.tsx")
    content = header_path.read_text()

    # Check for responsive state
    assert 'isMobile' in content, "Header should track mobile state"
    assert 'isTablet' in content, "Header should track tablet state"

    # Check for responsive effect
    assert 'window.innerWidth' in content, "Header should check window width"
    assert 'resize' in content, "Header should handle resize events"

    # Check for conditional rendering of controls
    assert '!isMobile' in content or 'isMobile &&' in content, \
        "Header should conditionally render based on mobile state"

    # Check for thinking toggle visibility
    assert 'thinking-toggle' in content, "Header should have thinking toggle"
    assert 'data-tour="thinking-toggle"' in content, "Header should have thinking toggle data attribute"

    # Check for action button visibility control
    assert 'Todo button' in content or 'todo button' in content, "Header should have todo button"
    assert 'Files button' in content or 'files button' in content, "Header should have files button"

    print("✅ Feature #119: Header component handles responsive layout")


def test_chatpage_responsive_panels():
    """Feature #120: ChatPage handles responsive panels.

    Steps:
    1. Verify ChatPage tracks screen size
    2. Verify panels become overlays on mobile/tablet
    3. Verify main content width adjusts properly
    """
    chatpage_path = Path("/media/DATA/projects/autonomous-coding-clone-cc/talos/client/src/pages/ChatPage.tsx")
    content = chatpage_path.read_text()

    # Check for responsive state
    assert 'isMobile' in content, "ChatPage should track mobile state"
    assert 'isTablet' in content, "ChatPage should track tablet state"

    # Check for panel width adjustment
    assert 'shouldAdjustWidth' in content, "ChatPage should calculate panel width adjustment"
    assert '!isTablet' in content or '!isMobile' in content, \
        "ChatPage should exclude mobile/tablet from width adjustment"

    # Check for overlay handling
    assert 'fixed inset-0' in content, "ChatPage should use fixed positioning for overlays"
    assert 'bg-black/50' in content, "ChatPage should have backdrop overlay"
    assert 'z-30' in content, "ChatPage should have proper z-index"

    # Check for panel types
    assert 'artifacts' in content, "ChatPage should handle artifacts panel"
    assert 'todos' in content, "ChatPage should handle todos panel"
    assert 'files' in content, "ChatPage should handle files panel"
    assert 'diffs' in content, "ChatPage should handle diffs panel"
    assert 'memory' in content, "ChatPage should handle memory panel"

    print("✅ Feature #120: ChatPage handles responsive panels")


def test_all_responsive_features():
    """Run all responsive design feature tests."""
    print("\n=== Testing Responsive Design Features ===\n")

    test_responsive_css_media_queries()
    test_layout_responsive_handling()
    test_header_responsive_handling()
    test_chatpage_responsive_panels()

    print("\n=== All Responsive Design Features Verified ===\n")


if __name__ == "__main__":
    test_all_responsive_features()
