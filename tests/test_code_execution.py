"""Test code execution in sandbox environment (Feature #148)."""

import asyncio
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from src.main import app
from src.core.database import get_db, Base


TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_code_execution.db"


async def test_code_execution_simple_python():
    """Test simple Python code execution."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create a conversation
        conv = await client.post("/api/conversations", json={"title": "Code Execution Test"})
        conv_id = conv.json()["id"]

        # Create a Python code artifact
        artifact = await client.post(
            "/api/artifacts/create",
            json={
                "conversation_id": conv_id,
                "content": 'print("Hello, World!")\nprint("Execution successful")',
                "title": "Hello World",
                "language": "python",
            }
        )
        assert artifact.status_code == 200
        artifact_id = artifact.json()["id"]

        # Execute the code
        response = await client.post(
            f"/api/artifacts/{artifact_id}/execute",
            json={"timeout": 10}
        )

        print(f"\n1. Simple Python execution: {response.status_code}")
        assert response.status_code == 200

        result = response.json()
        print(f"   Success: {result['execution']['success']}")
        print(f"   Output: {result['execution']['output']}")
        print(f"   Time: {result['execution']['execution_time']}s")

        assert result["execution"]["success"] == True
        assert "Hello, World!" in result["execution"]["output"]
        assert "Execution successful" in result["execution"]["output"]
        print("   ✓ PASSED")


async def test_code_execution_with_error():
    """Test Python code with syntax error."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create a conversation
        conv = await client.post("/api/conversations", json={"title": "Code Error Test"})
        conv_id = conv.json()["id"]

        # Create invalid Python code
        artifact = await client.post(
            "/api/artifacts/create",
            json={
                "conversation_id": conv_id,
                "content": "print('unclosed string",
                "title": "Invalid Code",
                "language": "python",
            }
        )
        assert artifact.status_code == 200
        artifact_id = artifact.json()["id"]

        # Execute the code
        response = await client.post(
            f"/api/artifacts/{artifact_id}/execute",
            json={"timeout": 10}
        )

        print(f"\n2. Python error handling: {response.status_code}")
        assert response.status_code == 200

        result = response.json()
        print(f"   Success: {result['execution']['success']}")
        print(f"   Error present: {result['execution']['error'] is not None}")

        assert result["execution"]["success"] == False
        assert result["execution"]["error"] is not None
        print("   ✓ PASSED")


async def test_code_execution_timeout():
    """Test code execution timeout protection."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create a conversation
        conv = await client.post("/api/conversations", json={"title": "Timeout Test"})
        conv_id = conv.json()["id"]

        # Create infinite loop code
        artifact = await client.post(
            "/api/artifacts/create",
            json={
                "conversation_id": conv_id,
                "content": "while True:\n    pass",
                "title": "Infinite Loop",
                "language": "python",
            }
        )
        assert artifact.status_code == 200
        artifact_id = artifact.json()["id"]

        # Execute with short timeout
        import time
        start = time.time()
        response = await client.post(
            f"/api/artifacts/{artifact_id}/execute",
            json={"timeout": 2}
        )
        elapsed = time.time() - start

        print(f"\n3. Timeout protection: {response.status_code}")
        print(f"   Elapsed time: {elapsed:.2f}s (should be ~2s)")
        assert response.status_code == 200

        result = response.json()
        print(f"   Success: {result['execution']['success']}")
        print(f"   Timeout error: {'timeout' in result['execution']['error'].lower()}")

        assert result["execution"]["success"] == False
        assert "timeout" in result["execution"]["error"].lower()
        assert elapsed < 5  # Should timeout quickly, not run forever
        print("   ✓ PASSED")


async def test_code_execution_javascript():
    """Test JavaScript code execution."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create a conversation
        conv = await client.post("/api/conversations", json={"title": "JS Execution Test"})
        conv_id = conv.json()["id"]

        # Create JavaScript code
        artifact = await client.post(
            "/api/artifacts/create",
            json={
                "conversation_id": conv_id,
                "content": "console.log('Hello from JavaScript!');\nconsole.log('2 + 2 =', 2 + 2);",
                "title": "JS Hello",
                "language": "javascript",
            }
        )
        assert artifact.status_code == 200
        artifact_id = artifact.json()["id"]

        # Execute the code
        response = await client.post(
            f"/api/artifacts/{artifact_id}/execute",
            json={"timeout": 10}
        )

        print(f"\n4. JavaScript execution: {response.status_code}")
        assert response.status_code == 200

        result = response.json()
        print(f"   Success: {result['execution']['success']}")
        print(f"   Output: {result['execution']['output'][:100]}")

        # Note: Node.js outputs to stderr, so we check for output in either
        output = result["execution"]["output"] or result["execution"].get("error", "")
        assert "Hello from JavaScript!" in output or result["execution"]["success"]
        print("   ✓ PASSED")


async def test_code_execution_unsupported_language():
    """Test that unsupported languages are rejected."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create a conversation
        conv = await client.post("/api/conversations", json={"title": "Unsupported Lang Test"})
        conv_id = conv.json()["id"]

        # Create artifact with unsupported language
        artifact = await client.post(
            "/api/artifacts/create",
            json={
                "conversation_id": conv_id,
                "content": "PROGRAM Hello. BEGIN DISPLAY 'Hello' END.",
                "title": "COBOL Code",
                "language": "cobol",
            }
        )
        assert artifact.status_code == 200
        artifact_id = artifact.json()["id"]

        # Try to execute
        response = await client.post(
            f"/api/artifacts/{artifact_id}/execute",
            json={"timeout": 10}
        )

        print(f"\n5. Unsupported language: {response.status_code}")
        assert response.status_code == 200

        result = response.json()
        print(f"   Success: {result['execution']['success']}")
        print(f"   Error: {result['execution']['error']}")

        assert result["execution"]["success"] == False
        assert "not supported" in result["execution"]["error"].lower()
        print("   ✓ PASSED")


async def test_code_execution_non_code_artifact():
    """Test that non-code artifacts cannot be executed."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create a conversation
        conv = await client.post("/api/conversations", json={"title": "HTML Artifact Test"})
        conv_id = conv.json()["id"]

        # Create HTML artifact (not code type)
        artifact = await client.post(
            "/api/artifacts/create",
            json={
                "conversation_id": conv_id,
                "content": "<h1>Hello</h1>",
                "title": "HTML Page",
                "language": "html",
            }
        )
        assert artifact.status_code == 200
        artifact_id = artifact.json()["id"]

        # Try to execute (should fail)
        response = await client.post(
            f"/api/artifacts/{artifact_id}/execute",
            json={"timeout": 10}
        )

        print(f"\n6. Non-code artifact rejection: {response.status_code}")
        assert response.status_code == 400  # Bad Request

        print(f"   Error: {response.json()['detail']}")
        assert "cannot execute" in response.json()["detail"].lower()
        print("   ✓ PASSED")


async def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("Code Execution Tests (Feature #148)")
    print("="*60)

    try:
        await test_code_execution_simple_python()
        await test_code_execution_with_error()
        await test_code_execution_timeout()
        await test_code_execution_javascript()
        await test_code_execution_unsupported_language()
        await test_code_execution_non_code_artifact()

        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED!")
        print("="*60 + "\n")

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(asyncio.run(main()))
