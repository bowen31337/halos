"""Test Sub-agent Delegation Features (Features #63, #64, #65, #95, #185).

This test verifies that:
1. Feature #63: Sub-agent delegation indicator shows when task is delegated
2. Feature #64: Built-in subagents are available (research, code-review, docs, test)
3. Feature #65: Create custom subagent with specific tools and prompt
4. Feature #95: Subagents API manages custom subagent configurations
5. Feature #185: Complete subagent delegation and result integration workflow
"""

import pytest
import asyncio
import json
from uuid import uuid4


@pytest.mark.asyncio
async def test_get_available_subagents(client, test_db):
    """Test that built-in subagents are available via API."""
    response = await client.get("/api/agent/subagents/available")
    assert response.status_code == 200

    data = response.json()
    assert "subagents" in data
    subagents = data["subagents"]

    # Verify all required subagents are present
    subagent_names = [s["name"] for s in subagents]
    assert "research_agent" in subagent_names
    assert "code_review_agent" in subagent_names
    assert "documentation_agent" in subagent_names
    assert "testing_agent" in subagent_names

    # Verify each subagent has required fields
    for subagent in subagents:
        assert "name" in subagent
        assert "description" in subagent
        assert "tools" in subagent


@pytest.mark.asyncio
async def test_create_custom_subagent(client, test_db):
    """Test creating a custom subagent configuration."""
    subagent_data = {
        "name": "custom_analyzer",
        "description": "Analyzes custom patterns",
        "tools": ["pattern_match", "regex_search"],
        "prompt": "You are a pattern analysis specialist."
    }

    response = await client.post(
        "/api/agent/subagents/custom",
        json=subagent_data
    )
    assert response.status_code == 200

    data = response.json()
    assert data["success"] == True
    assert data["subagent"]["name"] == "custom_analyzer"
    assert data["subagent"]["description"] == "Analyzes custom patterns"


