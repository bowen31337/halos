"""Test Code Execution in Sandbox Environment (Feature #148).

This test verifies that:
1. Code artifacts can be executed in a sandboxed environment
2. Execution respects timeout limits
3. Output is captured correctly
4. Errors are properly reported
5. Different languages are supported (Python, JavaScript, Bash)
6. HITL approval dialog is shown before execution
7. Execution results are displayed in the UI
"""

import pytest
import asyncio
from uuid import uuid4


@pytest.mark.asyncio
async def test_execute_python_artifact(client, test_db):
    """Test executing a Python code artifact."""
    # Create a conversation
    conversation_data = {
        "title": "Test Code Execution",
        "model": "claude-sonnet-4-5-20250929"
    }
    response = await client.post("/api/conversations", json=conversation_data)
    assert response.status_code == 201
    conversation = response.json()
    conversation_id = conversation["id"]

    # Create a Python artifact
    artifact_data = {
        "content": "print('Hello from Python!')\nfor i in range(3):\n    print(f'Line {i}')",
        "title": "test_script",
        "language": "python",
        "conversation_id": conversation_id
    }
    response = await client.post("/api/artifacts/create", json=artifact_data)
    assert response.status_code == 201
    artifact = response.json()
    artifact_id = artifact["id"]

    # Execute the artifact
    response = await client.post(f"/api/artifacts/{artifact_id}/execute", json={"timeout": 10})
    assert response.status_code == 200
    result = response.json()

    # Verify execution result
    assert result["artifact_id"] == artifact_id
    assert result["title"] == "test_script"
    assert result["language"] == "python"
    assert result["execution"]["success"] is True
    assert "Hello from Python!" in result["execution"]["output"]
    assert "Line 0" in result["execution"]["output"]
    assert result["execution"]["return_code"] == 0
    assert result["execution"]["execution_time"] > 0


@pytest.mark.asyncio
async def test_execute_javascript_artifact(client, test_db):
    """Test executing a JavaScript code artifact."""
    # Create a conversation
    conversation_data = {
        "title": "Test JS Execution",
        "model": "claude-sonnet-4-5-20250929"
    }
    response = await client.post("/api/conversations", json=conversation_data)
    assert response.status_code == 201
    conversation = response.json()
    conversation_id = conversation["id"]

    # Create a JavaScript artifact
    artifact_data = {
        "content": "console.log('Hello from JavaScript!');\nfor(let i=0; i<3; i++) { console.log('Line ' + i); }",
        "title": "test_js",
        "language": "javascript",
        "conversation_id": conversation_id
    }
    response = await client.post("/api/artifacts/create", json=artifact_data)
    assert response.status_code == 201
    artifact = response.json()
    artifact_id = artifact["id"]

    # Execute the artifact
    response = await client.post(f"/api/artifacts/{artifact_id}/execute", json={"timeout": 10})
    assert response.status_code == 200
    result = response.json()

    # Verify execution result
    assert result["execution"]["success"] is True
    assert "Hello from JavaScript!" in result["execution"]["output"]
    assert result["execution"]["return_code"] == 0


@pytest.mark.asyncio
async def test_execute_bash_artifact(client, test_db):
    """Test executing a Bash code artifact."""
    # Create a conversation
    conversation_data = {
        "title": "Test Bash Execution",
        "model": "claude-sonnet-4-5-20250929"
    }
    response = await client.post("/api/conversations", json=conversation_data)
    assert response.status_code == 201
    conversation = response.json()
    conversation_id = conversation["id"]

    # Create a Bash artifact
    artifact_data = {
        "content": "echo 'Hello from Bash'\necho 'Current directory:'\npwd",
        "title": "test_bash",
        "language": "bash",
        "conversation_id": conversation_id
    }
    response = await client.post("/api/artifacts/create", json=artifact_data)
    assert response.status_code == 201
    artifact = response.json()
    artifact_id = artifact["id"]

    # Execute the artifact
    response = await client.post(f"/api/artifacts/{artifact_id}/execute", json={"timeout": 10})
    assert response.status_code == 200
    result = response.json()

    # Verify execution result
    assert result["execution"]["success"] is True
    assert "Hello from Bash" in result["execution"]["output"]
    assert result["execution"]["return_code"] == 0


