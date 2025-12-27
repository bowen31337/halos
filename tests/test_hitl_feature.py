"""Test Human-in-the-Loop (HITL) approval feature (Features #58, #59, #60, #61).

This test verifies that:
1. Permission mode can be set to 'default' (Feature #61)
2. Agent requests approval for execute tool (Feature #58)
3. Approval dialog appears with tool info
4. User can approve, reject, or edit (Features #58, #59, #60)
"""

import pytest
import asyncio
from uuid import uuid4


@pytest.mark.asyncio
async def test_permission_mode_in_stream_request(client, test_db):
    """Test that permission_mode is passed to stream endpoint."""
    # Create a conversation
    conversation_data = {
        "title": "Test HITL Permission",
        "model": "claude-sonnet-4-5-20250929"
    }
    response = await client.post("/api/conversations", json=conversation_data)
    assert response.status_code == 201
    conversation = response.json()
    conversation_id = conversation["id"]

    # Stream with default permission mode
    thread_id = str(uuid4())
    response = await client.post(
        "/api/agent/stream",
        json={
            "message": "Run a shell command",
            "thread_id": thread_id,
            "conversation_id": conversation_id,
            "model": "claude-sonnet-4-5-20250929",
            "permission_mode": "default"
        }
    )

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_execute_tool_emits_interrupt_event(client, test_db):
    """Test that execute tool in default mode emits interrupt event."""
    from src.api.routes.agent import pending_approvals
    import json

    # Create a conversation
    conversation_data = {
        "title": "Test Execute Interrupt",
        "model": "claude-sonnet-4-5-20250929"
    }
    response = await client.post("/api/conversations", json=conversation_data)
    assert response.status_code == 201
    conversation = response.json()
    conversation_id = conversation["id"]

    # Stream with execute command in default mode
    thread_id = str(uuid4())
    response = await client.post(
        "/api/agent/stream",
        json={
            "message": "Execute: echo hello",
            "thread_id": thread_id,
            "conversation_id": conversation_id,
            "model": "claude-sonnet-4-5-20250929",
            "permission_mode": "default"
        }
    )

    assert response.status_code == 200

    # Read the stream
    content = response.content.decode('utf-8')
    lines = content.split('\n')

    # Parse SSE events for interrupt
    interrupt_found = False
    interrupt_data = None
    current_event = None
    current_data = None

    for line in lines:
        line = line.strip()
        if line.startswith('event:'):
            current_event = line[6:].strip()
        elif line.startswith('data:'):
            current_data = line[5:].strip()
        elif line == '':
            if current_event and current_data:
                if current_event == 'interrupt':
                    interrupt_found = True
                    interrupt_data = json.loads(current_data)
                    break
            current_event = None
            current_data = None

    assert interrupt_found, "Should have emitted interrupt event"
    assert interrupt_data is not None
    assert interrupt_data["tool"] == "execute"
    assert "input" in interrupt_data
    assert "reason" in interrupt_data

    # Verify pending approval was stored
    assert thread_id in pending_approvals
    assert pending_approvals[thread_id]["tool"] == "execute"

    # Clean up
    if thread_id in pending_approvals:
        del pending_approvals[thread_id]


@pytest.mark.asyncio
async def test_approve_interrupt_decision(client, test_db):
    """Test approving an interrupt decision (Feature #58)."""
    from src.api.routes.agent import pending_approvals

    # Create a conversation
    conversation_data = {
        "title": "Test Approve HITL",
        "model": "claude-sonnet-4-5-20250929"
    }
    response = await client.post("/api/conversations", json=conversation_data)
    assert response.status_code == 201
    conversation = response.json()
    conversation_id = conversation["id"]

    # Stream to trigger interrupt
    thread_id = str(uuid4())
    stream_response = await client.post(
        "/api/agent/stream",
        json={
            "message": "Execute: echo test",
            "thread_id": thread_id,
            "conversation_id": conversation_id,
            "model": "claude-sonnet-4-5-20250929",
            "permission_mode": "default"
        }
    )
    stream_response.content  # Consume stream

    # Verify pending approval exists
    assert thread_id in pending_approvals

    # Approve the interrupt
    interrupt_response = await client.post(
        "/api/agent/interrupt",
        json={
            "thread_id": thread_id,
            "decision": "approve"
        }
    )

    assert interrupt_response.status_code == 200
    result = interrupt_response.json()
    assert result["decision"] == "approve"
    assert result["status"] == "resumed"
    assert result["tool"] == "execute"

    # Verify pending approval was cleared
    assert thread_id not in pending_approvals


