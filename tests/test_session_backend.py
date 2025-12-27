"""Backend Session Management Tests (Feature #137)

Tests for backend session timeout handling:
1. Session manager creates tokens correctly
2. Session timeout is enforced
3. Token refresh works
4. Session middleware returns appropriate headers
5. Session status endpoint works
"""

import time
import jwt
import pytest
from datetime import timedelta

from src.core.session import SessionManager, TokenData, session_manager
from src.core.config import settings


def test_session_manager_init():
    """Verify session manager initializes with correct settings."""
    sm = SessionManager()
    assert sm.timeout_minutes == settings.access_token_expire_minutes
    assert sm.refresh_buffer_minutes == 5
    assert sm.refresh_token_expiry_days == 7
    assert isinstance(sm.sessions, dict)
    print("✓ Session manager initializes correctly")


def test_create_access_token():
    """Verify access token creation."""
    sm = SessionManager()
    data = {"sub": "test_user", "session_id": "test_session", "last_activity": int(time.time())}

    token = sm.create_access_token(data)
    assert token is not None
    assert isinstance(token, str)
    assert len(token) > 0
    print("✓ Access token created successfully")


def test_create_refresh_token():
    """Verify refresh token creation."""
    sm = SessionManager()
    session_id = "test_session_123"

    # Create session first
    sm.sessions[session_id] = {
        "username": "test_user",
        "created_at": int(time.time()),
        "last_activity": int(time.time()),
        "is_active": True
    }

    refresh_token = sm.create_refresh_token(session_id)
    assert refresh_token is not None
    assert refresh_token.startswith("refresh_")
    assert sm.sessions[session_id]["refresh_token"] == refresh_token
    print("✓ Refresh token created successfully")


def test_create_full_session():
    """Verify full session with both tokens."""
    sm = SessionManager()
    result = sm.create_full_session("test_user")

    assert "access_token" in result
    assert "refresh_token" in result
    assert "session_id" in result
    assert result["access_token"].startswith("eyJ")  # JWT format
    assert result["refresh_token"].startswith("refresh_")
    print("✓ Full session created with both tokens")


def test_verify_token():
    """Verify token verification."""
    sm = SessionManager()

    # Create session and token
    token = sm.create_session("test_user")

    # Verify token
    token_data = sm.verify_token(token)
    assert token_data is not None
    assert token_data.username == "test_user"
    assert token_data.session_id is not None
    print("✓ Token verification works")


def test_session_activity_timeout():
    """Verify session times out based on last activity."""
    sm = SessionManager()
    original_timeout = sm.timeout_minutes
    sm.timeout_minutes = 0.01  # 0.01 minutes = 0.6 seconds for testing

    try:
        # Create session with short timeout
        token = sm.create_session("test_user")

        # Decode token to get session_id
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        session_id = payload["session_id"]
        last_activity = payload["last_activity"]

        # Session should be active initially
        assert sm._is_session_active(session_id, last_activity)

        # Wait for timeout (longer than JWT expiry)
        time.sleep(1.0)

        # Session should be inactive (last_activity is old)
        # Note: verify_token will fail because JWT is expired
        token_data = sm.verify_token(token)
        assert token_data is None
        print("✓ Session times out correctly after inactivity")
    finally:
        sm.timeout_minutes = original_timeout


def test_refresh_token():
    """Verify token refresh."""
    sm = SessionManager()

    # Create session
    token = sm.create_session("test_user")
    token_data = sm.verify_token(token)

    # Refresh the token
    new_token = sm.refresh_token(token_data)
    assert new_token is not None
    assert new_token != token  # Should be a new token

    # New token should be valid
    new_token_data = sm.verify_token(new_token)
    assert new_token_data is not None
    assert new_token_data.username == token_data.username
    print("✓ Token refresh works")


def test_refresh_with_refresh_token():
    """Verify refresh using refresh token."""
    sm = SessionManager()

    # Create full session
    result = sm.create_full_session("test_user")
    access_token = result["access_token"]
    refresh_token = result["refresh_token"]

    # Use refresh token to get new access token
    new_access_token = sm.refresh_with_refresh_token(refresh_token)
    assert new_access_token is not None
    assert new_access_token != access_token

    # New token should be valid
    token_data = sm.verify_token(new_access_token)
    assert token_data is not None
    print("✓ Refresh with refresh token works")


def test_should_refresh_token():
    """Verify token refresh threshold."""
    sm = SessionManager()

    # Create token data that's about to expire
    current_time = int(time.time())
    expiring_soon = current_time + (2 * 60)  # 2 minutes from now

    token_data = TokenData(
        username="test_user",
        session_id="test_session",
        last_activity=current_time,
        exp=expiring_soon
    )

    # Should need refresh (within 5 minute buffer)
    assert sm.should_refresh_token(token_data) == True

    # Token far from expiry
    far_future = current_time + (30 * 60)  # 30 minutes
    token_data_far = TokenData(
        username="test_user",
        session_id="test_session",
        last_activity=current_time,
        exp=far_future
    )

    assert sm.should_refresh_token(token_data_far) == False
    print("✓ Token refresh threshold works correctly")


def test_get_session_info():
    """Verify session info retrieval."""
    sm = SessionManager()

    # Create session
    sm.create_session("test_user")
    session_id = list(sm.sessions.keys())[0]

    # Get session info
    info = sm.get_session_info(session_id)
    assert info is not None
    assert "remaining_minutes" in info
    assert "remaining_seconds" in info
    assert "expires_at" in info
    assert info["username"] == "test_user"
    print("✓ Session info retrieval works")


