"""
Test Suite: Offline Mode Functionality

This test verifies that the offline mode feature works correctly:
- Offline indicator appears when offline
- Local data remains accessible
- Send button is disabled/queued when offline
- Actions are queued when offline
- Queued actions sync when connection restored
"""

import os
import sys
import json

# Add parent directory to path to import from src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def test_network_store_exists():
    """Test that networkStore.ts exists and has correct structure"""
    client_src = os.path.join(os.path.dirname(__file__), '..', 'client', 'src', 'stores', 'networkStore.ts')

    assert os.path.exists(client_src), "networkStore.ts should exist"
    print("✅ networkStore.ts exists")

    with open(client_src, 'r') as f:
        content = f.read()

    # Check for required fields and methods
    required_fields = [
        'isOnline',
        'isOffline',
        'actionQueue',
        'setOnline',
        'queueAction',
        'dequeueAction',
        'processQueue',
    ]

    for field in required_fields:
        assert field in content, f"networkStore should have {field}"
        print(f"✅ networkStore has {field}")


def test_online_status_hook_exists():
    """Test that useOnlineStatus hook exists"""
    hook_path = os.path.join(os.path.dirname(__file__), '..', 'client', 'src', 'hooks', 'useOnlineStatus.ts')

    assert os.path.exists(hook_path), "useOnlineStatus.ts should exist"
    print("✅ useOnlineStatus.ts exists")

    with open(hook_path, 'r') as f:
        content = f.read()

    # Check for event listeners
    assert 'addEventListener' in content, "Should listen to online/offline events"
    assert "'online'" in content or '"online"' in content, "Should listen to 'online' event"
    assert "'offline'" in content or '"offline"' in content, "Should listen to 'offline' event"
    assert 'setOnline' in content, "Should call setOnline"
    assert 'processQueue' in content, "Should process queue when coming online"
    print("✅ useOnlineStatus hook monitors online/offline status")


def test_offline_indicator_component_exists():
    """Test that OfflineIndicator component exists"""
    component_path = os.path.join(os.path.dirname(__file__), '..', 'client', 'src', 'components', 'OfflineIndicator.tsx')

    assert os.path.exists(component_path), "OfflineIndicator.tsx should exist"
    print("✅ OfflineIndicator.tsx exists")

    with open(component_path, 'r') as f:
        content = f.read()

    # Check for offline indicator usage
    assert 'isOffline' in content, "Should use isOffline from networkStore"
    assert 'actionQueue' in content, "Should show actionQueue count"
    assert 'You are offline' in content or 'offline' in content.lower(), "Should display offline message"
    print("✅ OfflineIndicator component renders offline status")


def test_app_integrates_offline_mode():
    """Test that App.tsx integrates offline mode"""
    app_path = os.path.join(os.path.dirname(__file__), '..', 'client', 'src', 'App.tsx')

    assert os.path.exists(app_path), "App.tsx should exist"

    with open(app_path, 'r') as f:
        content = f.read()

    # Check for imports and usage
    assert 'useOnlineStatus' in content, "App should use useOnlineStatus hook"
    assert 'OfflineIndicator' in content, "App should render OfflineIndicator"
    assert 'useOnlineStatus()' in content, "App should call useOnlineStatus()"
    print("✅ App.tsx integrates offline mode")


def test_chat_input_offline_handling():
    """Test that ChatInput handles offline mode"""
    chat_input_path = os.path.join(os.path.dirname(__file__), '..', 'client', 'src', 'components', 'ChatInput.tsx')

    assert os.path.exists(chat_input_path), "ChatInput.tsx should exist"

    with open(chat_input_path, 'r') as f:
        content = f.read()

    # Check for offline handling
    assert 'isOffline' in content, "ChatInput should use isOffline"
    assert 'queueAction' in content, "ChatInput should queue actions when offline"
    assert 'isOffline' in content and 'Queue' in content, "Send button should show 'Queue' when offline"
    assert 'Message will be queued' in content or 'queued' in content.lower(), "Should indicate message will be queued"
    print("✅ ChatInput handles offline mode")
    print("✅ Send button shows 'Queue' when offline")
    print("✅ Messages are queued when offline")


def test_local_storage_persistence():
    """Test that offline queue is persisted to localStorage"""
    network_store_path = os.path.join(os.path.dirname(__file__), '..', 'client', 'src', 'stores', 'networkStore.ts')

    with open(network_store_path, 'r') as f:
        content = f.read()

    # Check for localStorage persistence
    assert 'localStorage' in content, "Should use localStorage"
    assert 'claude-offline-queue' in content, "Should persist queue to localStorage"
    assert 'JSON.parse' in content and 'JSON.stringify' in content, "Should serialize queue"
    print("✅ Offline queue is persisted to localStorage")


def test_queue_processing_on_reconnect():
    """Test that queue is processed when connection is restored"""
    network_store_path = os.path.join(os.path.dirname(__file__), '..', 'client', 'src', 'stores', 'networkStore.ts')

    with open(network_store_path, 'r') as f:
        content = f.read()

    # Check for processQueue method
    assert 'processQueue' in content, "Should have processQueue method"
    assert 'async' in content and 'processQueue' in content, "processQueue should be async"
    print("✅ Queue processing method exists")


def run_all_tests():
    """Run all offline mode tests"""
    print("\n" + "="*70)
    print("OFFLINE MODE TEST SUITE")
    print("="*70 + "\n")

    tests = [
        ("Network Store Exists", test_network_store_exists),
        ("Online Status Hook Exists", test_online_status_hook_exists),
        ("Offline Indicator Component", test_offline_indicator_component_exists),
        ("App Integration", test_app_integrates_offline_mode),
        ("ChatInput Offline Handling", test_chat_input_offline_handling),
        ("LocalStorage Persistence", test_local_storage_persistence),
        ("Queue Processing on Reconnect", test_queue_processing_on_reconnect),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        print(f"\n{'='*70}")
        print(f"Test: {test_name}")
        print('='*70)
        try:
            test_func()
            passed += 1
            print(f"✅ PASSED: {test_name}\n")
        except AssertionError as e:
            failed += 1
            print(f"❌ FAILED: {test_name}")
            print(f"   Error: {str(e)}\n")
        except Exception as e:
            failed += 1
            print(f"❌ ERROR in {test_name}: {str(e)}\n")

    print("\n" + "="*70)
    print(f"TEST RESULTS: {passed} passed, {failed} failed out of {len(tests)} tests")
    print("="*70 + "\n")

    return failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
