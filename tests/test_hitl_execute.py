"""Test Human-in-the-Loop (HITL) approval for execute tool.

This test verifies that:
1. Execute tool triggers interrupt event in default permission mode
2. Approval dialog displays tool name and command
3. User can approve/reject the execution
4. Execution continues after approval
"""

import pytest
import asyncio
from uuid import uuid4


@pytest.mark.asyncio
async def test_execute_tool_interrupts_in_default_mode(client, test_db):
    """Test that execute tool triggers interrupt in default permission mode."""
    from src.api.routes.agent import thread_states
    import json

    # Create a conversation
    conversation_data = {
        "title": "Test HITL Execute",
        "model": "claude-sonnet-4-5-20250929"
    }
    response = await client.post("/api/conversations", json=conversation_data)
    assert response.status_code == 201
    conversation = response.json()
    conversation_id = conversation["id"]

    # Stream with a message that triggers execute tool
    thread_id = str(uuid4())
    response = await client.post(
        "/api/agent/stream",
        json={
            "message": "Execute the command: echo 'hello world'",
            "thread_id": thread_id,
            "conversation_id": conversation_id,
            "model": "claude-sonnet-4-5-20250929",
            "permission_mode": "default"  # This should trigger interrupt
        }
    )

    assert response.status_code == 200

    # Read the stream to find interrupt event
    interrupt_found = False
    interrupt_data = None
    current_event = None
    current_data = None

    async for chunk in response.aiter_text():
        lines = chunk.split('\n')
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
        if interrupt_found:
            break

    assert interrupt_found, "Should have emitted interrupt event"
    assert interrupt_data is not None
    assert interrupt_data["tool"] == "execute"
    assert "command" in interrupt_data["input"]
    assert "reason" in interrupt_data


@pytest.mark.asyncio
async def test_execute_tool_no_interrupt_in_bypass_mode(client, test_db):
    """Test that execute tool does NOT trigger interrupt in bypass mode."""
    import json

    # Create a conversation
    conversation_data = {
        "title": "Test HITL Bypass",
        "model": "claude-sonnet-4-5-20250929"
    }
    response = await client.post("/api/conversations", json=conversation_data)
    assert response.status_code == 201
    conversation = response.json()
    conversation_id = conversation["id"]

    # Stream with a message that triggers execute tool
    thread_id = str(uuid4())
    response = await client.post(
        "/api/agent/stream",
        json={
            "message": "Execute the command: echo 'hello world'",
            "thread_id": thread_id,
            "conversation_id": conversation_id,
            "model": "claude-sonnet-4-5-20250929",
            "permission_mode": "bypassPermissions"  # This should NOT trigger interrupt
        }
    )

    assert response.status_code == 200

    # Read the stream - should NOT have interrupt event
    interrupt_found = False
    current_event = None
    current_data = None

    async for chunk in response.aiter_text():
        lines = chunk.split('\n')
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
                        break
                current_event = None
                current_data = None
        if interrupt_found:
            break

    assert not interrupt_found, "Should NOT have emitted interrupt event in bypass mode"


@pytest.mark.asyncio
async def test_interrupt_endpoint(client, test_db):
    """Test the /api/agent/interrupt endpoint for handling approval decisions."""
    from src.api.routes.agent import pending_approvals

    # Create a conversation
    conversation_data = {
        "title": "Test Interrupt Endpoint",
        "model": "claude-sonnet-4-5-20250929"
    }
    response = await client.post("/api/conversations", json=conversation_data)
    assert response.status_code == 201

    # Simulate a pending approval
    thread_id = str(uuid4())
    pending_approvals[thread_id] = {
        "tool": "execute",
        "input": {"command": "echo 'test'"},
        "reason": "Test approval"
    }

    # Test approve
    response = await client.post(
        "/api/agent/interrupt",
        json={
            "thread_id": thread_id,
            "decision": "approve"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["decision"] == "approve"
    assert data["status"] == "resumed"
    assert thread_id not in pending_approvals

    # Test reject
    pending_approvals[thread_id] = {
        "tool": "execute",
        "input": {"command": "echo 'test'"},
        "reason": "Test approval"
    }
    response = await client.post(
        "/api/agent/interrupt",
        json={
            "thread_id": thread_id,
            "decision": "reject"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["decision"] == "reject"
    assert data["status"] == "rejected"

    # Test edit
    pending_approvals[thread_id] = {
        "tool": "execute",
        "input": {"command": "echo 'test'"},
        "reason": "Test approval"
    }
    response = await client.post(
        "/api/agent/interrupt",
        json={
            "thread_id": thread_id,
            "decision": "edit",
            "edited_input": {"command": "echo 'edited'"}
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["decision"] == "edit"
    assert data["status"] == "resumed"
    assert data["edited_input"]["command"] == "echo 'edited'"


@pytest.mark.asyncio
async def test_pending_approval_endpoint(client, test_db):
    """Test the /api/agent/pending-approval/{thread_id} endpoint."""
    from src.api.routes.agent import pending_approvals

    thread_id = str(uuid4())

    # Test when no pending approval
    response = await client.get(f"/api/agent/pending-approval/{thread_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["pending"] == False

    # Test when there is a pending approval
    pending_approvals[thread_id] = {
        "tool": "execute",
        "input": {"command": "echo 'test'"},
        "reason": "Test approval"
    }

    response = await client.get(f"/api/agent/pending-approval/{thread_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["pending"] == True
    assert data["tool"] == "execute"
    assert data["input"]["command"] == "echo 'test'"
    assert data["reason"] == "Test approval"

    # Clean up
    del pending_approvals[thread_id]


@pytest.mark.asyncio
async def test_get_agent_state_endpoint(client, test_db):
    """Test the /api/agent/state/{thread_id} endpoint."""
    from src.api.routes.agent import thread_states

    thread_id = str(uuid4())

    # Test when thread doesn't exist
    response = await client.get(f"/api/agent/state/{thread_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["state"] is None

    # Test when thread exists with state
    thread_states[thread_id] = {
        "todos": [{"id": "1", "content": "Test", "status": "pending"}],
        "files": [{"id": "2", "name": "test.py"}]
    }

    response = await client.get(f"/api/agent/state/{thread_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["state"]["todos"] == [{"id": "1", "content": "Test", "status": "pending"}]
    assert data["state"]["files"] == [{"id": "2", "name": "test.py"}]

    # Clean up
    del thread_states[thread_id]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
