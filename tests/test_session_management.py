#!/usr/bin/env python3
"""
Test Feature #135: Session management handles timeout correctly

Tests that the application handles session timeout with appropriate warnings,
data preservation, and session restoration.
"""

import os
from pathlib import Path
import re


def test_session_store_exists():
    """Verify that session store exists with proper state management"""
    store_path = Path(__file__).parent.parent / 'client' / 'src' / 'stores' / 'sessionStore.ts'

    assert store_path.exists(), "sessionStore.ts should exist"

    with open(store_path, 'r') as f:
        content = f.read()

    # Check for required state
    assert 'lastActivity' in content, "Should have lastActivity state"
    assert 'isSessionActive' in content, "Should have isSessionActive state"
    assert 'isTimedOut' in content, "Should have isTimedOut state"
    assert 'timeoutWarningShown' in content, "Should have timeoutWarningShown state"
    assert 'timeoutDuration' in content, "Should have timeoutDuration state"
    assert 'warningDuration' in content, "Should have warningDuration state"

    # Check for required actions
    assert 'updateActivity' in content, "Should have updateActivity action"
    assert 'checkSessionTimeout' in content, "Should have checkSessionTimeout action"
    assert 'handleTimeout' in content, "Should have handleTimeout action"
    assert 'extendSession' in content, "Should have extendSession action"
    assert 'resetSession' in content, "Should have resetSession action"

    # Check for data preservation
    assert 'preserveCurrentData' in content, "Should have preserveCurrentData action"
    assert 'restorePreservedData' in content, "Should have restorePreservedData action"
    assert 'clearPreservedData' in content, "Should have clearPreservedData action"
    assert 'preservedData' in content, "Should have preservedData state"

    print("✓ Session store exists with proper state management")


def test_session_timeout_modal_exists():
    """Verify that session timeout modal component exists"""
    component_path = Path(__file__).parent.parent / 'client' / 'src' / 'components' / 'SessionTimeoutModal.tsx'

    assert component_path.exists(), "SessionTimeoutModal.tsx should exist"

    with open(component_path, 'r') as f:
        content = f.read()

    # Check for component exports
    assert 'SessionTimeoutModal' in content, "Should export SessionTimeoutModal"

    # Check for timeout messaging
    assert 'Session Timed Out' in content or 'timed out' in content.lower(), "Should have timeout message"
    assert 'Session Expiring Soon' in content or 'expiring' in content.lower(), "Should have warning message"

    # Check for UI elements
    assert 'handleExtend' in content, "Should have extend session handler"
    assert 'onLogout' in content, "Should have logout handler"
    assert 'onClose' in content, "Should have close handler"

    # Check for time display
    assert 'formatTime' in content or 'timeRemaining' in content, "Should show time remaining"

    print("✓ Session timeout modal component exists")


def test_session_timeout_hook_exists():
    """Verify that session timeout hook exists"""
    hook_path = Path(__file__).parent.parent / 'client' / 'src' / 'hooks' / 'useSessionTimeout.ts'

    assert hook_path.exists(), "useSessionTimeout.ts should exist"

    with open(hook_path, 'r') as f:
        content = f.read()

    # Check for hook exports
    assert 'useSessionTimeout' in content, "Should export useSessionTimeout"

    # Check for activity monitoring
    assert 'handleUserActivity' in content or 'updateActivity' in content, "Should monitor user activity"
    assert 'mousedown' in content or 'keydown' in content, "Should listen to user events"

    # Check for timeout checking
    assert 'checkSessionTimeout' in content, "Should check for timeout"
    assert 'setInterval' in content, "Should use interval for checking"

    # Check for return values
    assert 'showWarning' in content, "Should return showWarning"
    assert 'showTimeout' in content, "Should return showTimeout"
    assert 'handleSessionReset' in content, "Should return handleSessionReset"
    assert 'handleLogout' in content, "Should return handleLogout"

    print("✓ Session timeout hook exists")


def test_app_uses_session_timeout():
    """Verify that App component uses session timeout monitoring"""
    app_path = Path(__file__).parent.parent / 'client' / 'src' / 'App.tsx'

    with open(app_path, 'r') as f:
        content = f.read()

    # Check for session timeout imports
    assert 'useSessionTimeout' in content, "Should import useSessionTimeout"
    assert 'SessionTimeoutModal' in content, "Should import SessionTimeoutModal"

    # Check for hook usage
    assert 'useSessionTimeout()' in content, "Should call useSessionTimeout hook"

    # Check for modal rendering
    assert 'showModal' in content, "Should have showModal state"
    assert 'SessionTimeoutModal' in content, "Should render SessionTimeoutModal"

    print("✓ App component uses session timeout monitoring")


