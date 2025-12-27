#!/usr/bin/env python3
"""
Manual Verification Script for Local Storage Persistence

This script helps verify that localStorage persistence is working correctly
by checking the frontend code and providing testing instructions.

Usage:
    python tests/verify_local_storage_manual.py
"""

import subprocess
import time
import json
from pathlib import Path


def print_section(title):
    """Print a formatted section header."""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70 + "\n")


def check_frontend_running():
    """Check if the frontend development server is running."""
    try:
        result = subprocess.run(
            ["python", "-c", "import requests; print(requests.get('http://localhost:5173').status_code)"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.stdout.strip() == "200":
            return True
    except Exception as e:
        pass

    return False


def print_browser_test_instructions():
    """Print instructions for manual browser testing."""
    print_section("Manual Browser Testing Instructions")

    print("1. Open your browser and navigate to: http://localhost:5173\n")

    print("2. Open Browser DevTools (F12 or Cmd+Option+I)\n")

    print("3. Go to the Console tab\n")

    print("4. Run these commands to test localStorage persistence:\n")

    commands = [
        ("// Check current localStorage", "localStorage.getItem('claude-ui-settings')"),
        ("// Set theme to dark", "localStorage.setItem('claude-ui-settings', JSON.stringify({theme: 'dark', fontSize: 20}))"),
        ("// Verify it was saved", "localStorage.getItem('claude-ui-settings')"),
        ("// Reload the page", "location.reload()"),
        ("// Check if settings persist after reload", "localStorage.getItem('claude-ui-settings')"),
    ]

    for i, (description, command) in enumerate(commands, 1):
        print(f"   {i}. {description}")
        print(f"      {command}")
        print()

    print("5. Expected Results:\n")
    print("   ✓ Settings should be saved to localStorage with key 'claude-ui-settings'")
    print("   ✓ Settings should persist after page reload")
    print("   ✓ UI should apply the saved settings on page load")
    print()


def print_ui_store_test():
    """Print instructions to test UI store directly."""
    print_section("UI Store Testing (Browser Console)")

    print("In the browser console on http://localhost:5173:\n")

    commands = [
        ("// Access the UI store (Zustand devtools)", "window.$r = window.__ZUSTAND_STORES__"),
        ("// Try to trigger theme change (if UI has settings)", "// Click the settings gear icon and change theme"),
        ("// Check if localStorage updates", "localStorage.getItem('claude-ui-settings')"),
        ("// Verify theme is applied to document", "document.documentElement.classList.contains('dark')"),
    ]

    for description, command in commands:
        print(f"   {command}")
        if "//" not in description:
            print(f"   // {description}")
        print()


def verify_code_implementation():
    """Verify that the code implementation is correct."""
    print_section("Code Implementation Verification")

    ui_store_path = Path("client/src/stores/uiStore.ts")
    app_path = Path("client/src/App.tsx")

    # Check UI store
    if ui_store_path.exists():
        content = ui_store_path.read_text()

        checks = [
            ("Persist middleware imported", "persist" in content and "zustand/middleware" in content),
            ("LocalStorage key configured", "'claude-ui-settings'" in content or '"claude-ui-settings"' in content),
            ("Partialize function defined", "partialize:" in content),
            ("Theme state defined", "theme:" in content),
            ("Font size state defined", "fontSize:" in content),
            ("setTheme action defined", "setTheme:" in content),
            ("setFontSize action defined", "setFontSize:" in content),
        ]

        print("UI Store (client/src/stores/uiStore.ts):")
        for check_name, passed in checks:
            status = "✓" if passed else "✗"
            print(f"   {status} {check_name}")
        print()

    # Check App.tsx
    if app_path.exists():
        content = app_path.read_text()

        checks = [
            ("useUIStore imported", "useUIStore" in content),
            ("useEffect for theme initialization", "setTheme(theme)" in content),
            ("useEffect for font size initialization", "setFontSize(fontSize)" in content),
        ]

        print("App Component (client/src/App.tsx):")
        for check_name, passed in checks:
            status = "✓" if passed else "✗"
            print(f"   {status} {check_name}")
        print()


def print_feature_summary():
    """Print a summary of the localStorage persistence feature."""
    print_section("Feature Summary: Local Storage Persistence")

    print("What persists across browser sessions:\n")

    persisted_items = [
        "Theme preference (light/dark/system)",
        "Font size (base font size in pixels)",
        "Selected model (Claude Sonnet/Haiku/Opus)",
        "Extended thinking toggle",
        "Custom instructions",
        "Temperature (0-1)",
        "Max tokens (1-4096)",
        "Permission mode (auto/manual)",
        "Memory enabled toggle",
        "Sidebar width",
    ]

    for item in persisted_items:
        print(f"   ✓ {item}")

    print("\nTransient state (NOT persisted):\n")

    transient_items = [
        "Sidebar open/closed state",
        "Panel open/closed state",
        "Current panel type (artifacts/files/todos)",
    ]

    for item in transient_items:
        print(f"   ✗ {item}")

    print()


def main():
    """Main verification function."""
    print_section("Local Storage Persistence - Verification Tool")

    # Check if frontend is running
    print("Checking if frontend server is running...")
    if check_frontend_running():
        print("✓ Frontend is running on http://localhost:5173\n")
    else:
        print("✗ Frontend is not running on http://localhost:5173")
        print("  Please start it with: cd client && pnpm dev\n")
        return

    # Verify code implementation
    verify_code_implementation()

    # Print feature summary
    print_feature_summary()

    # Print browser test instructions
    print_browser_test_instructions()
    print_ui_store_test()

    print_section("Next Steps")

    print("1. Open http://localhost:5173 in your browser")
    print("2. Open DevTools (F12)")
    print("3. Run the test commands above")
    print("4. Verify that preferences persist across page reloads")
    print("5. If all tests pass, the feature is working correctly!\n")

    print("For automated testing, run:")
    print("   python tests/test_local_storage_simple.py\n")


if __name__ == "__main__":
    main()
