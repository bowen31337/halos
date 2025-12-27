"""
Font Size Feature Test Suite (Feature #31)

Tests:
1. UI Store has fontSize state
2. Font size persists to localStorage
3. setFontSize action updates CSS variable
4. SettingsModal slider connects to store
5. Font size applies to body element
"""

import pytest
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestFontSizeStore:
    """Test font size state management in uiStore"""

    def test_ui_store_has_font_size_state(self):
        """Verify uiStore has fontSize state"""
        import json

        store_path = 'client/src/stores/uiStore.ts'
        # If we're in the talos directory, try without client prefix
        if not os.path.exists(store_path):
            store_path = 'src/stores/uiStore.ts'

        with open(store_path, 'r') as f:
            content = f.read()

        # Check for fontSize property in interface
        assert 'fontSize: number' in content, "UIState interface should have fontSize property"
        print("   ✓ UIStore has fontSize state")

    def test_ui_store_has_set_font_size_action(self):
        """Verify uiStore has setFontSize action"""
        store_path = 'client/src/stores/uiStore.ts'
        if not os.path.exists(store_path):
            store_path = 'src/stores/uiStore.ts'

        with open(store_path, 'r') as f:
            content = f.read()

        # Check for setFontSize action
        assert 'setFontSize' in content, "UIStore should have setFontSize action"
        assert 'setFontSize: (size: number) => void' in content, "setFontSize should accept number parameter"
        print("   ✓ UIStore has setFontSize action")

    def test_font_size_persists_to_localstorage(self):
        """Verify fontSize is persisted in localStorage"""
        store_path = 'client/src/stores/uiStore.ts'
        if not os.path.exists(store_path):
            store_path = 'src/stores/uiStore.ts'

        with open(store_path, 'r') as f:
            content = f.read()

        # Check that fontSize is in partialize (persisted fields)
        assert 'fontSize: state.fontSize' in content, "fontSize should be persisted to localStorage"
        print("   ✓ fontSize persists to localStorage")

    def test_set_font_size_updates_css_variable(self):
        """Verify setFontSize updates CSS variable"""
        store_path = 'client/src/stores/uiStore.ts'
        if not os.path.exists(store_path):
            store_path = 'src/stores/uiStore.ts'

        with open(store_path, 'r') as f:
            content = f.read()

        # Check that setFontSize updates CSS variable
        assert "document.documentElement.style.setProperty('--base-font-size'" in content, \
            "setFontSize should update --base-font-size CSS variable"
        assert '`${size}px`' in content, "setFontSize should set size in pixels"
        print("   ✓ setFontSize updates --base-font-size CSS variable")

    def test_font_size_initial_value(self):
        """Verify fontSize has initial value of 16"""
        store_path = 'client/src/stores/uiStore.ts'
        if not os.path.exists(store_path):
            store_path = 'src/stores/uiStore.ts'

        with open(store_path, 'r') as f:
            content = f.read()

        # Check for initial value
        assert 'fontSize: 16' in content, "fontSize should default to 16"
        print("   ✓ fontSize has correct initial value (16px)")


class TestFontSizeCSS:
    """Test CSS font size implementation"""

    def test_css_variable_exists(self):
        """Verify --base-font-size CSS variable exists"""
        css_path = 'client/src/index.css'
        if not os.path.exists(css_path):
            css_path = 'src/index.css'

        with open(css_path, 'r') as f:
            content = f.read()

        assert '--base-font-size:' in content, "index.css should define --base-font-size variable"
        assert '--base-font-size: 16px' in content, "--base-font-size should default to 16px"
        print("   ✓ --base-font-size CSS variable exists")

    def test_body_uses_font_size_variable(self):
        """Verify body element uses --base-font-size"""
        css_path = 'client/src/index.css'
        if not os.path.exists(css_path):
            css_path = 'src/index.css'

        with open(css_path, 'r') as f:
            content = f.read()

        # Find body rule
        body_section = content[content.find('body {'):content.find('}', content.find('body {'))]
        assert 'font-size: var(--base-font-size)' in body_section, \
            "body should use font-size: var(--base-font-size)"
        print("   ✓ body uses --base-font-size CSS variable")


