#!/usr/bin/env python3
"""Test Styling Features (Features #101-105) - Code verification.

This test verifies that:
1. Feature #101: Primary orange/amber color (#CC785C) is defined
2. Feature #102: Light theme background colors are defined
3. Feature #103: Dark theme colors are defined
4. Feature #104: Typography font family and sizes are defined
5. Feature #105: Message bubble styling uses correct colors

Tests use file-based verification to check CSS variables and component usage.
"""

import re


def test_primary_color_is_defined():
    """Verify primary orange/amber color (#CC785C) is defined in CSS."""
    print("\n1. Checking for primary color definition...")

    with open('client/src/index.css', 'r') as f:
        css = f.read()

    # Check for primary color
    assert '--primary: #CC785C' in css, "Primary color #CC785C not found"
    assert '--primary-hover: #B86A4E' in css, "Primary hover color not found"
    assert '--primary-active: #A35D42' in css, "Primary active color not found"

    print("   ✓ Primary color #CC785C defined")
    print("   ✓ Primary hover color #B86A4E defined")
    print("   ✓ Primary active color #A35D42 defined")
    return True


def test_light_theme_colors():
    """Verify light theme background colors are defined."""
    print("\n2. Checking light theme colors...")

    with open('client/src/index.css', 'r') as f:
        css = f.read()

    # Extract :root section
    root_match = re.search(r':root\s*\{([^}]+)\}', css, re.DOTALL)
    assert root_match, "No :root CSS block found"
    root_section = root_match.group(1)

    # Check light theme colors
    assert '--bg-primary: #FFFFFF' in root_section, "Light bg-primary not found"
    assert '--bg-secondary: #F5F5F5' in root_section, "Light bg-secondary not found"
    assert '--bg-elevated: #FAFAFA' in root_section, "Light bg-elevated not found"
    assert '--surface-elevated: #FAFAFA' in root_section, "Light surface-elevated not found"
    assert '--text-primary: #1A1A1A' in root_section, "Light text-primary not found"
    assert '--text-secondary: #6B7280' in root_section, "Light text-secondary not found"
    assert '--text-muted: #9CA3AF' in root_section, "Light text-muted not found"
    assert '--border: #E5E5E5' in root_section, "Light border not found"
    assert '--border-primary: #E5E5E5' in root_section, "Light border-primary not found"
    assert '--border-light: #F0F0F0' in root_section, "Light border-light not found"

    print("   ✓ Light theme background colors defined")
    print("   ✓ Light theme text colors defined")
    print("   ✓ Light theme border colors defined")
    return True


def test_dark_theme_colors():
    """Verify dark theme colors are defined."""
    print("\n3. Checking dark theme colors...")

    with open('client/src/index.css', 'r') as f:
        css = f.read()

    # Extract .dark section
    dark_match = re.search(r'\.dark\s*\{([^}]+)\}', css, re.DOTALL)
    assert dark_match, "No .dark CSS block found"
    dark_section = dark_match.group(1)

    # Check dark theme colors
    assert '--bg-primary: #1A1A1A' in dark_section, "Dark bg-primary not found"
    assert '--bg-secondary: #2A2A2A' in dark_section, "Dark bg-secondary not found"
    assert '--bg-elevated: #333333' in dark_section, "Dark bg-elevated not found"
    assert '--surface-elevated: #333333' in dark_section, "Dark surface-elevated not found"
    assert '--text-primary: #E5E5E5' in dark_section, "Dark text-primary not found"
    assert '--text-secondary: #9CA3AF' in dark_section, "Dark text-secondary not found"
    assert '--text-muted: #6B7280' in dark_section, "Dark text-muted not found"
    assert '--border: #404040' in dark_section, "Dark border not found"
    assert '--border-primary: #404040' in dark_section, "Dark border-primary not found"
    assert '--border-light: #333333' in dark_section, "Dark border-light not found"

    print("   ✓ Dark theme background colors defined")
    print("   ✓ Dark theme text colors defined")
    print("   ✓ Dark theme border colors defined")
    return True


def test_typography_definitions():
    """Verify typography font family and sizes are defined."""
    print("\n4. Checking typography definitions...")

    with open('client/src/index.css', 'r') as f:
        css = f.read()

    # Check font family in body
    assert 'font-family:' in css and 'Inter' in css, "Inter font family not found"
    assert '--base-font-size: 16px' in css, "Base font size not found"

    # Check prose styles exist
    assert '.prose' in css, "Prose styles not found"
    assert '.prose h1' in css or 'prose h1' in css, "Prose h1 styles not found"
    assert '.prose h2' in css or 'prose h2' in css, "Prose h2 styles not found"
    assert '.prose p' in css or 'prose p' in css, "Prose p styles not found"

    print("   ✓ Inter font family defined")
    print("   ✓ Base font size (16px) defined")
    print("   ✓ Prose typography styles defined")
    return True