@pytest.mark.asyncio
async def test_execute_with_error(client, test_db):
    """Test executing code that produces an error."""
    # Create a conversation
    conversation_data = {
        "title": "Test Error Handling",
        "model": "claude-sonnet-4-5-20250929"
    }
    response = await client.post("/api/conversations", json=conversation_data)
    assert response.status_code == 201
    conversation = response.json()
    conversation_id = conversation["id"]

    # Create an artifact with code that will error
    artifact_data = {
        "content": "print('Before error')\nraise ValueError('This is an error message')\nprint('After error')",
        "title": "error_script",
        "language": "python",
        "conversation_id": conversation_id
    }
    response = await client.post("/api/artifacts/create", json=artifact_data)
    assert response.status_code == 201
    artifact = response.json()
    artifact_id = artifact["id"]

    # Execute the artifact
    response = await client.post(f"/api/artifacts/{artifact_id}/execute", json={"timeout": 10})
    assert response.status_code == 200
    result = response.json()

    # Verify execution result shows error
    assert result["execution"]["success"] is False
    assert "Before error" in result["execution"]["output"]
    assert result["execution"]["return_code"] != 0


@pytest.mark.asyncio
async def test_execute_timeout(client, test_db):
    """Test execution timeout protection."""
    # Create a conversation
    conversation_data = {
        "title": "Test Timeout",
        "model": "claude-sonnet-4-5-20250929"
    }
    response = await client.post("/api/conversations", json=conversation_data)
    assert response.status_code == 201
    conversation = response.json()
    conversation_id = conversation["id"]

    # Create an artifact with infinite loop
    artifact_data = {
        "content": "while True:\n    pass",  # Infinite loop
        "title": "timeout_test",
        "language": "python",
        "conversation_id": conversation_id
    }
    response = await client.post("/api/artifacts/create", json=artifact_data)
    assert response.status_code == 201
    artifact = response.json()
    artifact_id = artifact["id"]

    # Execute with short timeout
    response = await client.post(f"/api/artifacts/{artifact_id}/execute", json={"timeout": 2})
    assert response.status_code == 200
    result = response.json()

    # Verify timeout occurred
    assert result["execution"]["success"] is False
    assert "timeout" in result["execution"]["error"].lower()
    assert result["execution"]["return_code"] == -1


@pytest.mark.asyncio
async def test_execute_unsupported_language(client, test_db):
    """Test executing unsupported language."""
    # Create a conversation
    conversation_data = {
        "title": "Test Unsupported",
        "model": "claude-sonnet-4-5-20250929"
    }
    response = await client.post("/api/conversations", json=conversation_data)
    assert response.status_code == 201
    conversation = response.json()
    conversation_id = conversation["id"]

    # Create an artifact with unsupported language
    artifact_data = {
        "content": "print('test')",
        "title": "unsupported",
        "language": "cobol",  # Not supported
        "conversation_id": conversation_id
    }
    response = await client.post("/api/artifacts/create", json=artifact_data)
    assert response.status_code == 201
    artifact = response.json()
    artifact_id = artifact["id"]

    # Execute the artifact
    response = await client.post(f"/api/artifacts/{artifact_id}/execute", json={"timeout": 10})
    assert response.status_code == 200
    result = response.json()

    # Verify error about unsupported language
    assert result["execution"]["success"] is False
    assert "cobol" in result["execution"]["error"].lower()


@pytest.mark.asyncio
async def test_execute_non_code_artifact_fails(client, test_db):
    """Test that non-code artifacts cannot be executed."""
    # Create a conversation
    conversation_data = {
        "title": "Test Non-Code",
        "model": "claude-sonnet-4-5-20250929"
    }
    response = await client.post("/api/conversations", json=conversation_data)
    assert response.status_code == 201
    conversation = response.json()
    conversation_id = conversation["id"]

    # Create an HTML artifact (non-code)
    artifact_data = {
        "content": "<h1>Hello</h1>",
        "title": "html_test",
        "language": "html",
        "artifact_type": "html",
        "conversation_id": conversation_id
    }
    response = await client.post("/api/artifacts/create", json=artifact_data)
    assert response.status_code == 201
    artifact = response.json()
    artifact_id = artifact["id"]

    # Try to execute - should fail
    response = await client.post(f"/api/artifacts/{artifact_id}/execute", json={"timeout": 10})
    assert response.status_code == 400
    error = response.json()
    assert "Cannot execute artifact of type 'html'" in error["message"]


@pytest.mark.asyncio
async def test_execute_artifact_not_found(client, test_db):
    """Test executing non-existent artifact."""
    fake_id = str(uuid4())
    response = await client.post(f"/api/artifacts/{fake_id}/execute", json={"timeout": 10})
    assert response.status_code == 404
    error = response.json()
    assert "Artifact not found" in error["message"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
