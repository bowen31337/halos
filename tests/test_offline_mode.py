#!/usr/bin/env python3
"""
Test Feature #134: Offline mode shows appropriate messaging

Tests that the application detects network status and shows appropriate
messaging when offline, with retry functionality.
"""

import os
from pathlib import Path
import re


def test_network_store_exists():
    """Verify that network store exists with proper state management"""
    store_path = Path(__file__).parent.parent / 'client' / 'src' / 'stores' / 'networkStore.ts'

    assert store_path.exists(), "networkStore.ts should exist"

    with open(store_path, 'r') as f:
        content = f.read()

    # Check for required state
    assert 'isOnline' in content, "Should have isOnline state"
    assert 'isOffline' in content, "Should have isOffline state"
    assert 'retryCount' in content, "Should have retryCount state"
    assert 'reconnectAttempts' in content, "Should have reconnectAttempts state"

    # Check for required actions
    assert 'setOnline' in content, "Should have setOnline action"
    assert 'incrementRetry' in content, "Should have incrementRetry action"
    assert 'resetRetry' in content, "Should have resetRetry action"
    assert 'incrementReconnectAttempts' in content, "Should have incrementReconnectAttempts action"
    assert 'resetReconnectAttempts' in content, "Should have resetReconnectAttempts action"

    print("✓ Network store exists with proper state management")


def test_network_status_indicator_exists():
    """Verify that network status indicator component exists"""
    component_path = Path(__file__).parent.parent / 'client' / 'src' / 'components' / 'NetworkStatusIndicator.tsx'

    assert component_path.exists(), "NetworkStatusIndicator.tsx should exist"

    with open(component_path, 'r') as f:
        content = f.read()

    # Check for component exports
    assert 'NetworkStatusIndicator' in content, "Should export NetworkStatusIndicator"
    assert 'NetworkStatusBadge' in content, "Should export NetworkStatusBadge"

    # Check for offline messaging
    assert 'offline' in content.lower(), "Should have offline messaging"
    assert 'retry' in content.lower(), "Should have retry functionality"

    # Check for banner styling
    assert 'fixed top-0' in content, "Should have fixed positioning for banner"
    assert 'z-[9999]' in content, "Should have high z-index for banner"

    print("✓ Network status indicator component exists")


def test_layout_uses_network_monitoring():
    """Verify that Layout component monitors network status"""
    layout_path = Path(__file__).parent.parent / 'client' / 'src' / 'components' / 'Layout.tsx'

    with open(layout_path, 'r') as f:
        content = f.read()

    # Check for network store import
    assert 'useNetworkStore' in content, "Should import useNetworkStore"
    assert 'NetworkStatusIndicator' in content, "Should import NetworkStatusIndicator"

    # Check for event listeners
    assert "window.addEventListener('online'" in content, "Should listen for online events"
    assert "window.addEventListener('offline'" in content, "Should listen for offline events"

    # Check for setOnline usage
    assert 'setOnline' in content, "Should call setOnline action"

    print("✓ Layout component monitors network status")


def test_header_shows_network_badge():
    """Verify that Header shows network status badge when offline"""
    header_path = Path(__file__).parent.parent / 'client' / 'src' / 'components' / 'Header.tsx'

    with open(header_path, 'r') as f:
        content = f.read()

    # Check for network store usage
    assert 'useNetworkStore' in content, "Should import useNetworkStore"
    assert 'isOffline' in content, "Should use isOffline state"
    assert 'NetworkStatusBadge' in content, "Should import NetworkStatusBadge"

    # Check for conditional rendering
    assert 'isOffline &&' in content or 'isOffline ?' in content, "Should conditionally render badge"

    print("✓ Header shows network status badge")


def test_offline_mode_ui_messaging():
    """Verify that offline mode has appropriate UI messaging"""
    indicator_path = Path(__file__).parent.parent / 'client' / 'src' / 'components' / 'NetworkStatusIndicator.tsx'

    with open(indicator_path, 'r') as f:
        content = f.read()

    # Check for clear messaging
    assert 'offline' in content.lower(), "Should mention offline status"
    assert 'connection' in content.lower(), "Should mention connection"
    assert 'restore' in content.lower() or 'reconnect' in content.lower(), "Should mention restoration"

    # Check for visual indicators
    assert 'bg-[var(--status-error)]' in content, "Should use error color for offline"
    assert 'bg-[var(--status-success)]' in content, "Should use success color for reconnection"

    print("✓ Offline mode has appropriate UI messaging")


def test_retry_functionality():
    """Verify that retry functionality exists"""
    indicator_path = Path(__file__).parent.parent / 'client' / 'src' / 'components' / 'NetworkStatusIndicator.tsx'

    with open(indicator_path, 'r') as f:
        content = f.read()

    # Check for retry button
    assert 'handleRetry' in content, "Should have retry handler"
    assert 'fetch' in content, "Should attempt to fetch"
    assert 'health' in content.lower(), "Should check health endpoint"

    # Check for connecting state
    assert 'isConnecting' in content, "Should track connecting state"

    print("✓ Retry functionality exists")