@pytest.mark.asyncio
async def test_reject_interrupt_decision(client, test_db):
    """Test rejecting an interrupt decision (Feature #60)."""
    from src.api.routes.agent import pending_approvals

    # Create a conversation
    conversation_data = {
        "title": "Test Reject HITL",
        "model": "claude-sonnet-4-5-20250929"
    }
    response = await client.post("/api/conversations", json=conversation_data)
    assert response.status_code == 201
    conversation = response.json()
    conversation_id = conversation["id"]

    # Stream to trigger interrupt
    thread_id = str(uuid4())
    stream_response = await client.post(
        "/api/agent/stream",
        json={
            "message": "Execute: echo test",
            "thread_id": thread_id,
            "conversation_id": conversation_id,
            "model": "claude-sonnet-4-5-20250929",
            "permission_mode": "default"
        }
    )
    stream_response.content  # Consume stream

    # Reject the interrupt
    interrupt_response = await client.post(
        "/api/agent/interrupt",
        json={
            "thread_id": thread_id,
            "decision": "reject"
        }
    )

    assert interrupt_response.status_code == 200
    result = interrupt_response.json()
    assert result["decision"] == "reject"
    assert result["status"] == "rejected"
    assert result["tool"] == "execute"

    # Verify pending approval was cleared
    assert thread_id not in pending_approvals


@pytest.mark.asyncio
async def test_edit_interrupt_decision(client, test_db):
    """Test editing tool input in interrupt decision (Feature #59)."""
    from src.api.routes.agent import pending_approvals

    # Create a conversation
    conversation_data = {
        "title": "Test Edit HITL",
        "model": "claude-sonnet-4-5-20250929"
    }
    response = await client.post("/api/conversations", json=conversation_data)
    assert response.status_code == 201
    conversation = response.json()
    conversation_id = conversation["id"]

    # Stream to trigger interrupt
    thread_id = str(uuid4())
    stream_response = await client.post(
        "/api/agent/stream",
        json={
            "message": "Execute: echo test",
            "thread_id": thread_id,
            "conversation_id": conversation_id,
            "model": "claude-sonnet-4-5-20250929",
            "permission_mode": "default"
        }
    )
    stream_response.content  # Consume stream

    # Edit and approve the interrupt
    edited_input = {"command": "echo 'edited command'"}
    interrupt_response = await client.post(
        "/api/agent/interrupt",
        json={
            "thread_id": thread_id,
            "decision": "edit",
            "edited_input": edited_input
        }
    )

    assert interrupt_response.status_code == 200
    result = interrupt_response.json()
    assert result["decision"] == "edit"
    assert result["status"] == "resumed"
    assert result["edited_input"] == edited_input

    # Verify pending approval was cleared
    assert thread_id not in pending_approvals


@pytest.mark.asyncio
async def test_auto_mode_no_interrupt(client, test_db):
    """Test that auto permission mode doesn't trigger interrupts."""
    from src.api.routes.agent import pending_approvals

    # Create a conversation
    conversation_data = {
        "title": "Test Auto Mode",
        "model": "claude-sonnet-4-5-20250929"
    }
    response = await client.post("/api/conversations", json=conversation_data)
    assert response.status_code == 201
    conversation = response.json()
    conversation_id = conversation["id"]

    # Stream with execute command in auto mode
    thread_id = str(uuid4())
    response = await client.post(
        "/api/agent/stream",
        json={
            "message": "Execute: echo hello",
            "thread_id": thread_id,
            "conversation_id": conversation_id,
            "model": "claude-sonnet-4-5-20250929",
            "permission_mode": "auto"
        }
    )

    assert response.status_code == 200

    # Read the stream
    content = response.content.decode('utf-8')
    lines = content.split('\n')

    # Check for interrupt event
    has_interrupt = any('event: interrupt' in line for line in lines)

    # In auto mode, should NOT have interrupt
    assert not has_interrupt, "Should NOT emit interrupt event in auto mode"

    # Verify no pending approval
    assert thread_id not in pending_approvals


@pytest.mark.asyncio
async def test_pending_approval_endpoint(client, test_db):
    """Test the pending approval endpoint."""
    from src.api.routes.agent import pending_approvals

    # Create a conversation
    conversation_data = {
        "title": "Test Pending Approval",
        "model": "claude-sonnet-4-5-20250929"
    }
    response = await client.post("/api/conversations", json=conversation_data)
    assert response.status_code == 201
    conversation = response.json()
    conversation_id = conversation["id"]

    # Stream to trigger interrupt
    thread_id = str(uuid4())
    stream_response = await client.post(
        "/api/agent/stream",
        json={
            "message": "Execute: echo test",
            "thread_id": thread_id,
            "conversation_id": conversation_id,
            "model": "claude-sonnet-4-5-20250929",
            "permission_mode": "default"
        }
    )
    stream_response.content  # Consume stream

    # Get pending approval
    approval_response = await client.get(f"/api/agent/pending-approval/{thread_id}")
    assert approval_response.status_code == 200

    approval = approval_response.json()
    assert approval["thread_id"] == thread_id
    assert approval["tool"] == "execute"
    assert "input" in approval
    assert "reason" in approval

    # Clean up
    if thread_id in pending_approvals:
        del pending_approvals[thread_id]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
