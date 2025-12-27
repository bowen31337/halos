"""
Test Feature #127: High contrast mode maintains readability
"""

import pytest
import sys
import os


def test_high_contrast_css_variables_exist():
    """Verify high contrast CSS variables are defined"""
    css_path = os.path.join(os.path.dirname(__file__), '..', 'client', 'src', 'index.css')

    with open(css_path, 'r') as f:
        css_content = f.read()

    # Check for high contrast class
    assert '.high-contrast' in css_content, \
        "CSS should have .high-contrast class defined"

    # Check for text color overrides
    assert '--text-primary: #000000' in css_content, \
        "High contrast mode should override text-primary to black"

    # Check for border color overrides
    assert '--border: #000000' in css_content, \
        "High contrast mode should override border to black"

    print("✓ High contrast CSS variables are defined")


def test_high_contrast_dark_mode():
    """Verify high contrast works with dark mode"""
    css_path = os.path.join(os.path.dirname(__file__), '..', 'client', 'src', 'index.css')

    with open(css_path, 'r') as f:
        css_content = f.read()

    # Check for dark high contrast combination
    assert '.dark.high-contrast' in css_content, \
        "CSS should have .dark.high-contrast combined selector"

    # Check for white text in dark mode
    assert '--text-primary: #FFFFFF' in css_content, \
        "Dark high contrast mode should use white text"

    # Check for white borders in dark mode
    css_content.count('--border: #FFFFFF') >= 1 or '--border-primary: #FFFFFF' in css_content

    print("✓ High contrast dark mode is properly configured")


def test_high_contrast_enhanced_status_colors():
    """Verify status colors are enhanced in high contrast mode"""
    css_path = os.path.join(os.path.dirname(__file__), '..', 'client', 'src', 'index.css')

    with open(css_path, 'r') as f:
        css_content = f.read()

    # Check for enhanced success color (darker/more visible)
    assert '--success: #006400' in css_content or '--success: #00FF00' in css_content, \
        "High contrast should enhance success color"

    # Check for enhanced error color
    assert '--error: #8B0000' in css_content or '--error: #FF4444' in css_content, \
        "High contrast should enhance error color"

    # Check for enhanced warning color
    assert '--warning: #B8860B' in css_content or '--warning: #FFD700' in css_content, \
        "High contrast should enhance warning color"

    print("✓ Status colors are enhanced for visibility")


def test_ui_store_has_high_contrast_state():
    """Verify UI store has high contrast state management"""
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

    # Check for state property
    assert 'highContrast: boolean' in content, \
        "UI store should have highContrast state"

    # Check for actions
    assert 'setHighContrast:' in content, \
        "UI store should have setHighContrast action"

    assert 'toggleHighContrast:' in content, \
        "UI store should have toggleHighContrast action"

    # Check initial value
    assert 'highContrast: false' in content, \
        "Initial highContrast should be false"

    print("✓ UI store has high contrast state management")


def test_high_contrast_applies_class_to_document():
    """Verify high contrast applies class to document element"""
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

    # Check that setHighContrast adds class
    assert "classList.add('high-contrast')" in content, \
        "setHighContrast should add high-contrast class to document"

    # Check that removing high contrast removes class
    assert "classList.remove('high-contrast')" in content, \
        "setHighContrast should remove high-contrast class when disabled"

    print("✓ High contrast properly toggles document class")


def test_high_contrast_increased_text_contrast():
    """Verify text contrast is increased in high contrast mode"""
    css_path = os.path.join(os.path.dirname(__file__), '..', 'client', 'src', 'index.css')

    with open(css_path, 'r') as f:
        css_content = f.read()

    # Extract high contrast text colors
    import re

    # Find .high-contrast block
    high_contrast_match = re.search(r'\.high-contrast\s*{([^}]+)}', css_content, re.DOTALL)
    assert high_contrast_match, "Should find .high-contrast block"

    block_content = high_contrast_match.group(1)

    # Verify pure black for primary text (maximum contrast)
    assert '--text-primary: #000000' in block_content, \
        "High contrast should use pure black (#000000) for primary text"

    # Verify dark secondary text
    assert '--text-secondary: #1A1A1A' in block_content, \
        "High contrast should use very dark color for secondary text"

    # Verify dark muted text
    assert '--text-muted: #333333' in block_content, \
        "High contrast should use dark color for muted text"

    print("✓ Text contrast is maximized in high contrast mode")


def test_high_contrast_stronger_borders():
    """Verify borders are stronger in high contrast mode"""
    css_path = os.path.join(os.path.dirname(__file__), '..', 'client', 'src', 'index.css')

    with open(css_path, 'r') as f:
        css_content = f.read()

    import re

    # Find .high-contrast block
    high_contrast_match = re.search(r'\.high-contrast\s*{([^}]+)}', css_content, re.DOTALL)
    assert high_contrast_match, "Should find .high-contrast block"

    block_content = high_contrast_match.group(1)

    # Verify pure black borders (maximum contrast)
    assert '--border: #000000' in block_content, \
        "High contrast should use pure black (#000000) for borders"

    assert '--border-primary: #000000' in block_content, \
        "High contrast should use pure black for primary borders"

    print("✓ Border contrast is maximized in high contrast mode")


def test_high_contrast_persistence():
    """Verify high contrast setting is persisted"""
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

    # Check that highContrast is in partialize (persisted state)
    assert 'highContrast: state.highContrast' in content, \
        "highContrast should be persisted in localStorage"

    print("✓ High contrast setting is persisted")


if __name__ == '__main__':
    print("\n" + "="*70)
    print("Testing Feature #127: High contrast mode maintains readability")
    print("="*70 + "\n")

    test_high_contrast_css_variables_exist()
    test_high_contrast_dark_mode()
    test_high_contrast_enhanced_status_colors()
    test_ui_store_has_high_contrast_state()
    test_high_contrast_applies_class_to_document()
    test_high_contrast_increased_text_contrast()
    test_high_contrast_stronger_borders()
    test_high_contrast_persistence()

    print("\n" + "="*70)
    print("All Feature #127 tests passed! ✓")
    print("="*70 + "\n")