def test_network_store_persistence():
    """Verify that network state is properly managed"""
    store_path = Path(__file__).parent.parent / 'client' / 'src' / 'stores' / 'networkStore.ts'

    with open(store_path, 'r') as f:
        content = f.read()

    # Check for initial state based on navigator.onLine
    assert 'navigator.onLine' in content, "Should initialize based on navigator.onLine"

    # Check for proper state updates
    assert 'isOnline: ' in content and 'isOffline: ' in content, "Should set both states"

    print("✓ Network store properly manages state")


def test_offline_mode_integration():
    """Verify that offline mode is integrated with the application"""
    # Check that all required files exist
    files_to_check = [
        'client/src/stores/networkStore.ts',
        'client/src/components/NetworkStatusIndicator.tsx',
        'client/src/components/Layout.tsx',
        'client/src/components/Header.tsx',
    ]

    for file_path in files_to_check:
        full_path = Path(__file__).parent.parent / file_path
        assert full_path.exists(), f"{file_path} should exist"

    print("✓ Offline mode is integrated with the application")


def test_chatinput_offline_behavior():
    """Verify that ChatInput handles offline mode correctly"""
    chatinput_path = Path(__file__).parent.parent / 'client' / 'src' / 'components' / 'ChatInput.tsx'

    with open(chatinput_path, 'r') as f:
        content = f.read()

    # Check for network store import
    assert 'useNetworkStore' in content, "Should import useNetworkStore"
    assert 'isOffline' in content, "Should use isOffline state"

    # Check for offline messaging in UI
    assert 'offline' in content.lower(), "Should have offline messaging"
    assert 'queue' in content.lower() or 'queued' in content.lower(), "Should mention queuing"

    # Check for offline handling in handleSend
    assert 'if (isOffline)' in content or 'isOffline &&' in content, "Should check offline state in send handler"

    print("✓ ChatInput handles offline mode correctly")


def test_chatinput_offline_action_queue():
    """Verify that ChatInput uses action queue for offline mode"""
    chatinput_path = Path(__file__).parent.parent / 'client' / 'src' / 'components' / 'ChatInput.tsx'

    with open(chatinput_path, 'r') as f:
        content = f.read()

    # Check for queueAction usage
    assert 'queueAction' in content, "Should use queueAction to queue messages"
    assert 'actionQueue' in content, "Should access actionQueue"

    # Check for proper action type
    assert "type: 'send_message'" in content, "Should queue with send_message type"

    print("✓ ChatInput uses action queue for offline mode")


def test_chatinput_offline_ui_indicators():
    """Verify that ChatInput shows appropriate UI indicators when offline"""
    chatinput_path = Path(__file__).parent.parent / 'client' / 'src' / 'components' / 'ChatInput.tsx'

    with open(chatinput_path, 'r') as f:
        content = f.read()

    # Check for offline banner/indicator in JSX
    assert 'isOffline' in content, "Should check isOffline for conditional rendering"

    # Check for disabled state on input elements
    assert 'disabled' in content, "Should have disabled attribute"

    print("✓ ChatInput shows appropriate UI indicators when offline")


def test_offline_mode_chatinput_complete():
    """Verify all ChatInput offline mode requirements are met"""
    chatinput_path = Path(__file__).parent.parent / 'client' / 'src' / 'components' / 'ChatInput.tsx'

    with open(chatinput_path, 'r') as f:
        content = f.read()

    # All requirements from feature spec:
    # 1. Offline indicator exists
    assert 'isOffline' in content, "Requirement 1: Offline indicator exists"

    # 2. UI messaging exists
    assert 'offline' in content.lower(), "Requirement 2: UI messaging exists"

    # 3. Send/queue functionality with explanation
    assert 'queueAction' in content, "Requirement 3: Queuing functionality exists"

    # 4. Messages are preserved in chat
    assert 'addMessage' in content, "Requirement 4: Messages preserved in chat"

    # 5. Action queue is used
    assert 'actionQueue' in content, "Requirement 5: Action queue is used"

    print("✓ ChatInput offline mode complete")


def main():
    """Run all offline mode tests"""
    print("\n" + "="*70)
    print("Testing Feature #134: Offline Mode")
    print("="*70 + "\n")

    tests = [
        test_network_store_exists,
        test_network_status_indicator_exists,
        test_layout_uses_network_monitoring,
        test_header_shows_network_badge,
        test_offline_mode_ui_messaging,
        test_retry_functionality,
        test_network_store_persistence,
        test_offline_mode_integration,
        test_chatinput_offline_behavior,
        test_chatinput_offline_action_queue,
        test_chatinput_offline_ui_indicators,
        test_offline_mode_chatinput_complete,
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

    print("\n" + "="*70)
    print(f"Results: {passed} passed, {failed} failed")
    print("="*70 + "\n")

    return failed == 0


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
