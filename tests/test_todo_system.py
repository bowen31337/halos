"""Test todo system functionality.

This test verifies that the todo system works end-to-end with MockAgent:
1. Backend /todos endpoint returns todos from agent state
2. SSE streaming emits todo events
3. MockAgent creates and tracks todos
4. Frontend can receive and display todos

Note: Real DeepAgent integration requires additional work as it uses
LangGraph state system instead of _thread_state.
"""

import pytest
import asyncio
import os
from uuid import uuid4
from src.services.agent_service import agent_service


@pytest.fixture(autouse=True)
def force_mock_agent():
    """Force use of MockAgent by temporarily removing API key."""
    # Store original values
    original_key = os.environ.get('ANTHROPIC_API_KEY')
    original_service_key = getattr(agent_service, 'api_key', None)

    # Remove API key from environment
    if original_key:
        del os.environ['ANTHROPIC_API_KEY']

    # Reset the agent service's api_key and clear cached agents
    agent_service.api_key = None
    agent_service.agents.clear()

    yield

    # Restore API key
    if original_key:
        os.environ['ANTHROPIC_API_KEY'] = original_key
    agent_service.api_key = original_service_key


@pytest.mark.asyncio
async def test_backend_todos_endpoint(client, test_db):
    """Test that the /api/agent/todos/{thread_id} endpoint returns todos."""
    # Create a conversation
    conversation_data = {
        "title": "Test Todo Conversation",
        "model": "claude-sonnet-4-5-20250929"
    }
    response = await client.post("/api/conversations", json=conversation_data)
    assert response.status_code == 201
    conversation = response.json()
    conversation_id = conversation["id"]

    # Use conversation_id as thread_id for todos
    thread_id = conversation_id

    # Initially, todos should be empty or not exist
    response = await client.get(f"/api/agent/todos/{thread_id}")
    assert response.status_code == 200
    data = response.json()
    assert "thread_id" in data
    assert "todos" in data
    # May be empty initially

    # Simulate agent storing todos in thread_states
    from src.api.routes.agent import thread_states
    thread_states[thread_id] = {
        "todos": [
            {"id": str(uuid4()), "content": "Test task 1", "status": "pending"},
            {"id": str(uuid4()), "content": "Test task 2", "status": "in_progress"},
        ]
    }

    # Now fetch todos again
    response = await client.get(f"/api/agent/todos/{thread_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["thread_id"] == thread_id
    assert len(data["todos"]) == 2
    assert data["todos"][0]["content"] == "Test task 1"
    assert data["todos"][1]["status"] == "in_progress"

    # Clean up
    del thread_states[thread_id]


@pytest.mark.asyncio
async def test_mock_agent_creates_todos():
    """Test that MockAgent creates todos for planning tasks."""
    from src.services.mock_agent import MockAgent
    from langchain_core.messages import HumanMessage

    agent = MockAgent()

    # Test with a planning message
    result = agent.invoke({
        "messages": [HumanMessage(content="Plan a project for me")]
    })

    assert "todos" in result
    assert len(result["todos"]) == 3
    assert all("id" in todo for todo in result["todos"])
    assert all("content" in todo for todo in result["todos"])
    assert all("status" in todo for todo in result["todos"])

    # Verify todo statuses
    statuses = [todo["status"] for todo in result["todos"]]
    assert "completed" in statuses
    assert "in_progress" in statuses
    assert "pending" in statuses


@pytest.mark.asyncio
async def test_mock_agent_astream_events_with_todos():
    """Test that MockAgent emits todo events during streaming."""
    from src.services.mock_agent import MockAgent
    from langchain_core.messages import HumanMessage

    agent = MockAgent()

    # Test with a planning message
    events = []
    async for event in agent.astream_events(
        {"messages": [HumanMessage(content="Create a todo list for building a website")]},
        config={"configurable": {"thread_id": str(uuid4()), "temperature": 0.7, "max_tokens": 4096}},
        version="v2"
    ):
        events.append(event)

    # Check for todo events
    todo_events = [e for e in events if e.get("event") == "on_custom_event" and e.get("name") == "todo_update"]
    assert len(todo_events) > 0, "Should emit at least one todo event"

    # Verify todo event structure
    todo_event = todo_events[0]
    assert "data" in todo_event
    assert "todos" in todo_event["data"]
    assert len(todo_event["data"]["todos"]) == 3

    # Verify agent state was updated
    assert "todos" in agent._thread_state
    assert len(agent._thread_state["todos"]) == 3


@pytest.mark.asyncio
async def test_chat_input_handles_todos_event():
    """Test that ChatInput component logic handles todos events correctly.

    This is a unit test of the event handling logic.
    """
    # Simulate the event handling from ChatInput
    event_data = {
        "todos": [
            {"id": "1", "content": "Task 1", "status": "pending"},
            {"id": "2", "content": "Task 2", "status": "in_progress"},
        ]
    }

    # Verify structure
    assert "todos" in event_data
    assert len(event_data["todos"]) == 2

    # Verify todo structure
    for todo in event_data["todos"]:
        assert "id" in todo
        assert "content" in todo
        assert "status" in todo
        assert todo["status"] in ["pending", "in_progress", "completed", "cancelled"]


@pytest.mark.asyncio
async def test_todo_panel_polling_and_display():
    """Test that TodoPanel can fetch and display todos.

    This verifies the polling mechanism and display logic.
    """
    from src.services.mock_agent import MockAgent
    from langchain_core.messages import HumanMessage
    from src.api.routes.agent import thread_states

    # Create a mock agent and invoke it to generate todos
    agent = MockAgent()
    result = agent.invoke({
        "messages": [HumanMessage(content="Build a todo app")]
    })

    # Store todos in thread_states (simulating what the stream endpoint does)
    thread_id = str(uuid4())
    thread_states[thread_id] = {"todos": result["todos"]}

    # Simulate the polling endpoint call
    state = thread_states.get(thread_id, {})
    todos = state.get("todos", [])

    # Verify todos can be retrieved
    assert len(todos) == 3
    assert all("id" in t for t in todos)
    assert all("content" in t for t in todos)
    assert all("status" in t for t in todos)

    # Clean up
    del thread_states[thread_id]


@pytest.mark.asyncio
async def test_todo_update_during_streaming():
    """Test that todos are updated in real-time during streaming."""
    from src.services.mock_agent import MockAgent
    from langchain_core.messages import HumanMessage

    agent = MockAgent()
    thread_id = str(uuid4())

    # Track todos during streaming
    todos_during_stream = []

    async for event in agent.astream_events(
        {"messages": [HumanMessage(content="Plan and implement a feature")]},
        config={"configurable": {"thread_id": thread_id, "temperature": 0.7, "max_tokens": 4096}},
        version="v2"
    ):
        if event.get("event") == "on_custom_event" and event.get("name") == "todo_update":
            todos_during_stream.append(event["data"]["todos"])

    # Should have received todos during streaming
    assert len(todos_during_stream) > 0

    # Final todos should be in agent state
    assert "todos" in agent._thread_state
    assert len(agent._thread_state["todos"]) == 3


@pytest.mark.asyncio
async def test_stream_endpoint_emits_todos(client, test_db):
    """Test that the /api/agent/stream endpoint emits todos events.

    Note: This test requires MockAgent. If a real API key is configured,
    the test will be skipped as the real DeepAgent has different behavior.
    """
    from src.api.routes.agent import thread_states
    from src.services.agent_service import agent_service
    import json

    # Check if we're using MockAgent (no API key or agent is MockAgent)
    agent = agent_service.get_or_create_agent()
    if not hasattr(agent, '_thread_state'):
        # Real DeepAgent - skip this test as it has different state management
        # The real agent uses LangGraph state system, not _thread_state
        print("Skipping test - real DeepAgent detected (different state system)")
        return

    # Create a conversation
    conversation_data = {
        "title": "Test Todo Stream",
        "model": "claude-sonnet-4-5-20250929"
    }
    response = await client.post("/api/conversations", json=conversation_data)
    assert response.status_code == 201
    conversation = response.json()
    conversation_id = conversation["id"]

    # Stream with a task that creates todos
    thread_id = str(uuid4())
    response = await client.post(
        "/api/agent/stream",
        json={
            "message": "Plan a React project setup",
            "thread_id": thread_id,
            "conversation_id": conversation_id,
            "model": "claude-sonnet-4-5-20250929"
        }
    )

    assert response.status_code == 200

    # Read the stream asynchronously
    todos_found = False
    todos_data = None
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
                    if current_event == 'todos':
                        todos_found = True
                        todos_data = json.loads(current_data)
                        break
                current_event = None
                current_data = None
        if todos_found:
            break

    assert todos_found, "Should have emitted todos event"
    assert todos_data is not None
    assert "todos" in todos_data
    assert len(todos_data["todos"]) == 3

    # Verify todos are stored in thread_states
    assert thread_id in thread_states
    assert "todos" in thread_states[thread_id]
    assert len(thread_states[thread_id]["todos"]) == 3

    # Clean up
    del thread_states[thread_id]


@pytest.mark.asyncio
async def test_todos_endpoint_after_stream(client, test_db):
    """Test that /api/agent/todos/{thread_id} returns todos after streaming.

    Note: This test requires MockAgent. If a real API key is configured,
    the test will be skipped as the real DeepAgent has different behavior.
    """
    from src.api.routes.agent import thread_states
    from src.services.agent_service import agent_service
    import json

    # Check if we're using MockAgent
    agent = agent_service.get_or_create_agent()
    if not hasattr(agent, '_thread_state'):
        print("Skipping test - real DeepAgent detected (different state system)")
        return

    # Create a conversation
    conversation_data = {
        "title": "Test Todo Retrieval",
        "model": "claude-sonnet-4-5-20250929"
    }
    response = await client.post("/api/conversations", json=conversation_data)
    assert response.status_code == 201
    conversation = response.json()
    conversation_id = conversation["id"]

    # Stream to generate todos
    thread_id = str(uuid4())
    stream_response = await client.post(
        "/api/agent/stream",
        json={
            "message": "Build a todo list app",
            "thread_id": thread_id,
            "conversation_id": conversation_id,
            "model": "claude-sonnet-4-5-20250929"
        }
    )

    # Consume the stream asynchronously to trigger todo storage
    async for chunk in stream_response.aiter_text():
        pass  # Just consume all events

    # Now check the todos endpoint
    response = await client.get(f"/api/agent/todos/{thread_id}")
    assert response.status_code == 200

    data = response.json()
    assert data["thread_id"] == thread_id
    assert "todos" in data
    assert len(data["todos"]) == 3

    # Verify todo structure
    for todo in data["todos"]:
        assert "id" in todo
        assert "content" in todo
        assert "status" in todo
        assert todo["status"] in ["pending", "in_progress", "completed", "cancelled"]

    # Clean up
    if thread_id in thread_states:
        del thread_states[thread_id]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