def test_message_bubble_styling():
    """Verify message bubble styling uses correct CSS variables."""
    print("\n5. Checking message bubble styling...")

    with open('client/src/components/MessageBubble.tsx', 'r') as f:
        component = f.read()

    # Check user message styling uses primary color
    assert 'bg-[var(--primary)]' in component, "User message doesn't use --primary variable"
    assert 'text-white' in component, "User message doesn't use white text"

    # Check assistant message styling
    assert 'bg-[var(--bg-secondary)]' in component, "Assistant message doesn't use --bg-secondary"
    assert 'text-[var(--text-primary)]' in component, "Assistant message doesn't use --text-primary"

    # Check border styling
    assert 'border-[var(--border-primary)]' in component, "Borders don't use --border-primary"

    # Check code block styling
    assert 'bg-[var(--bg-secondary)]' in component, "Code blocks don't use --bg-secondary"
    assert 'bg-[var(--bg-primary)]' in component, "Code blocks don't use --bg-primary"

    print("   ✓ User messages use primary color")
    print("   ✓ Assistant messages use background secondary")
    print("   ✓ Borders use border-primary variable")
    print("   ✓ Code blocks use correct background variables")
    return True


def test_header_styling():
    """Verify header uses correct styling variables."""
    print("\n6. Checking header styling...")

    with open('client/src/components/Header.tsx', 'r') as f:
        component = f.read()

    # Check header uses correct background and border
    assert 'bg-[var(--surface-secondary)]' in component or 'bg-[var(--surface-elevated)]' in component, \
        "Header doesn't use surface variables"
    assert 'border-[var(--border-primary)]' in component, "Header doesn't use border-primary"

    # Check buttons use hover states
    assert 'hover:bg-[var(--surface-elevated)]' in component, "Buttons missing hover state"

    print("   ✓ Header uses surface variables")
    print("   ✓ Header uses border-primary")
    print("   ✓ Buttons have hover states")
    return True


def test_chat_input_styling():
    """Verify chat input uses correct styling variables."""
    print("\n7. Checking chat input styling...")

    with open('client/src/components/ChatInput.tsx', 'r') as f:
        component = f.read()

    # Check input styling
    assert 'border-[var(--border-primary)]' in component, "Input doesn't use border-primary"
    assert 'bg-[var(--bg-primary)]' in component, "Input doesn't use bg-primary"
    assert 'text-[var(--text-primary)]' in component, "Input doesn't use text-primary"
    assert 'focus:ring-[var(--primary)]' in component, "Input doesn't use primary for focus ring"

    # Check button styling
    assert 'bg-[var(--primary)]' in component, "Send button doesn't use primary"
    assert 'hover:bg-[var(--primary-hover)]' in component, "Send button missing hover"

    print("   ✓ Input uses border-primary")
    print("   ✓ Input uses bg-primary and text-primary")
    print("   ✓ Focus ring uses primary color")
    print("   ✓ Send button uses primary with hover")
    return True


def test_layout_styling():
    """Verify layout uses correct styling variables."""
    print("\n8. Checking layout styling...")

    with open('client/src/components/Layout.tsx', 'r') as f:
        component = f.read()

    # Check main container
    assert 'bg-[var(--bg-primary)]' in component, "Layout doesn't use bg-primary"

    print("   ✓ Layout uses bg-primary")
    return True


def test_all_styling_features():
    """Run all styling tests."""
    print("=" * 60)
    print("Testing Styling Features #101-105")
    print("=" * 60)

    results = []

    try:
        results.append(("Primary Color (#CC785C)", test_primary_color_is_defined()))
    except AssertionError as e:
        results.append(("Primary Color (#CC785C)", False))
        print(f"   ✗ FAILED: {e}")

    try:
        results.append(("Light Theme Colors", test_light_theme_colors()))
    except AssertionError as e:
        results.append(("Light Theme Colors", False))
        print(f"   ✗ FAILED: {e}")

    try:
        results.append(("Dark Theme Colors", test_dark_theme_colors()))
    except AssertionError as e:
        results.append(("Dark Theme Colors", False))
        print(f"   ✗ FAILED: {e}")

    try:
        results.append(("Typography Definitions", test_typography_definitions()))
    except AssertionError as e:
        results.append(("Typography Definitions", False))
        print(f"   ✗ FAILED: {e}")

    try:
        results.append(("Message Bubble Styling", test_message_bubble_styling()))
    except AssertionError as e:
        results.append(("Message Bubble Styling", False))
        print(f"   ✗ FAILED: {e}")

    try:
        results.append(("Header Styling", test_header_styling()))
    except AssertionError as e:
        results.append(("Header Styling", False))
        print(f"   ✗ FAILED: {e}")

    try:
        results.append(("Chat Input Styling", test_chat_input_styling()))
    except AssertionError as e:
        results.append(("Chat Input Styling", False))
        print(f"   ✗ FAILED: {e}")

    try:
        results.append(("Layout Styling", test_layout_styling()))
    except AssertionError as e:
        results.append(("Layout Styling", False))
        print(f"   ✗ FAILED: {e}")

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    return passed == total


if __name__ == "__main__":
    import sys
    success = test_all_styling_features()
    sys.exit(0 if success else 1)