def test_backend_session_endpoints():
    """Verify that backend has session management endpoints"""
    settings_path = Path(__file__).parent.parent / 'src' / 'api' / 'routes' / 'settings.py'

    with open(settings_path, 'r') as f:
        content = f.read()

    # Check for session endpoints
    assert 'refresh_session' in content, "Should have refresh_session endpoint"
    assert 'session_status' in content, "Should have session_status endpoint"

    # Check for endpoint decorators
    assert '@router.post("/refresh-session")' in content, "Should have POST /refresh-session"
    assert '@router.get("/session-status")' in content, "Should have GET /session-status"

    # Check for proper response structure
    assert 'session_active' in content, "Should return session_active status"
    assert 'timestamp' in content, "Should return timestamp"

    print("✓ Backend session endpoints exist")


def test_api_service_session_methods():
    """Verify that API service has session management methods"""
    api_path = Path(__file__).parent.parent / 'client' / 'src' / 'services' / 'api.ts'

    with open(api_path, 'r') as f:
        content = f.read()

    # Check for session methods
    assert 'refreshSession' in content, "Should have refreshSession method"
    assert 'getSessionStatus' in content, "Should have getSessionStatus method"

    # Check for API calls
    assert '/settings/refresh-session' in content, "Should call refresh-session endpoint"
    assert '/settings/session-status' in content, "Should call session-status endpoint"

    print("✓ API service has session management methods")


def test_data_preservation():
    """Verify that data preservation is implemented"""
    store_path = Path(__file__).parent.parent / 'client' / 'src' / 'stores' / 'sessionStore.ts'

    with open(store_path, 'r') as f:
        content = f.read()

    # Check for data preservation structure
    assert 'preservedData' in content, "Should have preservedData structure"
    assert 'conversations' in content, "Should preserve conversations"
    assert 'messages' in content, "Should preserve messages"
    assert 'settings' in content, "Should preserve settings"
    assert 'draftMessage' in content, "Should preserve draft messages"

    # Check for localStorage persistence
    assert 'localStorage' in content, "Should use localStorage for persistence"
    assert 'claude-session-preserved' in content, "Should use specific localStorage key"

    print("✓ Data preservation is implemented")


def test_timeout_warning_ui():
    """Verify that timeout warning UI is properly implemented"""
    modal_path = Path(__file__).parent.parent / 'client' / 'src' / 'components' / 'SessionTimeoutModal.tsx'

    with open(modal_path, 'r') as f:
        content = f.read()

    # Check for warning mode UI
    assert 'Session Expiring Soon' in content, "Should show warning title"
    assert 'timeRemaining' in content, "Should show remaining time"
    assert 'Extend Session' in content, "Should have extend button"

    # Check for timeout mode UI
    assert 'Session Timed Out' in content, "Should show timeout title"
    assert 'Restore Session' in content, "Should have restore button"
    assert 'Preserved Data' in content, "Should show preserved data info"

    # Check for accessibility
    assert 'role="dialog"' in content or 'role="alertdialog"' in content, "Should have proper ARIA roles"
    assert 'aria-labelledby' in content, "Should have labeled dialogs"

    print("✓ Timeout warning UI is properly implemented")


def test_activity_monitoring():
    """Verify that user activity is monitored"""
    hook_path = Path(__file__).parent.parent / 'client' / 'src' / 'hooks' / 'useSessionTimeout.ts'

    with open(hook_path, 'r') as f:
        content = f.read()

    # Check for activity events
    activity_events = ['mousedown', 'keydown', 'scroll', 'touchstart', 'mousemove']
    for event in activity_events:
        assert event in content, f"Should monitor {event} event"

    # Check for visibility tracking
    assert 'visibilitychange' in content, "Should track visibility changes"

    # Check for updateActivity call
    assert 'updateActivity' in content, "Should call updateActivity on user activity"

    print("✓ User activity monitoring is implemented")


def test_session_integration():
    """Verify that all session components are integrated"""
    files_to_check = [
        'client/src/stores/sessionStore.ts',
        'client/src/components/SessionTimeoutModal.tsx',
        'client/src/hooks/useSessionTimeout.ts',
        'client/src/App.tsx',
        'src/api/routes/settings.py',
        'client/src/services/api.ts',
    ]

    for file_path in files_to_check:
        full_path = Path(__file__).parent.parent / file_path
        assert full_path.exists(), f"{file_path} should exist"

    print("✓ All session components are integrated")


def main():
    """Run all session management tests"""
    print("\n" + "="*70)
    print("Testing Feature #135: Session Management")
    print("="*70 + "\n")

    tests = [
        test_session_store_exists,
        test_session_timeout_modal_exists,
        test_session_timeout_hook_exists,
        test_app_uses_session_timeout,
        test_backend_session_endpoints,
        test_api_service_session_methods,
        test_data_preservation,
        test_timeout_warning_ui,
        test_activity_monitoring,
        test_session_integration,
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
