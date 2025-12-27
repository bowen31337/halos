"""Test session timeout management and authentication features.

Tests for Feature #136: Session management handles timeout correctly
"""

import time
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.session import session_manager, TokenData
from src.core.config import settings


class TestSessionTimeout:
    """Test session timeout management functionality."""

    @pytest.mark.asyncio
    async def test_session_timeout_config(self):
        """Test that session timeout configuration is correct."""
        assert session_manager.timeout_minutes == settings.access_token_expire_minutes
        assert session_manager.refresh_buffer_minutes == 5
        assert session_manager.refresh_token_expiry_days == 7

    @pytest.mark.asyncio
    async def test_create_session(self):
        """Test creating a new session."""
        username = "test_user"
        access_token = session_manager.create_session(username)

        # Verify token was created
        assert access_token is not None
        assert access_token.startswith("eyJ")  # JWT token format

        # Verify session exists
        session_id = None
        for sid, data in session_manager.sessions.items():
            if data.get("username") == username:
                session_id = sid
                break

        assert session_id is not None
        assert session_manager.sessions[session_id]["is_active"] is True

    @pytest.mark.asyncio
    async def test_create_full_session(self):
        """Test creating a session with both access and refresh tokens."""
        username = "test_user_full"
        tokens = session_manager.create_full_session(username)

        # Verify both tokens were created
        assert "access_token" in tokens
        assert "refresh_token" in tokens
        assert "session_id" in tokens
        assert tokens["access_token"].startswith("eyJ")
        assert tokens["refresh_token"].startswith("refresh_")

        # Verify session data
        session_id = tokens["session_id"]
        assert session_id in session_manager.sessions
        assert session_manager.sessions[session_id]["refresh_token"] == tokens["refresh_token"]

    @pytest.mark.asyncio
    async def test_verify_token(self):
        """Test token verification."""
        username = "test_verify"
        access_token = session_manager.create_session(username)

        # Verify valid token
        token_data = session_manager.verify_token(access_token)
        assert token_data is not None
        assert token_data.username == username
        assert token_data.session_id is not None

    @pytest.mark.asyncio
    async def test_session_timeout(self):
        """Test session timeout after inactivity."""
        # Create session with short timeout for testing
        original_timeout = session_manager.timeout_minutes
        session_manager.timeout_minutes = 0.01  # 0.01 minutes = 0.6 seconds

        username = "test_timeout"
        access_token = session_manager.create_session(username)

        # Get session ID
        session_id = None
        for sid, data in session_manager.sessions.items():
            if data.get("username") == username:
                session_id = sid
                break

        # Verify session is active
        assert session_manager._is_session_active(session_id, int(time.time())) is True

        # Wait for timeout
        time.sleep(0.7)  # Wait longer than timeout

        # Verify session is no longer active
        last_activity = session_manager.sessions[session_id]["last_activity"]
        assert session_manager._is_session_active(session_id, last_activity) is False

        # Restore original timeout
        session_manager.timeout_minutes = original_timeout

    @pytest.mark.asyncio
    async def test_refresh_with_refresh_token(self):
        """Test refreshing access token using refresh token."""
        import time
        username = "test_refresh"
        tokens = session_manager.create_full_session(username)

        # Get original access token
        original_token = tokens["access_token"]

        # Wait to ensure different timestamp
        time.sleep(0.01)

        # Refresh using refresh token
        new_access_token = session_manager.refresh_with_refresh_token(tokens["refresh_token"])

        # Verify new token was created
        assert new_access_token is not None
        assert new_access_token.startswith("eyJ")

    @pytest.mark.asyncio
    async def test_get_session_status(self):
        """Test getting detailed session status."""
        username = "test_status"
        tokens = session_manager.create_full_session(username)

        status = session_manager.get_session_status(tokens["session_id"])

        assert status is not None
        assert status["is_active"] is True
        assert status["is_expired"] is False
        assert status["username"] == username
        assert "remaining_seconds" in status
        assert "expires_at" in status

    @pytest.mark.asyncio
    async def test_end_session(self):
        """Test ending a session."""
        username = "test_end"
        tokens = session_manager.create_full_session(username)

        # End the session
        session_manager.end_session(tokens["session_id"])

        # Verify session is inactive
        session_data = session_manager.sessions[tokens["session_id"]]
        assert session_data["is_active"] is False


