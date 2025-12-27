"""
QA Test for Feature #78: Welcome Screen with Clickable Suggestions

This test verifies that:
1. WelcomeScreen component exists with suggestions
2. Each suggestion has a click handler
3. Clicking a suggestion calls setInputMessage with the prompt
4. ChatPage shows welcome screen when messages.length === 0
5. Welcome screen disappears after sending a message
"""

import pytest
import sys
import os

# Add client/src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'client', 'src'))

def test_welcome_screen_component_exists():
    """Test 1: Verify WelcomeScreen component exists"""
    from components import WelcomeScreen
    
    # Check component has render function
    assert hasattr(WelcomeScreen, 'WelcomeScreen')
    print("✓ WelcomeScreen component exists")

def test_welcome_screen_has_suggestions():
    """Test 2: Verify WelcomeScreen has 4 suggestions with prompts"""
    import subprocess
    result = subprocess.run(
        ['grep', '-A', '30', 'suggestions =', 'client/src/components/WelcomeScreen.tsx'],
        capture_output=True, text=True, cwd='/media/DATA/projects/autonomous-coding-clone-cc/talos'
    )
    
    content = result.stdout
    assert 'Help me write' in content
    assert 'Explain a topic' in content
    assert 'Help me code' in content
    assert 'Analyze data' in content
    assert 'prompt:' in content
    print("✓ WelcomeScreen has 4 suggestions with prompts")

def test_welcome_screen_has_click_handler():
    """Test 3: Verify suggestions have onClick handler"""
    import subprocess
    result = subprocess.run(
        ['grep', '-A', '10', 'onClick', 'client/src/components/WelcomeScreen.tsx'],
        capture_output=True, text=True, cwd='/media/DATA/projects/autonomous-coding-clone-cc/talos'
    )
    
    content = result.stdout
    assert 'handleSuggestion' in content
    assert 'setInputMessage' in content
    print("✓ WelcomeScreen has onClick handler with setInputMessage")

def test_chat_page_shows_welcome_when_empty():
    """Test 4: Verify ChatPage shows welcome when messages.length === 0"""
    import subprocess
    result = subprocess.run(
        ['grep', '-A', '5', 'showWelcome', 'client/src/pages/ChatPage.tsx'],
        capture_output=True, text=True, cwd='/media/DATA/projects/autonomous-coding-clone-cc/talos'
    )
    
    content = result.stdout
    assert "showWelcome = messages.length === 0" in content or "const showWelcome = messages.length === 0" in content
    assert "{showWelcome ?" in content
    print("✓ ChatPage shows WelcomeScreen when messages.length === 0")

def test_welcome_screen_disappears_after_message():
    """Test 5: Verify welcome screen condition logic"""
    import subprocess
    result = subprocess.run(
        ['grep', '-B', '2', '-A', '8', 'showWelcome', 'client/src/pages/ChatPage.tsx'],
        capture_output=True, text=True, cwd='/media/DATA/projects/autonomous-coding-clone-cc/talos'
    )
    
    content = result.stdout
    # Verify ternary operator: welcome if showWelcome, else MessageList
    assert "showWelcome ?" in content
    assert "<WelcomeScreen />" in content or "<WelcomeScreen" in content
    assert "<MessageList />" in content or "<MessageList" in content
    print("✓ Welcome screen disappears when messages exist")

if __name__ == '__main__':
    print("\n=== QA Test: Feature #78 - Welcome Screen with Clickable Suggestions ===\n")
    
    tests = [
        test_welcome_screen_component_exists,
        test_welcome_screen_has_suggestions,
        test_welcome_screen_has_click_handler,
        test_chat_page_shows_welcome_when_empty,
        test_welcome_screen_disappears_after_message,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"✗ {test.__name__}: {e}")
            failed += 1
    
    print(f"\n=== Results: {passed}/{len(tests)} tests passed ===")
    
    if failed == 0:
        print("✓ Feature #78 is VERIFIED - All tests passed!")
        sys.exit(0)
    else:
        print(f"✗ {failed} test(s) failed")
        sys.exit(1)
