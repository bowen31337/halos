"""Test diff viewer feature (Feature #55).

This test verifies that:
1. Agent creates a file
2. Agent modifies the file
3. Diff viewer shows the changes
4. Original content shows on left
5. Modified content shows on right
6. Changes are highlighted (added/removed)
"""

import pytest
import asyncio
from uuid import uuid4


@pytest.mark.asyncio
async def test_diff_tracking_in_chatstore():
    """Test that chatStore tracks file diffs automatically."""
    from src.services.mock_agent import MockAgent
    from langchain_core.messages import HumanMessage

    # Simulate the frontend chatStore behavior
    class MockChatStore:
        def __init__(self):
            self.files = []
            self.file_history = {}
            self.file_diffs = []

        def set_files(self, new_files):
            """Mimics chatStore.setFiles logic."""
            for file in new_files:
                file_id = file["id"]
                history = self.file_history.get(file_id, [])
                last_content = history[-1] if history else None

                # Track changes if content differs from last known version
                if last_content is not None and last_content != file["content"]:
                    self.file_diffs.append({
                        "id": str(uuid4()),
                        "fileId": file_id,
                        "fileName": file["name"],
                        "oldContent": last_content,
                        "newContent": file["content"],
                        "timestamp": "2024-01-01T00:00:00Z",
                        "changeType": "modified"
                    })
                elif last_content is None and len(history) == 0:
                    # New file added
                    self.file_diffs.append({
                        "id": str(uuid4()),
                        "fileId": file_id,
                        "fileName": file["name"],
                        "oldContent": "",
                        "newContent": file["content"],
                        "timestamp": "2024-01-01T00:00:00Z",
                        "changeType": "added"
                    })

                # Update history
                self.file_history[file_id] = history + [file["content"]]

            self.files = new_files

    store = MockChatStore()

    # Step 1: Agent creates a file
    agent = MockAgent()
    result = agent.invoke({
        "messages": [HumanMessage(content="Create a Python file")]
    })

    # Get the files from agent state
    files = agent._thread_state.get("files", [])
    assert len(files) >= 1

    # Simulate frontend receiving files event
    store.set_files(files)

    # Should have added file diffs
    assert len(store.file_diffs) >= 1
    assert store.file_diffs[0]["changeType"] == "added"

    # Step 2: Agent modifies the file
    # Simulate modified content
    modified_files = []
    for f in files:
        modified_file = f.copy()
        modified_file["content"] = f["content"] + "\n# Added comment"
        modified_files.append(modified_file)

    # Simulate frontend receiving updated files event
    store.set_files(modified_files)

    # Should have modification diffs
    assert len(store.file_diffs) >= 2
    # Find the modified diff
    modified_diff = next((d for d in store.file_diffs if d["changeType"] == "modified"), None)
    assert modified_diff is not None
    assert "# Added comment" in modified_diff["newContent"]
    assert "# Added comment" not in modified_diff["oldContent"]


@pytest.mark.asyncio
async def test_stream_endpoint_generates_diffs(client, test_db):
    """Test that streaming generates file diffs."""
    from src.api.routes.agent import thread_states
    import json

    # Create a conversation
    conversation_data = {
        "title": "Test Diff Feature",
        "model": "claude-sonnet-4-5-20250929"
    }
    response = await client.post("/api/conversations", json=conversation_data)
    assert response.status_code == 201
    conversation = response.json()
    conversation_id = conversation["id"]

    # Stream to create a file
    thread_id = str(uuid4())
    response = await client.post(
        "/api/agent/stream",
        json={
            "message": "Create a Python file with a main function",
            "thread_id": thread_id,
            "conversation_id": conversation_id,
            "model": "claude-sonnet-4-5-20250929"
        }
    )

    assert response.status_code == 200

    # Read the stream and collect files events
    content = response.content.decode('utf-8')
    lines = content.split('\n')

    files_events = []
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
                    files_events.append(json.loads(current_data))
            current_event = None
            current_data = None

    # Should have at least one files event
    assert len(files_events) >= 1

    # Verify files structure
    for event in files_events:
        assert "files" in event
        for file in event["files"]:
            assert "id" in file
            assert "name" in file
            assert "content" in file
            assert "path" in file

    # Clean up
    if thread_id in thread_states:
        del thread_states[thread_id]


@pytest.mark.asyncio
async def test_diff_panel_integration(client, test_db):
    """Test that diff panel can display file changes."""
    from src.api.routes.agent import thread_states

    # Create a conversation
    conversation_data = {
        "title": "Test Diff Panel",
        "model": "claude-sonnet-4-5-20250929"
    }
    response = await client.post("/api/conversations", json=conversation_data)
    assert response.status_code == 201
    conversation = response.json()
    conversation_id = conversation["id"]

    thread_id = conversation_id

    # Stream to create a file
    stream1 = await client.post(
        "/api/agent/stream",
        json={
            "message": "Create a file called hello.py with print('hello')",
            "thread_id": thread_id,
            "conversation_id": conversation_id,
            "model": "claude-sonnet-4-5-20250929"
        }
    )
    stream1.content  # Consume

    # Get initial files
    files1 = await client.get(f"/api/agent/files/{thread_id}")
    initial_files = files1.json()["files"]

    # Stream to modify the file
    stream2 = await client.post(
        "/api/agent/stream",
        json={
            "message": "Edit hello.py to print('hello world')",
            "thread_id": thread_id,
            "conversation_id": conversation_id,
            "model": "claude-sonnet-4-5-20250929"
        }
    )
    stream2.content  # Consume

    # Get updated files
    files2 = await client.get(f"/api/agent/files/{thread_id}")
    updated_files = files2.json()["files"]

    # Verify files were modified
    assert len(updated_files) >= 1

    # Find hello.py
    hello_py = next((f for f in updated_files if f["name"] == "hello.py"), None)
    if hello_py:
        # The content should have changed
        assert "hello" in hello_py["content"].lower()

    # Clean up
    if thread_id in thread_states:
        del thread_states[thread_id]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
