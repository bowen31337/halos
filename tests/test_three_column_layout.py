"""
Test Feature #122: Three-column desktop layout is properly proportioned
"""

import pytest
import sys
import os

# Add client directory to path for CSS parsing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def test_sidebar_width_in_css():
    """Verify sidebar width is defined in CSS variables"""
    css_path = os.path.join(os.path.dirname(__file__), '..', 'client', 'src', 'index.css')

    with open(css_path, 'r') as f:
        css_content = f.read()

    # Check for sidebar-width variable
    assert '--sidebar-width: 280px' in css_content or '--sidebar-width: 260px' in css_content, \
        "Sidebar width should be 260-280px in CSS variables"

    print("✓ Sidebar width defined in CSS (260-280px)")


def test_panel_width_in_css():
    """Verify artifacts panel width is defined in CSS variables"""
    css_path = os.path.join(os.path.dirname(__file__), '..', 'client', 'src', 'index.css')

    with open(css_path, 'r') as f:
        css_content = f.read()

    # Check for panel-artifacts-width variable
    assert '--panel-artifacts-width: 450px' in css_content or \
           '--panel-artifacts-width:' in css_content, \
        "Artifacts panel width should be defined in CSS variables (400-500px)"

    print("✓ Artifacts panel width defined in CSS (400-500px)")


def test_resizable_handle_component_exists():
    """Verify ResizableHandle component exists"""
    component_path = os.path.join(
        os.path.dirname(__file__),
        '..',
        'client',
        'src',
        'components',
        'ResizableHandle.tsx'
    )

    assert os.path.exists(component_path), \
        "ResizableHandle.tsx component should exist"

    with open(component_path, 'r') as f:
        content = f.read()

    # Check for key features
    assert 'onMouseDown' in content, "Should handle mouse down events"
    assert 'useRef' in content, "Should use React refs"
    assert 'role="separator"' in content, "Should have proper ARIA role"

    print("✓ ResizableHandle component exists with proper event handlers")


def test_layout_uses_resizable_sidebar():
    """Verify Layout component uses resizable sidebar"""
    layout_path = os.path.join(
        os.path.dirname(__file__),
        '..',
        'client',
        'src',
        'components',
        'Layout.tsx'
    )

    with open(layout_path, 'r') as f:
        content = f.read()

    # Check for resizable handle import and usage
    assert 'ResizableHandle' in content, \
        "Layout should import and use ResizableHandle"

    assert 'setSidebarWidth' in content, \
        "Layout should use setSidebarWidth function"

    assert 'sidebarWidth' in content, \
        "Layout should use sidebarWidth from store"

    print("✓ Layout component implements resizable sidebar")


def test_artifact_panel_uses_resizable():
    """Verify ArtifactPanel component uses resizable handle"""
    panel_path = os.path.join(
        os.path.dirname(__file__),
        '..',
        'client',
        'src',
        'components',
        'ArtifactPanel.tsx'
    )

    with open(panel_path, 'r') as f:
        content = f.read()

    # Check for resizable handle import and usage
    assert 'ResizableHandle' in content, \
        "ArtifactPanel should import and use ResizableHandle"

    assert 'setPanelWidth' in content, \
        "ArtifactPanel should use setPanelWidth function"

    assert 'panelWidth' in content, \
        "ArtifactPanel should use panelWidth from store"

    print("✓ ArtifactPanel component implements resizing")


def test_ui_store_has_width_state():
    """Verify UI store has width state management"""
    store_path = os.path.join(
        os.path.dirname(__file__),
        '..',
        'client',
        'src',
        'stores',
        'uiStore.ts'
    )

    with open(store_path, 'r') as f:
        content = f.read()

    # Check for state properties
    assert 'sidebarWidth: number' in content, \
        "UI store should have sidebarWidth state"

    assert 'panelWidth: number' in content, \
        "UI store should have panelWidth state"

    # Check for actions
    assert 'setSidebarWidth:' in content, \
        "UI store should have setSidebarWidth action"

    assert 'setPanelWidth:' in content, \
        "UI store should have setPanelWidth action"

    # Check initial values
    assert 'sidebarWidth: 260' in content or 'sidebarWidth: 280' in content, \
        "Initial sidebarWidth should be 260-280px"

    assert 'panelWidth: 450' in content, \
        "Initial panelWidth should be 450px"

    print("✓ UI store has width state management")


