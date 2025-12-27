"""
Test Feature #125: Empty states have appropriate illustrations and text
"""

import pytest
import sys
import os


def test_sidebar_empty_state():
    """Verify sidebar has proper empty state with illustration and CTA"""
    sidebar_path = os.path.join(
        os.path.dirname(__file__),
        '..',
        'client',
        'src',
        'components',
        'Sidebar.tsx'
    )

    with open(sidebar_path, 'r') as f:
        content = f.read()

    # Check for illustration
    assert '💬' in content, "Sidebar empty state should have chat icon illustration"

    # Check for helpful text
    assert 'No conversations yet' in content, \
        "Sidebar empty state should have helpful text"

    # Check for call-to-action button
    assert 'Start Chatting' in content, \
        "Sidebar empty state should have CTA button"

    assert 'onClick={handleNewConversation}' in content, \
        "CTA button should trigger new conversation creation"

    print("✓ Sidebar has proper empty state with illustration and CTA")


def test_welcome_screen_empty_state():
    """Verify WelcomeScreen has proper empty state with suggestions"""
    welcome_path = os.path.join(
        os.path.dirname(__file__),
        '..',
        'client',
        'src',
        'components',
        'WelcomeScreen.tsx'
    )

    with open(welcome_path, 'r') as f:
        content = f.read()

    # Check for welcome message
    assert 'How can I help you today?' in content, \
        "WelcomeScreen should have greeting message"

    # Check for suggestions
    assert 'suggestions' in content.lower(), \
        "WelcomeScreen should display conversation starters"

    # Check for helpful icons
    assert '✍️' in content or '💡' in content or '💻' in content, \
        "WelcomeScreen should have emoji icons for suggestions"

    # Check for description text
    assert 'Start a new conversation' in content or 'choose from the suggestions' in content, \
        "WelcomeScreen should have helpful description"

    print("✓ WelcomeScreen has proper empty state with suggestions")


def test_todo_panel_empty_state():
    """Verify TodoPanel has proper empty state with icon"""
    todo_path = os.path.join(
        os.path.dirname(__file__),
        '..',
        'client',
        'src',
        'components',
        'TodoPanel.tsx'
    )

    with open(todo_path, 'r') as f:
        content = f.read()

    # Check for illustration (emoji or SVG)
    assert ('📋' in content or 'svg' in content.lower()), \
        "TodoPanel empty state should have illustration"

    # Check for helpful text
    assert 'No tasks yet' in content or 'todos' in content.lower(), \
        "TodoPanel empty state should have helpful text"

    # Check for explanation
    assert 'Ask the agent' in content or 'plan a complex task' in content, \
        "TodoPanel empty state should explain how to create tasks"

    print("✓ TodoPanel has proper empty state with icon and explanation")


def test_files_panel_empty_state():
    """Verify FilesPanel has proper empty state with icon"""
    files_path = os.path.join(
        os.path.dirname(__file__),
        '..',
        'client',
        'src',
        'components',
        'FilesPanel.tsx'
    )

    with open(files_path, 'r') as f:
        content = f.read()

    # Check for illustration
    assert 'svg' in content.lower() or '📁' in content, \
        "FilesPanel empty state should have file icon illustration"

    # Check for helpful text
    assert 'No workspace files' in content or 'files' in content.lower(), \
        "FilesPanel empty state should have helpful text"

    # Check for explanation
    assert 'filesystem tools' in content or 'create files' in content, \
        "FilesPanel empty state should explain how to create files"

    print("✓ FilesPanel has proper empty state with icon and explanation")


def test_memory_manager_empty_state():
    """Verify MemoryManager has proper empty state with illustration"""
    memory_path = os.path.join(
        os.path.dirname(__file__),
        '..',
        'client',
        'src',
        'components',
        'MemoryManager.tsx'
    )

    with open(memory_path, 'r') as f:
        content = f.read()

    # Check for illustration
    assert '🧠' in content, \
        "MemoryManager empty state should have brain icon illustration"

    # Check for helpful text
    assert 'No memories yet' in content, \
        "MemoryManager empty state should have helpful text"

    # Check for explanation
    assert 'Memories help' in content or 'remember important' in content, \
        "MemoryManager empty state should explain the purpose of memories"

    # Check for hint/action
    assert 'Ask the agent' in content or 'create a memory' in content, \
        "MemoryManager empty state should suggest next action"

    print("✓ MemoryManager has proper empty state with illustration and explanation")


def test_memory_panel_empty_state():
    """Verify MemoryPanel has proper empty state"""
    memory_panel_path = os.path.join(
        os.path.dirname(__file__),
        '..',
        'client',
        'src',
        'components',
        'MemoryPanel.tsx'
    )

    with open(memory_panel_path, 'r') as f:
        content = f.read()

    # Check for illustration
    assert '🧠' in content, \
        "MemoryPanel empty state should have brain icon illustration"

    # Check for helpful text
    assert 'No memories found' in content, \
        "MemoryPanel empty state should have helpful text"

    # Check for explanation
    assert 'automatically stored' in content or 'tell the AI to remember' in content, \
        "MemoryPanel empty state should explain automatic memory creation"

    print("✓ MemoryPanel has proper empty state with illustration")


def test_empty_states_consistency():
    """Verify all empty states follow consistent pattern"""
    components = [
        ('Sidebar.tsx', 'No conversations yet'),
        ('TodoPanel.tsx', 'No tasks'),
        ('FilesPanel.tsx', 'No workspace files'),
        ('MemoryManager.tsx', 'No memories yet'),
        ('MemoryPanel.tsx', 'No memories found'),
        ('WelcomeScreen.tsx', 'How can I help'),
    ]

    for component_name, expected_text in components:
        component_path = os.path.join(
            os.path.dirname(__file__),
            '..',
            'client',
            'src',
            'components',
            component_name
        )

        if not os.path.exists(component_path):
            continue

        with open(component_path, 'r') as f:
            content = f.read()

        # All empty states should have emoji illustrations or SVG icons
        has_emoji = any(char in content for char in ['💬', '🧠', '📋', '📁', '✍️', '💡', '💻', '📊'])
        has_svg = 'svg' in content.lower()

        # Should have at least one type of illustration
        # (not all need emoji, some use SVG which is fine)
        if component_name in ['Sidebar.tsx', 'MemoryManager.tsx', 'MemoryPanel.tsx']:
            assert has_emoji, f"{component_name} should have emoji illustration"

        # All should have helpful text
        assert expected_text.lower() in content.lower(), \
            f"{component_name} should have helpful empty state text"

        print(f"✓ {component_name} follows consistent empty state pattern")


if __name__ == '__main__':
    print("\n" + "="*70)
    print("Testing Feature #125: Empty states have illustrations and text")
    print("="*70 + "\n")

    test_sidebar_empty_state()
    test_welcome_screen_empty_state()
    test_todo_panel_empty_state()
    test_files_panel_empty_state()
    test_memory_manager_empty_state()
    test_memory_panel_empty_state()
    test_empty_states_consistency()

    print("\n" + "="*70)
    print("All Feature #125 tests passed! ✓")
    print("="*70 + "\n")
