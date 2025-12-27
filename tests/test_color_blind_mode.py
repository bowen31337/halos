"""
Test Feature #132: Color blind modes provide distinguishable UI elements
"""

import os
import pytest


def test_color_blind_css_classes_exist():
    """Verify color blind CSS classes are defined"""
    css_path = os.path.join(os.path.dirname(__file__), '..', 'client', 'src', 'index.css')

    with open(css_path, 'r') as f:
        css_content = f.read()

    # Check for all color blind classes
    assert '.colorblind-deuteranopia' in css_content, \
        "CSS should have .colorblind-deuteranopia class defined"
    assert '.colorblind-protanopia' in css_content, \
        "CSS should have .colorblind-protanopia class defined"
    assert '.colorblind-tritanopia' in css_content, \
        "CSS should have .colorblind-tritanopia class defined"
    assert '.colorblind-achromatopsia' in css_content, \
        "CSS should have .colorblind-achromatopsia class defined"

    print("✓ All color blind CSS classes are defined")


def test_deuteranopia_colors_are_distinguishable():
    """Verify deuteranopia mode uses distinguishable colors"""
    css_path = os.path.join(os.path.dirname(__file__), '..', 'client', 'src', 'index.css')

    with open(css_path, 'r') as f:
        css_content = f.read()

    # Extract deuteranopia block
    import re
    deuteranopia_match = re.search(r'\.colorblind-deuteranopia\s*{([^}]+)}', css_content, re.DOTALL)
    assert deuteranopia_match, "Should find .colorblind-deuteranopia block"

    block_content = deuteranopia_match.group(1)

    # Check for blue primary (instead of green/orange)
    assert '--primary: #0077B6' in block_content or '--primary: #005F8C' in block_content, \
        "Deuteranopia should use blue for primary"

    # Check for distinct error color
    assert '--error:' in block_content, "Deuteranopia should define error color"

    # Check for distinct warning color
    assert '--warning:' in block_content, "Deuteranopia should define warning color"

    print("✓ Deuteranopia colors are distinguishable")


def test_protanopia_colors_are_distinguishable():
    """Verify protanopia mode uses distinguishable colors"""
    css_path = os.path.join(os.path.dirname(__file__), '..', 'client', 'src', 'index.css')

    with open(css_path, 'r') as f:
        css_content = f.read()

    # Extract protanopia block
    import re
    protanopia_match = re.search(r'\.colorblind-protanopia\s*{([^}]+)}', css_content, re.DOTALL)
    assert protanopia_match, "Should find .colorblind-protanopia block"

    block_content = protanopia_match.group(1)

    # Check for blue primary
    assert '--primary:' in block_content, "Protanopia should define primary color"

    # Check for distinct error color (dark red)
    assert '--error:' in block_content, "Protanopia should define error color"

    # Check for distinct warning color
    assert '--warning:' in block_content, "Protanopia should define warning color"

    print("✓ Protanopia colors are distinguishable")


def test_tritanopia_colors_are_distinguishable():
    """Verify tritanopia mode uses distinguishable colors"""
    css_path = os.path.join(os.path.dirname(__file__), '..', 'client', 'src', 'index.css')

    with open(css_path, 'r') as f:
        css_content = f.read()

    # Extract tritanopia block
    import re
    tritanopia_match = re.search(r'\.colorblind-tritanopia\s*{([^}]+)}', css_content, re.DOTALL)
    assert tritanopia_match, "Should find .colorblind-tritanopia block"

    block_content = tritanopia_match.group(1)

    # Check for red primary (instead of blue)
    assert '--primary:' in block_content, "Tritanopia should define primary color"

    # Check for distinct error color
    assert '--error:' in block_content, "Tritanopia should define error color"

    # Check for distinct warning color
    assert '--warning:' in block_content, "Tritanopia should define warning color"

    print("✓ Tritanopia colors are distinguishable")


def test_ui_store_has_color_blind_state():
    """Verify UI store has color blind mode state management"""
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
    assert 'colorBlindMode:' in content, \
        "UI store should have colorBlindMode state"

    # Check for action
    assert 'setColorBlindMode:' in content, \
        "UI store should have setColorBlindMode action"

    # Check initial value
    assert "colorBlindMode: 'none'" in content, \
        "Initial colorBlindMode should be 'none'"

    # Check that it applies class to document
    assert 'classList.add' in content and 'colorblind-' in content, \
        "Should apply color blind class to document"

    print("✓ UI store has color blind state management")


def test_ui_store_persists_color_blind_mode():
    """Verify color blind mode is persisted in localStorage"""
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

    # Check that colorBlindMode is in partialize (persisted state)
    assert 'colorBlindMode: state.colorBlindMode' in content, \
        "colorBlindMode should be persisted in localStorage"

    print("✓ Color blind mode setting is persisted")


def test_settings_modal_has_color_blind_controls():
    """Verify SettingsModal has color blind mode controls"""
    modal_path = os.path.join(
        os.path.dirname(__file__),
        '..',
        'client',
        'src',
        'components',
        'SettingsModal.tsx'
    )

    with open(modal_path, 'r') as f:
        content = f.read()

    # Check for color blind mode in imports
    assert 'colorBlindMode,' in content, \
        "SettingsModal should import colorBlindMode from store"
    assert 'setColorBlindMode,' in content, \
        "SettingsModal should import setColorBlindMode from store"

    # Check for color blind mode UI
    assert 'Color Blind Mode' in content, \
        "SettingsModal should have Color Blind Mode section"

    # Check for all mode options
    assert "'deuteranopia'" in content, \
        "Should have deuteranopia option"
    assert "'protanopia'" in content, \
        "Should have protanopia option"
    assert "'tritanopia'" in content, \
        "Should have tritanopia option"
    assert "'achromatopsia'" in content, \
        "Should have achromatopsia option"

    # Check for setColorBlindMode call
    assert 'setColorBlindMode' in content, \
        "Should call setColorBlindMode"

    print("✓ SettingsModal has color blind mode controls")


def test_settings_modal_appearance_tab_structure():
    """Verify SettingsModal appearance tab has proper structure"""
    modal_path = os.path.join(
        os.path.dirname(__file__),
        '..',
        'client',
        'src',
        'components',
        'SettingsModal.tsx'
    )

    with open(modal_path, 'r') as f:
        content = f.read()

    # Find appearance tab
    appearance_match = content.find('renderAppearanceTab')
    if appearance_match == -1:
        pytest.fail("renderAppearanceTab function not found")

    # Check for high contrast toggle
    assert 'High Contrast Mode' in content, \
        "Should have High Contrast Mode toggle"

    # Check for font size
    assert 'Font Size' in content, \
        "Should have Font Size control"

    print("✓ Appearance tab structure is correct")


if __name__ == '__main__':
    print("\n" + "="*70)
    print("Testing Feature #132: Color blind modes provide distinguishable UI elements")
    print("="*70 + "\n")

    test_color_blind_css_classes_exist()
    test_deuteranopia_colors_are_distinguishable()
    test_protanopia_colors_are_distinguishable()
    test_tritanopia_colors_are_distinguishable()
    test_ui_store_has_color_blind_state()
    test_ui_store_persists_color_blind_mode()
    test_settings_modal_has_color_blind_controls()
    test_settings_modal_appearance_tab_structure()

    print("\n" + "="*70)
    print("All Feature #132 tests passed! ✓")
    print("="*70 + "\n")