class TestSettingsModalIntegration:
    """Test SettingsModal font size slider integration"""

    def test_settings_modal_imports_font_size(self):
        """Verify SettingsModal imports fontSize from store"""
        modal_path = 'client/src/components/SettingsModal.tsx'
        if not os.path.exists(modal_path):
            modal_path = 'src/components/SettingsModal.tsx'

        with open(modal_path, 'r') as f:
            content = f.read()

        assert 'fontSize' in content, "SettingsModal should use fontSize from store"
        assert 'setFontSize' in content, "SettingsModal should use setFontSize from store"
        print("   ✓ SettingsModal imports fontSize and setFontSize")

    def test_font_slider_connected_to_store(self):
        """Verify font slider is connected to store"""
        modal_path = 'client/src/components/SettingsModal.tsx'
        if not os.path.exists(modal_path):
            modal_path = 'src/components/SettingsModal.tsx'

        with open(modal_path, 'r') as f:
            content = f.read()

        # Check slider uses fontSize value
        assert 'value={fontSize}' in content, "Slider should use fontSize from store"
        # Check slider calls setFontSize
        assert 'setFontSize(' in content, "Slider onChange should call setFontSize"
        print("   ✓ Font slider connected to store")

    def test_font_slider_range(self):
        """Verify font slider has correct range"""
        modal_path = 'client/src/components/SettingsModal.tsx'
        if not os.path.exists(modal_path):
            modal_path = 'src/components/SettingsModal.tsx'

        with open(modal_path, 'r') as f:
            content = f.read()

        # Find font size slider section
        font_section = content[content.find('Font Size'):content.find('</div>', content.find('Font Size'))]

        assert 'min="12"' in font_section, "Slider should have min value of 12"
        assert 'max="20"' in font_section, "Slider should have max value of 20"
        print("   ✓ Font slider has correct range (12-20px)")

    def test_font_size_display(self):
        """Verify current font size is displayed"""
        modal_path = 'client/src/components/SettingsModal.tsx'
        if not os.path.exists(modal_path):
            modal_path = 'src/components/SettingsModal.tsx'

        with open(modal_path, 'r') as f:
            content = f.read()

        # Check for px display
        assert '{fontSize}px' in content, "Current font size should be displayed with 'px' unit"
        print("   ✓ Current font size value is displayed")


class TestAppInitialization:
    """Test app initialization of font size"""

    def test_app_initializes_font_size(self):
        """Verify App.tsx initializes font size on mount"""
        app_path = 'client/src/App.tsx'
        if not os.path.exists(app_path):
            app_path = 'src/App.tsx'

        with open(app_path, 'r') as f:
            content = f.read()

        assert 'fontSize' in content, "App should use fontSize from store"
        assert 'setFontSize' in content, "App should use setFontSize from store"
        print("   ✓ App.tsx imports fontSize state and actions")

    def test_app_has_font_size_effect(self):
        """Verify App has useEffect to initialize font size"""
        app_path = 'client/src/App.tsx'
        if not os.path.exists(app_path):
            app_path = 'src/App.tsx'

        with open(app_path, 'r') as f:
            content = f.read()

        # Check for useEffect with fontSize
        assert 'useEffect' in content, "App should use useEffect"
        assert 'setFontSize(fontSize)' in content, "App should call setFontSize on mount"
        print("   ✓ App initializes font size on mount")


def run_tests():
    """Run all font size feature tests"""
    print("\n" + "="*60)
    print("FONT SIZE FEATURE TEST SUITE (Feature #31)")
    print("="*60 + "\n")

    tests = [
        ("UI Store Tests", TestFontSizeStore),
        ("CSS Implementation Tests", TestFontSizeCSS),
        ("SettingsModal Integration Tests", TestSettingsModalIntegration),
        ("App Initialization Tests", TestAppInitialization),
    ]

    failed = 0
    passed = 0

    for suite_name, test_class in tests:
        print(f"\n{suite_name}:")
        print("-" * 40)

        test_methods = [m for m in dir(test_class) if m.startswith('test_')]

        for method_name in test_methods:
            try:
                method = getattr(test_class(), method_name)
                method()
                passed += 1
            except AssertionError as e:
                print(f"   ✗ {method_name}: {str(e)}")
                failed += 1
            except Exception as e:
                print(f"   ✗ {method_name}: Unexpected error - {str(e)}")
                failed += 1

    print("\n" + "="*60)
    print(f"TEST RESULTS: {passed} passed, {failed} failed")
    print("="*60 + "\n")

    if failed == 0:
        print("🎉 ALL TESTS PASSED - Font size feature is working!")
        return 0
    else:
        print(f"⚠️  {failed} test(s) failed")
        return 1


if __name__ == '__main__':
    sys.exit(run_tests())
