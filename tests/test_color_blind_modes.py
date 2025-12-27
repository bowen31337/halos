"""Test Color Blind Modes Feature"""
import re


def test_css_has_deuteranopia_mode():
    with open('client/src/index.css', 'r') as f:
        css = f.read()
    assert '.colorblind-deuteranopia' in css


def test_css_has_protanopia_mode():
    with open('client/src/index.css', 'r') as f:
        css = f.read()
    assert '.colorblind-protanopia' in css


def test_css_has_tritanopia_mode():
    with open('client/src/index.css', 'r') as f:
        css = f.read()
    assert '.colorblind-tritanopia' in css


def test_css_has_achromatopsia_mode():
    with open('client/src/index.css', 'r') as f:
        css = f.read()
    assert '.colorblind-achromatopsia' in css


def test_ui_store_has_all_modes():
    with open('client/src/stores/uiStore.ts', 'r') as f:
        store = f.read()
    assert "'achromatopsia'" in store or '"achromatopsia"' in store
    assert "colorblind-achromatopsia" in store


def test_color_blind_mode_in_settings():
    with open('client/src/components/SettingsModal.tsx', 'r') as f:
        modal = f.read()
    assert 'colorBlindMode' in modal
    assert 'setColorBlindMode' in modal


if __name__ == '__main__':
    print("Testing Color Blind Modes (Feature #132)")
    test_css_has_deuteranopia_mode()
    test_css_has_protanopia_mode()
    test_css_has_tritanopia_mode()
    test_css_has_achromatopsia_mode()
    test_ui_store_has_all_modes()
    test_color_blind_mode_in_settings()
    print("✅ All tests passed!")