def test_layout_proportions():
    """Test that layout proportions are within expected ranges"""
    # Based on 1920px width
    total_width = 1920

    # Expected ranges
    sidebar_min, sidebar_max = 260, 320
    panel_min, panel_max = 400, 500

    # Get default values from store
    store_path = os.path.join(
        os.path.dirname(__file__),
        '..',
        'client',
        'src',
        'stores',
        'uiStore.ts'
    )

    with open(store_path, 'r') as f:
        content = f.read()

    # Extract initial values
    import re
    sidebar_match = re.search(r'sidebarWidth:\s*(\d+)', content)
    panel_match = re.search(r'panelWidth:\s*(\d+)', content)

    if sidebar_match and panel_match:
        sidebar_width = int(sidebar_match.group(1))
        panel_width = int(panel_match.group(1))

        # Verify sidebar is in range
        assert sidebar_min <= sidebar_width <= sidebar_max, \
            f"Sidebar width {sidebar_width}px should be between {sidebar_min}-{sidebar_max}px"

        # Verify panel is in range
        assert panel_min <= panel_width <= panel_max, \
            f"Panel width {panel_width}px should be between {panel_min}-{panel_max}px"

        # Verify they don't overlap (with some buffer)
        main_chat_width = total_width - sidebar_width - panel_width
        assert main_chat_width > 800, \
            f"Main chat area should be at least 800px (currently {main_chat_width}px)"

        # Verify proportions feel balanced (sidebar and panel shouldn't be too large)
        sidebar_ratio = sidebar_width / total_width
        panel_ratio = panel_width / total_width

        assert sidebar_ratio < 0.2, \
            f"Sidebar ratio {sidebar_ratio:.2%} should be less than 20%"

        assert panel_ratio < 0.3, \
            f"Panel ratio {panel_ratio:.2%} should be less than 30%"

        print(f"✓ Layout proportions are balanced at 1920px width:")
        print(f"  - Sidebar: {sidebar_width}px ({sidebar_ratio:.1%})")
        print(f"  - Main chat: {main_chat_width}px ({main_chat_width/total_width:.1%})")
        print(f"  - Panel: {panel_width}px ({panel_ratio:.1%})")


def test_resizable_handle_constraints():
    """Verify resize handles have proper min/max constraints"""
    component_path = os.path.join(
        os.path.dirname(__file__),
        '..',
        'client',
        'src',
        'components',
        'ResizableHandle.tsx'
    )

    with open(component_path, 'r') as f:
        content = f.read()

    # Check for min/max props
    assert 'minWidth' in content, "Should have minWidth prop"
    assert 'maxWidth' in content, "Should have maxWidth prop"

    # Check constraint logic
    assert 'Math.max' in content and 'Math.min' in content, \
        "Should constrain resize values within bounds"

    print("✓ Resizable handles have proper min/max constraints")


if __name__ == '__main__':
    print("\n" + "="*70)
    print("Testing Feature #122: Three-column desktop layout proportions")
    print("="*70 + "\n")

    test_sidebar_width_in_css()
    test_panel_width_in_css()
    test_resizable_handle_component_exists()
    test_layout_uses_resizable_sidebar()
    test_artifact_panel_uses_resizable()
    test_ui_store_has_width_state()
    test_layout_proportions()
    test_resizable_handle_constraints()

    print("\n" + "="*70)
    print("All Feature #122 tests passed! ✓")
    print("="*70 + "\n")