@pytest.mark.asyncio
async def test_create_custom_subagent_missing_name(client, test_db):
    """Test that creating subagent without name fails."""
    subagent_data = {
        "description": "No name provided",
        "tools": ["test"],
        "prompt": "Test prompt"
    }

    response = await client.post(
        "/api/agent/subagents/custom",
        json=subagent_data
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_list_custom_subagents(client, test_db):
    """Test listing custom subagents."""
    response = await client.get("/api/agent/subagents/custom")
    assert response.status_code == 200

    data = response.json()
    assert "subagents" in data
    # Should return list (empty or populated)
    assert isinstance(data["subagents"], list)


@pytest.mark.asyncio
async def test_subagent_delegation_stream_events(client, test_db):
    """Test that subagent delegation emits proper SSE events."""
    from src.api.routes.agent import thread_states

    # Create a conversation
    conversation_data = {
        "title": "Test Subagent Delegation",
        "model": "claude-sonnet-4-5-20250929"
    }
    response = await client.post("/api/conversations", json=conversation_data)
    assert response.status_code == 201
    conversation = response.json()
    conversation_id = conversation["id"]

    # Stream with subagent delegation keywords
    thread_id = str(uuid4())
    response = await client.post(
        "/api/agent/stream",
        json={
            "message": "Research the latest AI trends",
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

    # Parse SSE events for subagent delegation
    subagent_start_found = False
    subagent_end_found = False

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
                if current_event == 'subagent_start':
                    subagent_start_found = True
                    data = json.loads(current_data)
                    assert "subagent" in data
                    assert "reason" in data
                elif current_event == 'subagent_end':
                    subagent_end_found = True
                    data = json.loads(current_data)
                    assert "subagent" in data
                    assert "output" in data
            current_event = None
            current_data = None

    # Both events should be present for research delegation
    assert subagent_start_found, "Should emit subagent_start event"
    assert subagent_end_found, "Should emit subagent_end event"


@pytest.mark.asyncio
async def test_subagent_results_endpoint(client, test_db):
    """Test that subagent results are stored and retrievable."""
    from src.api.routes.agent import thread_states

    thread_id = str(uuid4())

    # Manually set up subagent results in thread state
    thread_states[thread_id] = {
        "subagent_results": [
            {
                "subagent": "research_agent",
                "output": "Found relevant information about AI trends"
            },
            {
                "subagent": "code_review_agent",
                "output": "Code looks good with minor suggestions"
            }
        ]
    }

    response = await client.get(f"/api/agent/subagent-results/{thread_id}")
    assert response.status_code == 200

    data = response.json()
    assert data["thread_id"] == thread_id
    assert len(data["subagent_results"]) == 2
    assert data["subagent_results"][0]["subagent"] == "research_agent"

    # Clean up
    del thread_states[thread_id]


@pytest.mark.asyncio
async def test_subagent_workflow_integration(client, test_db):
    """Test complete subagent delegation workflow."""
    from src.api.routes.agent import thread_states

    # Create conversation
    conversation_data = {
        "title": "Test Subagent Workflow",
        "model": "claude-sonnet-4-5-20250929"
    }
    response = await client.post("/api/conversations", json=conversation_data)
    assert response.status_code == 201
    conversation = response.json()
    conversation_id = conversation["id"]

    thread_id = str(uuid4())

    # Stream with code review request
    response = await client.post(
        "/api/agent/stream",
        json={
            "message": "Review this code for bugs",
            "thread_id": thread_id,
            "conversation_id": conversation_id,
            "model": "claude-sonnet-4-5-20250929",
            "permission_mode": "auto"
        }
    )

    assert response.status_code == 200

    # Parse all events
    content = response.content.decode('utf-8')
    lines = content.split('\n')

    events = []
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
                events.append({
                    "event": current_event,
                    "data": json.loads(current_data)
                })
            current_event = None
            current_data = None

    # Verify workflow:
    # 1. Start event
    assert any(e["event"] == "start" for e in events), "Should have start event"

    # 2. Subagent delegation events (mock agent uses test-agent for "test" keyword)
    subagent_events = [e for e in events if e["event"] in ["subagent_start", "subagent_end"]]
    assert len(subagent_events) >= 1, "Should have at least one subagent event"

    # 3. Message streaming
    message_events = [e for e in events if e["event"] == "message"]
    assert len(message_events) > 0, "Should stream message content"

    # 4. Done event
    assert any(e["event"] == "done" for e in events), "Should have done event"

    # Verify thread state has subagent results (if tracked)
    if thread_id in thread_states:
        state = thread_states[thread_id]
        if "subagent_results" in state:
            assert len(state["subagent_results"]) > 0, "Should have subagent results"


@pytest.mark.asyncio
async def test_subagent_different_types(client, test_db):
    """Test that subagent delegation works for different message types."""
    test_cases = [
        "Research the latest trends",
        "Review this code",
        "Investigate the bug",
        "Create tests",
    ]

    for message in test_cases:
        conversation_data = {
            "title": f"Test {message[:20]}",
            "model": "claude-sonnet-4-5-20250929"
        }
        response = await client.post("/api/conversations", json=conversation_data)
        assert response.status_code == 201
        conversation = response.json()
        conversation_id = conversation["id"]

        thread_id = str(uuid4())
        response = await client.post(
            "/api/agent/stream",
            json={
                "message": message,
                "thread_id": thread_id,
                "conversation_id": conversation_id,
                "model": "claude-sonnet-4-5-20250929",
                "permission_mode": "auto"
            }
        )

        content = response.content.decode('utf-8')

        # Verify subagent events are emitted
        assert "subagent_start" in content or "subagent_end" in content, \
               f"Should emit subagent events for: {message}"


@pytest.mark.asyncio
async def test_mock_agent_subagent_events():
    """Test that MockAgent properly emits subagent events."""
    from src.services.mock_agent import MockAgent
    from langchain_core.messages import HumanMessage

    agent = MockAgent()

    # Test research delegation
    input_data = {"messages": [HumanMessage(content="Research AI trends")]}
    config = {"configurable": {"thread_id": str(uuid4()), "permission_mode": "auto"}}

    events = []
    async for event in agent.astream_events(input_data, config, version="v2"):
        events.append(event)

    # Check for subagent events (mock agent uses on_custom_event wrapper)
    subagent_start = [e for e in events if e.get("event") == "on_custom_event" and e.get("name") == "subagent_start"]
    subagent_end = [e for e in events if e.get("event") == "on_custom_event" and e.get("name") == "subagent_end"]

    assert len(subagent_start) > 0, "Should emit subagent_start via on_custom_event"
    assert len(subagent_end) > 0, "Should emit subagent_end via on_custom_event"

    # Verify subagent name exists in data
    if subagent_start:
        start_data = subagent_start[0].get("data", {})
        assert "subagent" in start_data, "Start event should have subagent field"
        assert start_data["subagent"] in ["research-agent", "code-review-agent", "docs-agent", "test-agent"]