class TestAuthAPI:
    """Test authentication API endpoints."""

    @pytest.mark.asyncio
    async def test_login_endpoint(self, client: AsyncClient):
        """Test login endpoint returns access and refresh tokens."""
        response = await client.post(
            "/api/auth/login",
            data={"username": "testuser", "password": "testpass"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert "session_id" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data

    @pytest.mark.asyncio
    async def test_register_endpoint(self, client: AsyncClient):
        """Test register endpoint."""
        response = await client.post(
            "/api/auth/register",
            data={"username": "newuser", "password": "newpass"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    @pytest.mark.asyncio
    async def test_refresh_token_endpoint(self, client: AsyncClient):
        """Test refresh token endpoint."""
        import asyncio
        # First login to get tokens
        login_response = await client.post(
            "/api/auth/login",
            data={"username": "testuser", "password": "testpass"}
        )
        login_data = login_response.json()

        # Wait to ensure different timestamp
        await asyncio.sleep(0.01)

        # Refresh using refresh token
        refresh_response = await client.post(
            "/api/auth/refresh",
            json={"refresh_token": login_data["refresh_token"]}
        )

        assert refresh_response.status_code == 200
        data = refresh_response.json()
        assert "access_token" in data

    @pytest.mark.asyncio
    async def test_logout_endpoint(self, client: AsyncClient):
        """Test logout endpoint."""
        # First login
        login_response = await client.post(
            "/api/auth/login",
            data={"username": "testuser", "password": "testpass"}
        )
        login_data = login_response.json()

        # Logout
        logout_response = await client.post(
            "/api/auth/logout",
            headers={"Authorization": f"Bearer {login_data['access_token']}"}
        )

        assert logout_response.status_code == 200
        assert logout_response.json()["message"] == "Logout successful"

    @pytest.mark.asyncio
    async def test_me_endpoint(self, client: AsyncClient):
        """Test get current user endpoint."""
        # First login
        login_response = await client.post(
            "/api/auth/login",
            data={"username": "testuser", "password": "testpass"}
        )
        login_data = login_response.json()

        # Get user info
        me_response = await client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {login_data['access_token']}"}
        )

        assert me_response.status_code == 200
        data = me_response.json()
        assert data["username"] == "testuser"
        assert "session_info" in data

    @pytest.mark.asyncio
    async def test_session_status_endpoint(self, client: AsyncClient):
        """Test session status endpoint."""
        # First login
        login_response = await client.post(
            "/api/auth/login",
            data={"username": "testuser", "password": "testpass"}
        )
        login_data = login_response.json()

        # Check session status
        status_response = await client.get(
            "/api/auth/session/status",
            headers={"Authorization": f"Bearer {login_data['access_token']}"}
        )

        assert status_response.status_code == 200
        data = status_response.json()
        assert data["is_active"] is True
        assert data["is_expired"] is False
        assert "remaining_seconds" in data

    @pytest.mark.asyncio
    async def test_keep_alive_endpoint(self, client: AsyncClient):
        """Test keep-alive endpoint."""
        # First login
        login_response = await client.post(
            "/api/auth/login",
            data={"username": "testuser", "password": "testpass"}
        )
        login_data = login_response.json()

        # Keep session alive
        keep_alive_response = await client.post(
            "/api/auth/session/keep-alive",
            headers={"Authorization": f"Bearer {login_data['access_token']}"}
        )

        assert keep_alive_response.status_code == 200
        data = keep_alive_response.json()
        assert data["message"] == "Session kept alive"

    @pytest.mark.asyncio
    async def test_auth_health_check(self, client: AsyncClient):
        """Test auth health check endpoint."""
        response = await client.get("/api/auth/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "auth_service_healthy"
        assert "sessions_active" in data
        assert "timeout_minutes" in data


class TestSessionLifecycle:
    """Test complete session lifecycle."""

    @pytest.mark.asyncio
    async def test_full_session_lifecycle(self, client: AsyncClient):
        """Test complete session lifecycle: login -> use -> refresh -> logout."""
        # 1. Login
        login_resp = await client.post(
            "/api/auth/login",
            data={"username": "lifecycle_user", "password": "pass"}
        )
        assert login_resp.status_code == 200
        login_data = login_resp.json()
        access_token = login_data["access_token"]
        refresh_token = login_data["refresh_token"]

        # 2. Use access token to get user info
        me_resp = await client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert me_resp.status_code == 200

        # 3. Refresh access token
        refresh_resp = await client.post(
            "/api/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        assert refresh_resp.status_code == 200
        new_access_token = refresh_resp.json()["access_token"]

        # 4. Use new access token
        me_resp_2 = await client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {new_access_token}"}
        )
        assert me_resp_2.status_code == 200

        # 5. Logout
        logout_resp = await client.post(
            "/api/auth/logout",
            headers={"Authorization": f"Bearer {new_access_token}"}
        )
        assert logout_resp.status_code == 200

        # 6. Verify token no longer works
        me_resp_3 = await client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {new_access_token}"}
        )
        assert me_resp_3.status_code == 401


class TestSessionTimeoutEdgeCases:
    """Test edge cases for session timeout."""

    @pytest.mark.asyncio
    async def test_invalid_refresh_token(self, client: AsyncClient):
        """Test that invalid refresh token fails."""
        response = await client.post(
            "/api/auth/refresh",
            json={"refresh_token": "invalid_token"}
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_missing_authorization_header(self, client: AsyncClient):
        """Test that requests without authorization fail."""
        response = await client.get("/api/auth/me")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_invalid_authorization_header(self, client: AsyncClient):
        """Test that requests with invalid authorization fail."""
        response = await client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == 401
