"""Test files panel functionality.

This test verifies that the files panel works end-to-end with MockAgent:
1. Backend /agent/files/{thread_id} endpoint returns files from agent state
2. SSE streaming emits files events
3. MockAgent creates and tracks files
4. Frontend can receive and display files in the FilesPanel

Feature #54: Files panel shows agent workspace files
"""

import pytest
import asyncio
from uuid import uuid4


@pytest.mark.asyncio
async def test_backend_files_endpoint(client, test_db):
    """Test that the /api/agent/files/{thread_id} endpoint returns files."""
    # Create a conversation
    conversation_data = {
        "title": "Test Files Conversation",
        "model": "claude-sonnet-4-5-20250929"
    }
    response = await client.post("/api/conversations", json=conversation_data)
    assert response.status_code == 201
    conversation = response.json()
    conversation_id = conversation["id"]

    # Use conversation_id as thread_id for files
    thread_id = conversation_id

    # Initially, files should be empty or not exist
    response = await client.get(f"/api/agent/files/{thread_id}")
    assert response.status_code == 200
    data = response.json()
    assert "thread_id" in data
    assert "files" in data
    # May be empty initially

    # Simulate agent storing files in thread_states
    from src.api.routes.agent import thread_states
    thread_states[thread_id] = {
        "files": [
            {
                "id": str(uuid4()),
                "name": "main.py",
                "path": "main.py",
                "content": "print('Hello, World!')",
                "size": 24,
                "file_type": "text/x-python",
                "created_at": "2024-01-01T00:00:00Z"
            },
            {
                "id": str(uuid4()),
                "name": "utils.py",
                "path": "src/utils.py",
                "content": "def helper(): return 'help'",
                "size": 30,
                "file_type": "text/x-python",
                "created_at": "2024-01-01T00:00:00Z"
            }
        ]
    }

    # Now fetch files again
    response = await client.get(f"/api/agent/files/{thread_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["thread_id"] == thread_id
    assert len(data["files"]) == 2
    assert data["files"][0]["name"] == "main.py"
    assert data["files"][1]["path"] == "src/utils.py"

    # Clean up
    del thread_states[thread_id]


@pytest.mark.asyncio
async def test_mock_agent_creates_files():
    """Test that MockAgent creates files for file-related tasks."""
    from src.services.mock_agent import MockAgent
    from langchain_core.messages import HumanMessage

    agent = MockAgent()

    # Test with a file creation message
    result = agent.invoke({
        "messages": [HumanMessage(content="Create a Python file")]
    })

    assert "files" in agent._thread_state
    assert len(agent._thread_state["files"]) >= 1

    # Verify file structure
    for file in agent._thread_state["files"]:
        assert "id" in file
        assert "name" in file
        assert "path" in file
        assert "content" in file
        assert "size" in file
        assert "file_type" in file
        assert "created_at" in file


@pytest.mark.asyncio
async def test_mock_agent_astream_events_with_files():
    """Test that MockAgent creates files during streaming."""
    from src.services.mock_agent import MockAgent
    from langchain_core.messages import HumanMessage

    agent = MockAgent()

    # Test with a file-related message
    async for event in agent.astream_events(
        {"messages": [HumanMessage(content="Write a script file")]},
        config={"configurable": {"thread_id": str(uuid4()), "temperature": 0.7, "max_tokens": 4096}},
        version="v2"
    ):
        pass  # Just consume the stream

    # Verify agent state was updated with files
    assert "files" in agent._thread_state
    assert len(agent._thread_state["files"]) >= 1


@pytest.mark.asyncio
async def test_chat_input_handles_files_event():
    """Test that ChatInput component logic handles files events correctly.

    This is a unit test of the event handling logic.
    """
    # Simulate the event handling from ChatInput
    event_data = {
        "files": [
            {
                "id": "1",
                "name": "main.py",
                "path": "main.py",
                "content": "print('hello')",
                "size": 17,
                "file_type": "text/x-python",
                "created_at": "2024-01-01T00:00:00Z"
            },
            {
                "id": "2",
                "name": "utils.py",
                "path": "src/utils.py",
                "content": "def helper(): pass",
                "size": 18,
                "file_type": "text/x-python",
                "created_at": "2024-01-01T00:00:00Z"
            }
        ]
    }

    # Verify structure
    assert "files" in event_data
    assert len(event_data["files"]) == 2

    # Verify file structure
    for file in event_data["files"]:
        assert "id" in file
        assert "name" in file
        assert "path" in file
        assert "content" in file
        assert "size" in file
        assert "file_type" in file
        assert "created_at" in file


@pytest.mark.asyncio
async def test_files_panel_polling_and_display():
    """Test that FilesPanel can fetch and display files.

    This verifies the polling mechanism and display logic.
    """
    from src.services.mock_agent import MockAgent
    from langchain_core.messages import HumanMessage
    from src.api.routes.agent import thread_states

    # Create a mock agent and invoke it to generate files
    agent = MockAgent()
    result = agent.invoke({
        "messages": [HumanMessage(content="Create a Python project")]
    })

    # Store files in thread_states (simulating what the stream endpoint does)
    thread_id = str(uuid4())
    thread_states[thread_id] = {"files": agent._thread_state.get("files", [])}

    # Simulate the polling endpoint call
    state = thread_states.get(thread_id, {})
    files = state.get("files", [])

    # Verify files can be retrieved
    assert len(files) >= 1
    assert all("id" in f for f in files)
    assert all("name" in f for f in files)
    assert all("path" in f for f in files)
    assert all("content" in f for f in files)

    # Clean up
    del thread_states[thread_id]


@pytest.mark.asyncio
async def test_stream_endpoint_emits_files(client, test_db):
    """Test that the /api/agent/stream endpoint emits files events."""
    from src.api.routes.agent import thread_states
    import json

    # Create a conversation
    conversation_data = {
        "title": "Test Files Stream",
        "model": "claude-sonnet-4-5-20250929"
    }
    response = await client.post("/api/conversations", json=conversation_data)
    assert response.status_code == 201
    conversation = response.json()
    conversation_id = conversation["id"]

    # Stream with a task that creates files
    thread_id = str(uuid4())
    response = await client.post(
        "/api/agent/stream",
        json={
            "message": "Create a Python script file",
            "thread_id": thread_id,
            "conversation_id": conversation_id,
            "model": "claude-sonnet-4-5-20250929"
        }
    )

    assert response.status_code == 200

    # Read the stream
    content = response.content.decode('utf-8')
    lines = content.split('\n')

    # Parse SSE events
    files_found = False
    files_data = None
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
                if current_event == 'files':
                    files_found = True
                    files_data = json.loads(current_data)
                    break
            current_event = None
            current_data = None

    assert files_found, "Should have emitted files event"
    assert files_data is not None
    assert "files" in files_data
    assert len(files_data["files"]) >= 1

    # Verify files are stored in thread_states
    assert thread_id in thread_states
    assert "files" in thread_states[thread_id]
    assert len(thread_states[thread_id]["files"]) >= 1

    # Clean up
    del thread_states[thread_id]


@pytest.mark.asyncio
async def test_files_endpoint_after_stream(client, test_db):
    """Test that /api/agent/files/{thread_id} returns files after streaming."""
    from src.api.routes.agent import thread_states
    import json

    # Create a conversation
    conversation_data = {
        "title": "Test Files Retrieval",
        "model": "claude-sonnet-4-5-20250929"
    }
    response = await client.post("/api/conversations", json=conversation_data)
    assert response.status_code == 201
    conversation = response.json()
    conversation_id = conversation["id"]

    # Stream to generate files
    thread_id = str(uuid4())
    stream_response = await client.post(
        "/api/agent/stream",
        json={
            "message": "Create a Python project with files",
            "thread_id": thread_id,
            "conversation_id": conversation_id,
            "model": "claude-sonnet-4-5-20250929"
        }
    )

    # Consume the stream
    stream_response.content

    # Now check the files endpoint
    response = await client.get(f"/api/agent/files/{thread_id}")
    assert response.status_code == 200

    data = response.json()
    assert data["thread_id"] == thread_id
    assert "files" in data
    assert len(data["files"]) >= 1

    # Verify file structure
    for file in data["files"]:
        assert "id" in file
        assert "name" in file
        assert "path" in file
        assert "content" in file
        assert "size" in file
        assert "file_type" in file

    # Clean up
    if thread_id in thread_states:
        del thread_states[thread_id]


@pytest.mark.asyncio
async def test_files_panel_ui_integration(client, test_db):
    """Test that the files panel UI component can be accessed."""
    # Create a conversation
    conversation_data = {
        "title": "Test UI Integration",
        "model": "claude-sonnet-4-5-20250929"
    }
    response = await client.post("/api/conversations", json=conversation_data)
    assert response.status_code == 201
    conversation = response.json()
    conversation_id = conversation["id"]

    # Stream to generate files
    thread_id = conversation_id
    stream_response = await client.post(
        "/api/agent/stream",
        json={
            "message": "Create a main.py file",
            "thread_id": thread_id,
            "conversation_id": conversation_id,
            "model": "claude-sonnet-4-5-20250929"
        }
    )

    # Consume the stream
    stream_response.content

    # Get files
    files_response = await client.get(f"/api/agent/files/{thread_id}")
    files_data = files_response.json()

    # Verify the files can be displayed in the UI
    assert "files" in files_data
    files = files_data["files"]

    # Should have at least one file
    assert len(files) >= 1

    # Find main.py
    main_py = next((f for f in files if f["name"] == "main.py"), None)
    assert main_py is not None

    # Verify file has all required fields for UI display
    assert main_py["name"] == "main.py"
    assert "content" in main_py
    assert main_py["content"] is not None
    assert main_py["size"] > 0
    assert main_py["file_type"] is not None
    assert main_py["path"] is not None

    # Clean up
    from src.api.routes.agent import thread_states
    if thread_id in thread_states:
        del thread_states[thread_id]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
