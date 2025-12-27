"""
QA Test for Feature #78: Welcome Screen with Clickable Suggestions

This test verifies code structure for:
1. WelcomeScreen component exists with 4 suggestions
2. Each suggestion has prompt field
3. Click handler calls setInputMessage with prompt
4. ChatPage shows welcome when messages.length === 0
"""

import subprocess
import os

def run_grep(pattern, file):
    """Helper to run grep and return output"""
    result = subprocess.run(
        ['grep', pattern, file],
        capture_output=True, text=True,
        cwd='/media/DATA/projects/autonomous-coding-clone-cc/talos'
    )
    return result.stdout, result.returncode

def test_welcome_screen_component():
    """Test 1: Verify WelcomeScreen component file exists"""
    exists = os.path.exists('client/src/components/WelcomeScreen.tsx')
    assert exists, "WelcomeScreen.tsx file does not exist"
    print("✓ Test 1: WelcomeScreen component exists")

def test_suggestions_structure():
    """Test 2: Verify 4 suggestions with prompts exist"""
    output, _ = run_grep('-A', 'client/src/components/WelcomeScreen.tsx')
    assert 'title: \'Help me write\'' in output
    assert 'title: \'Explain a topic\'' in output
    assert 'title: \'Help me code\'' in output
    assert 'title: \'Analyze data\'' in output
    assert 'prompt:' in output
    print("✓ Test 2: 4 suggestions with prompts exist")

def test_handle_suggestion_function():
    """Test 3: Verify handleSuggestion function calls setInputMessage"""
    output, _ = run_grep('handleSuggestion', 'client/src/components/WelcomeScreen.tsx')
    assert 'setInputMessage' in output
    assert 'prompt' in output
    print("✓ Test 3: handleSuggestion calls setInputMessage")

def test_onclick_handler():
    """Test 4: Verify onClick handler exists on suggestion buttons"""
    output, _ = run_grep('onClick', 'client/src/components/WelcomeScreen.tsx')
    assert 'handleSuggestion' in output
    print("✓ Test 4: onClick handler calls handleSuggestion")

def test_chat_page_show_welcome():
    """Test 5: Verify ChatPage shows welcome when messages.length === 0"""
    output, _ = run_grep('showWelcome', 'client/src/pages/ChatPage.tsx')
    assert 'messages.length === 0' in output
    print("✓ Test 5: ChatPage shows welcome when messages.length === 0")

def test_welcome_conditional_render():
    """Test 6: Verify ternary operator for welcome vs messages"""
    output, _ = run_grep('-A', 'client/src/pages/ChatPage.tsx')
    assert 'showWelcome ?' in output
    assert '<WelcomeScreen' in output
    assert '<MessageList' in output
    print("✓ Test 6: Conditional render (welcome vs messages) exists")

if __name__ == '__main__':
    print("\n=== QA Test: Feature #78 - Welcome Screen ===\n")

    tests = [
        test_welcome_screen_component,
        test_suggestions_structure,
        test_handle_suggestion_function,
        test_onclick_handler,
        test_chat_page_show_welcome,
        test_welcome_conditional_render,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"✗ {test.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test.__name__}: Unexpected error - {e}")
            failed += 1

    print(f"\n=== Results: {passed}/{len(tests)} tests passed ===\n")

    if failed == 0:
        print("✅ Feature #78 QA PASSED - All code structure verified!")
        print("\nImplementation Summary:")
        print("- WelcomeScreen component: ✓")
        print("- 4 suggestions with prompts: ✓")
        print("- Click handlers with setInputMessage: ✓")
        print("- ChatPage conditional render: ✓")
    else:
        print(f"❌ {failed} test(s) failed")

    exit(0 if failed == 0 else 1)
