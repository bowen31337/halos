"""Test Feature #148: Code execution in sandbox environment

This test verifies:
- Code execution endpoint exists and works
- HITL approval dialog is shown
- Code runs in sandbox with timeout
- Output is displayed correctly
- Errors are caught and shown
- Timeout prevents infinite loops
"""

import pytest
import asyncio
from httpx import AsyncClient, ASGITransport
from src.main import app


@pytest.fixture
async def client():
    """Async HTTP client for testing."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_code_execution_endpoint_exists(client):
    """Test that the code execution endpoint exists."""
    # First, create a conversation
    conv_response = await client.post("/api/conversations", json={
        "title": "Test Conversation",
        "model": "claude-sonnet-4-5-20250929"
    })
    assert conv_response.status_code == 201
    conversation = conv_response.json()
    conversation_id = conversation["id"]

    # Now create a code artifact
    artifact_data = {
        "content": "print('Hello, World!')",
        "title": "test_script",
        "language": "python",
        "conversation_id": conversation_id
    }

    response = await client.post("/api/artifacts/create", json=artifact_data)
    assert response.status_code == 201
    artifact = response.json()

    artifact_id = artifact["id"]

    # Test execution endpoint
    exec_request = {"timeout": 10}
    response = await client.post(f"/api/artifacts/{artifact_id}/execute", json=exec_request)

    # The endpoint should exist and return a result
    assert response.status_code == 200
    result = response.json()

    # Verify response structure
    assert "artifact_id" in result
    assert "execution" in result
    assert "title" in result
    assert "language" in result

    # Verify execution result structure
    execution = result["execution"]
    assert "success" in execution
    assert "execution_time" in execution
    assert "return_code" in execution

    print(f"✓ Execution endpoint exists and returns proper structure")
    print(f"  Success: {execution['success']}")
    print(f"  Time: {execution['execution_time']}s")
    print(f"  Return code: {execution['return_code']}")


@pytest.mark.asyncio
async def test_python_code_execution(client):
    """Test Python code execution."""
    # Create Python artifact
    artifact_data = {
        "content": "print('Hello from Python!')\nprint('Second line')",
        "title": "python_test",
        "language": "python",
        "conversation_id": None
    }

    response = await client.post("/api/artifacts/create", json=artifact_data)
    assert response.status_code == 201
    artifact = response.json()
    artifact_id = artifact["id"]

    # Execute
    exec_request = {"timeout": 10}
    response = await client.post(f"/api/artifacts/{artifact_id}/execute", json=exec_request)
    assert response.status_code == 200

    result = response.json()
    execution = result["execution"]

    # Should succeed
    assert execution["success"] is True
    assert execution["return_code"] == 0

    # Should have output
    assert "output" in execution
    assert "Hello from Python!" in execution["output"]
    assert "Second line" in execution["output"]

    # Should have execution time
    assert execution["execution_time"] > 0

    print(f"✓ Python code executed successfully")
    print(f"  Output: {execution['output'][:50]}...")


@pytest.mark.asyncio
async def test_python_code_error_handling(client):
    """Test Python code error handling."""
    # Create Python artifact with syntax error
    artifact_data = {
        "content": "print('Missing quote)",
        "title": "python_error_test",
        "language": "python",
        "conversation_id": None
    }

    response = await client.post("/api/artifacts/create", json=artifact_data)
    assert response.status_code == 201
    artifact = response.json()
    artifact_id = artifact["id"]

    # Execute
    exec_request = {"timeout": 10}
    response = await client.post(f"/api/artifacts/{artifact_id}/execute", json=exec_request)
    assert response.status_code == 200

    result = response.json()
    execution = result["execution"]

    # Should fail
    assert execution["success"] is False
    assert execution["return_code"] != 0

    # Should have error message
    assert "error" in execution
    assert len(execution["error"]) > 0

    print(f"✓ Python error handled correctly")
    print(f"  Error: {execution['error'][:100]}...")


@pytest.mark.asyncio
async def test_timeout_protection(client):
    """Test timeout protection for infinite loops."""
    # Create Python artifact with infinite loop
    artifact_data = {
        "content": "while True:\n    pass",
        "title": "infinite_loop",
        "language": "python",
        "conversation_id": None
    }

    response = await client.post("/api/artifacts/create", json=artifact_data)
    assert response.status_code == 201
    artifact = response.json()
    artifact_id = artifact["id"]

    # Execute with short timeout
    exec_request = {"timeout": 2}  # 2 second timeout
    response = await client.post(f"/api/artifacts/{artifact_id}/execute", json=exec_request)
    assert response.status_code == 200

    result = response.json()
    execution = result["execution"]

    # Should fail due to timeout
    assert execution["success"] is False
    assert execution["return_code"] == -1

    # Should have timeout error
    assert "error" in execution
    assert "timeout" in execution["error"].lower()

    # Execution time should be approximately the timeout
    assert 1.5 < execution["execution_time"] <= 3

    print(f"✓ Timeout protection works")
    print(f"  Execution time: {execution['execution_time']}s")
    print(f"  Error: {execution['error']}")


@pytest.mark.asyncio
async def test_javascript_code_execution(client):
    """Test JavaScript code execution."""
    # Create JavaScript artifact
    artifact_data = {
        "content": "console.log('Hello from JavaScript!');\nconsole.log('Second line');",
        "title": "javascript_test",
        "language": "javascript",
        "conversation_id": None
    }

    response = await client.post("/api/artifacts/create", json=artifact_data)
    assert response.status_code == 201
    artifact = response.json()
    artifact_id = artifact["id"]

    # Execute
    exec_request = {"timeout": 10}
    response = await client.post(f"/api/artifacts/{artifact_id}/execute", json=exec_request)
    assert response.status_code == 200

    result = response.json()
    execution = result["execution"]

    # Should succeed
    assert execution["success"] is True
    assert execution["return_code"] == 0

    # Should have output
    assert "output" in execution
    assert "Hello from JavaScript!" in execution["output"]

    print(f"✓ JavaScript code executed successfully")
    print(f"  Output: {execution['output'][:50]}...")


@pytest.mark.asyncio
async def test_bash_code_execution(client):
    """Test Bash script execution."""
    # Create Bash artifact
    artifact_data = {
        "content": "#!/bin/bash\necho 'Hello from Bash!'\necho 'Current directory:'\npwd",
        "title": "bash_test",
        "language": "bash",
        "conversation_id": None
    }

    response = await client.post("/api/artifacts/create", json=artifact_data)
    assert response.status_code == 201
    artifact = response.json()
    artifact_id = artifact["id"]

    # Execute
    exec_request = {"timeout": 10}
    response = await client.post(f"/api/artifacts/{artifact_id}/execute", json=exec_request)
    assert response.status_code == 200

    result = response.json()
    execution = result["execution"]

    # Should succeed
    assert execution["success"] is True
    assert execution["return_code"] == 0

    # Should have output
    assert "output" in execution
    assert "Hello from Bash!" in execution["output"]

    print(f"✓ Bash script executed successfully")
    print(f"  Output: {execution['output'][:50]}...")


@pytest.mark.asyncio
async def test_unsupported_language(client):
    """Test unsupported language handling."""
    # Create artifact with unsupported language
    artifact_data = {
        "content": "PROGRAM MAIN. WRITE 'Hello'. END PROGRAM.",
        "title": "unsupported_test",
        "language": "fortran",
        "conversation_id": None
    }

    response = await client.post("/api/artifacts/create", json=artifact_data)
    assert response.status_code == 201
    artifact = response.json()
    artifact_id = artifact["id"]

    # Execute
    exec_request = {"timeout": 10}
    response = await client.post(f"/api/artifacts/{artifact_id}/execute", json=exec_request)
    assert response.status_code == 200

    result = response.json()
    execution = result["execution"]

    # Should fail with unsupported language error
    assert execution["success"] is False
    assert execution["return_code"] == -2

    # Should have error message
    assert "error" in execution
    assert "not supported" in execution["error"].lower()

    print(f"✓ Unsupported language handled correctly")
    print(f"  Error: {execution['error']}")


@pytest.mark.asyncio
async def test_only_code_artifacts_executable(client):
    """Test that non-code artifacts cannot be executed."""
    # Create HTML artifact (not executable)
    artifact_data = {
        "content": "<html><body>Hello</body></html>",
        "title": "html_test",
        "language": "html",
        "conversation_id": None
    }

    response = await client.post("/api/artifacts/create", json=artifact_data)
    assert response.status_code == 201
    artifact = response.json()
    artifact_id = artifact["id"]

    # Try to execute
    exec_request = {"timeout": 10}
    response = await client.post(f"/api/artifacts/{artifact_id}/execute", json=exec_request)

    # Should return 400 Bad Request
    assert response.status_code == 400

    # Should have error message
    error_detail = response.json()
    assert "Cannot execute" in error_detail["detail"]
    assert "html" in error_detail["detail"].lower()

    print(f"✓ Non-code artifacts correctly rejected")
    print(f"  Error: {error_detail['detail']}")


if __name__ == "__main__":
    # Run tests
    import sys

    pytest_args = [
        __file__,
        "-v",
        "--tb=short",
        "-W", "ignore::DeprecationWarning"
    ]

    sys.exit(pytest.main(pytest_args))
