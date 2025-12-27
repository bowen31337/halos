"""Test Feature #100: Audit logging captures important user actions.

This test verifies that the audit logging system properly captures
important user actions with timestamps, user IDs, resource information,
and tool decisions for HITL scenarios.
"""

import pytest
import asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import select

from src.main import app
from src.core.database import get_db, Base
from src.models.audit_log import AuditLog, AuditActionType
from src.utils.audit import (
    log_audit,
    log_tool_decision,
    log_conversation_action,
    log_project_action,
    log_agent_invocation,
    get_audit_logs,
    get_request_info,
)


# Test database setup
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def test_db():
    """Create a test database with tables."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        yield session

    await engine.dispose()


@pytest.fixture
async def client(test_db):
    """Create an HTTP client with test database override."""

    async def override_get_db():
        yield test_db

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_audit_log_model_creation(test_db):
    """Test that AuditLog model can be created with all fields."""
    from uuid import uuid4

    audit_log = AuditLog(
        user_id="test_user_123",
        action=AuditActionType.CONVERSATION_CREATE,
        resource_type="conversation",
        resource_id=str(uuid4()),
        tool_name="test_tool",
        tool_decision="approve",
        details={"test": "data"},
        ip_address="127.0.0.1",
        user_agent="test-agent/1.0",
    )

    test_db.add(audit_log)
    await test_db.commit()
    await test_db.refresh(audit_log)

    # Verify fields
    assert audit_log.user_id == "test_user_123"
    assert audit_log.action == AuditActionType.CONVERSATION_CREATE
    assert audit_log.resource_type == "conversation"
    assert audit_log.tool_name == "test_tool"
    assert audit_log.tool_decision == "approve"
    assert audit_log.details == {"test": "data"}
    assert audit_log.ip_address == "127.0.0.1"
    assert audit_log.user_agent == "test-agent/1.0"
    assert audit_log.created_at is not None

    # Test to_dict method
    log_dict = audit_log.to_dict()
    assert log_dict["user_id"] == "test_user_123"
    assert log_dict["action"] == "conversation_create"
    assert "id" in log_dict
    assert "created_at" in log_dict


@pytest.mark.asyncio
async def test_log_audit_function(test_db):
    """Test the log_audit utility function."""
    from uuid import uuid4

    user_id = "test_user_456"
    action = AuditActionType.CONVERSATION_CREATE
    resource_type = "conversation"
    resource_id = str(uuid4())

    audit_log = await log_audit(
        db=test_db,
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details={"message": "test message"},
        ip_address="192.168.1.1",
        user_agent="Mozilla/5.0",
    )

    assert audit_log.user_id == user_id
    assert audit_log.action == action
    assert audit_log.resource_type == resource_type
    assert audit_log.resource_id == resource_id
    assert audit_log.details == {"message": "test message"}
    assert audit_log.ip_address == "192.168.1.1"
    assert audit_log.user_agent == "Mozilla/5.0"


@pytest.mark.asyncio
async def test_log_tool_decision(test_db):
    """Test logging HITL tool decisions."""
    audit_log = await log_tool_decision(
        db=test_db,
        user_id="user_123",
        tool_name="file_editor",
        decision="approve",
        details={"file": "test.py", "changes": 5},
        ip_address="10.0.0.1",
        user_agent="test-client",
    )

    assert audit_log.user_id == "user_123"
    assert audit_log.tool_name == "file_editor"
    assert audit_log.tool_decision == "approve"
    assert audit_log.action == AuditActionType.AGENT_INTERRUPT_APPROVE
    assert audit_log.details["file"] == "test.py"


@pytest.mark.asyncio
async def test_log_conversation_action(test_db):
    """Test logging conversation actions."""
    from uuid import uuid4

    conversation_id = str(uuid4())

    audit_log = await log_conversation_action(
        db=test_db,
        user_id="user_789",
        action=AuditActionType.CONVERSATION_UPDATE,
        conversation_id=conversation_id,
        details={"title": "My Conversation"},
    )

    assert audit_log.user_id == "user_789"
    assert audit_log.action == AuditActionType.CONVERSATION_UPDATE
    assert audit_log.resource_type == "conversation"
    assert audit_log.resource_id == conversation_id
    assert audit_log.details["title"] == "My Conversation"


@pytest.mark.asyncio
async def test_log_project_action(test_db):
    """Test logging project actions."""
    from uuid import uuid4

    project_id = str(uuid4())

    audit_log = await log_project_action(
        db=test_db,
        user_id="user_abc",
        action=AuditActionType.PROJECT_FILE_UPLOAD,
        project_id=project_id,
        details={"filename": "main.py", "size": 1024},
    )

    assert audit_log.user_id == "user_abc"
    assert audit_log.action == AuditActionType.PROJECT_FILE_UPLOAD
    assert audit_log.resource_type == "project"
    assert audit_log.resource_id == project_id
    assert audit_log.details["filename"] == "main.py"


@pytest.mark.asyncio
async def test_log_agent_invocation(test_db):
    """Test logging agent invocations."""
    from uuid import uuid4

    conversation_id = str(uuid4())

    audit_log = await log_agent_invocation(
        db=test_db,
        user_id="user_xyz",
        conversation_id=conversation_id,
        model="claude-sonnet-4-5-20250929",
        details={"thread_id": "thread_123", "temperature": 0.7},
        ip_address="203.0.113.1",
        user_agent="WebClient/1.0",
    )

    assert audit_log.user_id == "user_xyz"
    assert audit_log.action == AuditActionType.AGENT_INVOKE
    assert audit_log.resource_type == "conversation"
    assert audit_log.resource_id == conversation_id
    assert audit_log.details["model"] == "claude-sonnet-4-5-20250929"
    assert audit_log.details["thread_id"] == "thread_123"
    assert audit_log.ip_address == "203.0.113.1"


@pytest.mark.asyncio
async def test_get_audit_logs(test_db):
    """Test querying audit logs with filters."""
    from uuid import uuid4

    # Create test audit logs
    user_id = "filter_test_user"
    conversation_id = str(uuid4())

    # Create multiple logs
    await log_audit(
        db=test_db,
        user_id=user_id,
        action=AuditActionType.CONVERSATION_CREATE,
        resource_type="conversation",
        resource_id=conversation_id,
    )

    await log_audit(
        db=test_db,
        user_id=user_id,
        action=AuditActionType.CONVERSATION_UPDATE,
        resource_type="conversation",
        resource_id=conversation_id,
    )

    await log_audit(
        db=test_db,
        user_id="other_user",
        action=AuditActionType.PROJECT_CREATE,
        resource_type="project",
        resource_id=str(uuid4()),
    )

    # Query by user_id
    logs = await get_audit_logs(db=test_db, user_id=user_id)
    assert len(logs) == 2
    assert all(log.user_id == user_id for log in logs)

    # Query by action
    logs = await get_audit_logs(
        db=test_db,
        action=AuditActionType.CONVERSATION_CREATE
    )
    assert len(logs) >= 1
    assert logs[0].action == AuditActionType.CONVERSATION_CREATE

    # Query by resource_type
    logs = await get_audit_logs(db=test_db, resource_type="conversation")
    assert len(logs) >= 2

    # Test limit and offset
    logs = await get_audit_logs(db=test_db, limit=1, offset=0)
    assert len(logs) <= 1


@pytest.mark.asyncio
async def test_get_request_info():
    """Test extracting IP and user agent from request."""
    from fastapi import Request
    from starlette.datastructures import Headers

    class MockRequest:
        def __init__(self, headers, client_host=None):
            self.headers = Headers(headers)
            self.client = type('obj', (object,), {'host': client_host})() if client_host else None

    # Test with X-Forwarded-For
    request = MockRequest(
        headers={"X-Forwarded-For": "203.0.113.1, 198.51.100.1", "User-Agent": "Mozilla/5.0"},
        client_host="127.0.0.1"
    )
    ip, ua = get_request_info(request)
    assert ip == "203.0.113.1"
    assert ua == "Mozilla/5.0"

    # Test without X-Forwarded-For
    request = MockRequest(
        headers={"User-Agent": "curl/7.68.0"},
        client_host="192.168.1.100"
    )
    ip, ua = get_request_info(request)
    assert ip == "192.168.1.100"
    assert ua == "curl/7.68.0"


@pytest.mark.asyncio
async def test_audit_log_enum_actions():
    """Test that all AuditActionType enum values are valid."""
    # Just verify the enum exists and has expected values
    assert hasattr(AuditActionType, "CONVERSATION_CREATE")
    assert hasattr(AuditActionType, "AGENT_INVOKE")
    assert hasattr(AuditActionType, "AGENT_INTERRUPT_APPROVE")
    assert hasattr(AuditActionType, "AGENT_INTERRUPT_REJECT")
    assert hasattr(AuditActionType, "AGENT_INTERRUPT_EDIT")
    assert hasattr(AuditActionType, "PROJECT_CREATE")
    assert hasattr(AuditActionType, "MEMORY_CREATE")
    assert hasattr(AuditActionType, "FOLDER_CREATE")
    assert hasattr(AuditActionType, "CONVERSATION_SHARE")
    assert hasattr(AuditActionType, "SUBAGENT_DELEGATION")
    assert hasattr(AuditActionType, "TASK_CREATE")
    assert hasattr(AuditActionType, "SETTINGS_UPDATE")
    assert hasattr(AuditActionType, "MCP_SERVER_ADD")
    assert hasattr(AuditActionType, "PROMPT_CREATE")

    # Verify all actions have string values
    for action in AuditActionType:
        assert isinstance(action.value, str)
        assert len(action.value) > 0


@pytest.mark.asyncio
async def test_audit_log_timestamps(test_db):
    """Test that audit logs are created with proper timestamps."""
    from datetime import datetime

    before = datetime.utcnow()

    audit_log = await log_audit(
        db=test_db,
        user_id="timestamp_test",
        action=AuditActionType.CONVERSATION_CREATE,
    )

    after = datetime.utcnow()

    assert audit_log.created_at is not None
    assert before <= audit_log.created_at <= after


@pytest.mark.asyncio
async def test_audit_log_null_fields(test_db):
    """Test that optional fields can be null."""
    # Create log with minimal required fields
    audit_log = AuditLog(
        user_id="minimal_user",
        action=AuditActionType.CONVERSATION_CREATE,
    )
    test_db.add(audit_log)
    await test_db.commit()
    await test_db.refresh(audit_log)

    assert audit_log.resource_type is None
    assert audit_log.resource_id is None
    assert audit_log.tool_name is None
    assert audit_log.tool_decision is None
    assert audit_log.details is None
    assert audit_log.ip_address is None
    assert audit_log.user_agent is None


@pytest.mark.asyncio
async def test_audit_log_indexing(test_db):
    """Test that indexes work correctly for common queries."""
    from uuid import uuid4

    # Create multiple logs with different users
    for i in range(5):
        await log_audit(
            db=test_db,
            user_id=f"user_{i % 2}",  # Two different users
            action=AuditActionType.CONVERSATION_CREATE,
            resource_type="conversation",
            resource_id=str(uuid4()),
        )

    # Query by user_id should be efficient (uses index)
    result = await test_db.execute(
        select(AuditLog).where(AuditLog.user_id == "user_0")
    )
    logs = result.scalars().all()
    assert len(logs) >= 2

    # Query by resource_id should be efficient (uses index)
    test_id = str(uuid4())
    await log_audit(
        db=test_db,
        user_id="test",
        action=AuditActionType.CONVERSATION_CREATE,
        resource_type="conversation",
        resource_id=test_id,
    )

    result = await test_db.execute(
        select(AuditLog).where(AuditLog.resource_id == test_id)
    )
    logs = result.scalars().all()
    assert len(logs) == 1
    assert logs[0].resource_id == test_id


@pytest.mark.asyncio
async def test_audit_log_ordering(test_db):
    """Test that audit logs are returned in chronological order."""
    user_id = "ordering_test"

    for i in range(3):
        audit_log = await log_audit(
            db=test_db,
            user_id=user_id,
            action=AuditActionType.CONVERSATION_CREATE,
        )
        await test_db.commit()
        if i < 2:
            await asyncio.sleep(0.01)  # Small delay to ensure different timestamps

    # Query logs
    logs = await get_audit_logs(db=test_db, user_id=user_id)

    # Should be in descending order by created_at
    assert len(logs) == 3
    assert logs[0].created_at >= logs[1].created_at >= logs[2].created_at


@pytest.mark.asyncio
async def test_audit_api_endpoints(client, test_db):
    """Test the audit API endpoints."""
    from uuid import uuid4

    # First, create some audit logs directly
    await log_audit(
        db=test_db,
        user_id="api_test_user",
        action=AuditActionType.CONVERSATION_CREATE,
        resource_type="conversation",
        resource_id=str(uuid4()),
        details={"test": True},
    )
    await test_db.commit()

    # Test GET /api/audit
    response = await client.get("/api/audit")
    assert response.status_code == 200
    data = response.json()
    assert "logs" in data
    assert "count" in data

    # Test GET /api/audit/stats
    response = await client.get("/api/audit/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "by_action" in data

    # Test GET /api/audit/actions
    response = await client.get("/api/audit/actions")
    assert response.status_code == 200
    data = response.json()
    assert "actions" in data
    assert "conversation_create" in data["actions"]

    # Test GET /api/audit/user/{user_id}
    response = await client.get("/api/audit/user/api_test_user")
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == "api_test_user"
    assert len(data["logs"]) >= 1

    # Test filtering
    response = await client.get("/api/audit?action=conversation_create")
    assert response.status_code == 200
    data = response.json()
    assert all(log["action"] == "conversation_create" for log in data["logs"])


@pytest.mark.asyncio
async def test_conversation_create_audit_logging(client, test_db):
    """Test that creating a conversation via API creates an audit log."""
    # Create a conversation
    response = await client.post(
        "/api/conversations",
        json={"title": "Audit Test Conversation", "model": "claude-sonnet"}
    )
    assert response.status_code == 201
    conv_data = response.json()
    conv_id = conv_data["id"]

    # Query audit logs for this conversation
    result = await test_db.execute(
        select(AuditLog).where(
            AuditLog.action == AuditActionType.CONVERSATION_CREATE
        ).where(AuditLog.resource_id == conv_id)
    )
    audit_logs = result.scalars().all()

    assert len(audit_logs) >= 1, "No audit log found for created conversation"

    log = audit_logs[0]
    assert log.action == AuditActionType.CONVERSATION_CREATE
    assert log.resource_type == "conversation"
    assert log.resource_id == conv_id
    assert log.details["title"] == "Audit Test Conversation"
    assert log.details["model"] == "claude-sonnet"
    assert log.ip_address is not None
    assert log.user_agent is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