def test_get_session_status():
    """Verify session status endpoint."""
    sm = SessionManager()

    # Create session
    sm.create_session("test_user")
    session_id = list(sm.sessions.keys())[0]

    # Get status
    status = sm.get_session_status(session_id)
    assert status is not None
    assert status["is_active"] == True
    assert status["is_expired"] == False
    assert "remaining_seconds" in status
    print("✓ Session status endpoint works")


def test_end_session():
    """Verify session ending."""
    sm = SessionManager()

    # Create session
    sm.create_session("test_user")
    session_id = list(sm.sessions.keys())[0]

    # End session
    sm.end_session(session_id)

    # Session should be inactive
    assert sm.sessions[session_id]["is_active"] == False
    print("✓ Session ending works")


def test_update_session_activity():
    """Verify session activity updates."""
    sm = SessionManager()

    # Create session
    sm.create_session("test_user")
    session_id = list(sm.sessions.keys())[0]

    initial_activity = sm.sessions[session_id]["last_activity"]

    # Wait a bit
    time.sleep(0.1)

    # Update activity
    sm._update_session_activity(session_id)

    # Activity should be updated
    assert sm.sessions[session_id]["last_activity"] > initial_activity
    print("✓ Session activity updates work")


def test_cleanup_expired_sessions():
    """Verify expired session cleanup."""
    sm = SessionManager()
    original_timeout = sm.timeout_minutes
    sm.timeout_minutes = 0.01  # 0.6 seconds

    try:
        # Create sessions
        sm.create_session("user1")
        sm.create_session("user2")

        # Get session IDs
        session_ids = list(sm.sessions.keys())

        # Wait for timeout
        time.sleep(0.7)

        # Manually mark as expired by updating last_activity to old value
        for session_id in session_ids:
            sm.sessions[session_id]["last_activity"] = int(time.time()) - 1000

        # Cleanup
        sm.cleanup_expired_sessions()

        # All sessions should be inactive
        for session_id, session_data in sm.sessions.items():
            assert session_data["is_active"] == False
        print("✓ Expired session cleanup works")
    finally:
        sm.timeout_minutes = original_timeout


def test_invalid_token_verification():
    """Verify invalid tokens are rejected."""
    sm = SessionManager()

    # Try to verify garbage token
    result = sm.verify_token("invalid_token")
    assert result is None

    # Try to verify non-existent session
    data = {"sub": "test", "session_id": "nonexistent", "last_activity": int(time.time())}
    token = sm.create_access_token(data)
    result = sm.verify_token(token)
    assert result is None
    print("✓ Invalid token rejection works")


def test_refresh_with_expired_refresh_token():
    """Verify expired refresh tokens are rejected."""
    sm = SessionManager()
    original_expiry = sm.refresh_token_expiry_days
    sm.refresh_token_expiry_days = 0.0001  # Very short expiry for testing

    try:
        # Create session
        result = sm.create_full_session("test_user")
        refresh_token = result["refresh_token"]

        # Wait for expiry
        time.sleep(0.5)

        # Try to refresh
        new_token = sm.refresh_with_refresh_token(refresh_token)
        assert new_token is None
        print("✓ Expired refresh token rejection works")
    finally:
        sm.refresh_token_expiry_days = original_expiry


def test_refresh_with_inactive_session():
    """Verify refresh fails for inactive session."""
    sm = SessionManager()

    # Create session
    result = sm.create_full_session("test_user")
    session_id = result["session_id"]
    refresh_token = result["refresh_token"]

    # End session
    sm.end_session(session_id)

    # Try to refresh
    new_token = sm.refresh_with_refresh_token(refresh_token)
    assert new_token is None
    print("✓ Inactive session refresh rejection works")


def run_all_tests():
    """Run all backend session tests."""
    print("\n" + "="*60)
    print("Backend Session Management Tests (Feature #137)")
    print("="*60 + "\n")

    tests = [
        ("Session Manager Init", test_session_manager_init),
        ("Create Access Token", test_create_access_token),
        ("Create Refresh Token", test_create_refresh_token),
        ("Create Full Session", test_create_full_session),
        ("Verify Token", test_verify_token),
        ("Session Activity Timeout", test_session_activity_timeout),
        ("Refresh Token", test_refresh_token),
        ("Refresh With Refresh Token", test_refresh_with_refresh_token),
        ("Should Refresh Token", test_should_refresh_token),
        ("Get Session Info", test_get_session_info),
        ("Get Session Status", test_get_session_status),
        ("End Session", test_end_session),
        ("Update Session Activity", test_update_session_activity),
        ("Cleanup Expired Sessions", test_cleanup_expired_sessions),
        ("Invalid Token Rejection", test_invalid_token_verification),
        ("Expired Refresh Token Rejection", test_refresh_with_expired_refresh_token),
        ("Inactive Session Refresh Rejection", test_refresh_with_inactive_session),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"✗ {name}: {str(e)}")
            failed += 1
        except Exception as e:
            print(f"✗ {name}: Unexpected error - {str(e)}")
            failed += 1

    print("\n" + "="*60)
    print(f"Results: {passed} passed, {failed} failed out of {passed + failed} tests")
    print("="*60 + "\n")

    return failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    if success:
        print("✅ All backend session tests passed!")
    else:
        print("❌ Some tests failed")
        exit(1)
