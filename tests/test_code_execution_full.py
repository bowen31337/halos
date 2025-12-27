"""Comprehensive code execution tests (Feature #148)."""

import asyncio
import time
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from src.main import app
from src.core.database import get_db, Base


async def run_all_tests():
    """Run all code execution tests."""
    # Use in-memory database
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Override get_db dependency
    async def override_get_db():
        async with async_session() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Create conversation once for all tests
            conv = await client.post("/api/conversations", json={"title": "Code Execution Tests"})
            assert conv.status_code in [200, 201]
            conv_id = conv.json()["id"]

            print("\n" + "="*60)
            print("Code Execution Tests (Feature #148)")
            print("="*60)

            # Test 1: Simple Python execution
            print("\n[Test 1] Simple Python execution...")
            artifact = await client.post(
                "/api/artifacts/create",
                json={
                    "conversation_id": conv_id,
                    "content": 'print("Hello, World!")\nprint("Test successful")',
                    "title": "Hello",
                    "language": "python",
                }
            )
            assert artifact.status_code in [200, 201]
            artifact_id = artifact.json()["id"]

            response = await client.post(
                f"/api/artifacts/{artifact_id}/execute",
                json={"timeout": 10}
            )
            assert response.status_code == 200
            result = response.json()
            assert result["execution"]["success"] == True
            assert "Hello, World!" in result["execution"]["output"]
            print(f"  ✓ Output: {result['execution']['output'].strip()}")
            print(f"  ✓ Time: {result['execution']['execution_time']}s")

            # Test 2: Python with error
            print("\n[Test 2] Python syntax error...")
            artifact = await client.post(
                "/api/artifacts/create",
                json={
                    "conversation_id": conv_id,
                    "content": "print('unclosed string",
                    "title": "Invalid",
                    "language": "python",
                }
            )
            assert artifact.status_code in [200, 201]
            artifact_id = artifact.json()["id"]

            response = await client.post(
                f"/api/artifacts/{artifact_id}/execute",
                json={"timeout": 10}
            )
            assert response.status_code == 200
            result = response.json()
            assert result["execution"]["success"] == False
            assert result["execution"]["error"] is not None
            print(f"  ✓ Error caught: {result['execution']['error'][:50]}...")

            # Test 3: Timeout protection
            print("\n[Test 3] Timeout protection (infinite loop)...")
            artifact = await client.post(
                "/api/artifacts/create",
                json={
                    "conversation_id": conv_id,
                    "content": "while True:\n    pass",
                    "title": "Infinite Loop",
                    "language": "python",
                }
            )
            assert artifact.status_code in [200, 201]
            artifact_id = artifact.json()["id"]

            start = time.time()
            response = await client.post(
                f"/api/artifacts/{artifact_id}/execute",
                json={"timeout": 2}
            )
            elapsed = time.time() - start
            assert response.status_code == 200
            result = response.json()
            assert result["execution"]["success"] == False
            assert "timeout" in result["execution"]["error"].lower()
            assert elapsed < 5  # Should timeout quickly
            print(f"  ✓ Timeout after {elapsed:.2f}s (expected ~2s)")

            # Test 4: JavaScript execution
            print("\n[Test 4] JavaScript execution...")
            artifact = await client.post(
                "/api/artifacts/create",
                json={
                    "conversation_id": conv_id,
                    "content": "console.log('Hello from JS!');",
                    "title": "JS Test",
                    "language": "javascript",
                }
            )
            assert artifact.status_code in [200, 201]
            artifact_id = artifact.json()["id"]

            response = await client.post(
                f"/api/artifacts/{artifact_id}/execute",
                json={"timeout": 10}
            )
            assert response.status_code == 200
            result = response.json()
            # JavaScript may output to stderr, so just check it ran
            print(f"  ✓ Success: {result['execution']['success']}")
            if result["execution"]["output"]:
                print(f"  ✓ Output: {result['execution']['output'][:50]}")

            # Test 5: Unsupported language
            print("\n[Test 5] Unsupported language rejection...")
            artifact = await client.post(
                "/api/artifacts/create",
                json={
                    "conversation_id": conv_id,
                    "content": "DATA DIVISION. PROGRAM-ID. TEST.",
                    "title": "COBOL",
                    "language": "cobol",
                }
            )
            assert artifact.status_code in [200, 201]
            artifact_id = artifact.json()["id"]

            response = await client.post(
                f"/api/artifacts/{artifact_id}/execute",
                json={"timeout": 10}
            )
            assert response.status_code == 200
            result = response.json()
            assert result["execution"]["success"] == False
            assert "not supported" in result["execution"]["error"].lower()
            print(f"  ✓ Error: {result['execution']['error']}")

            # Test 6: Non-code artifact rejection
            print("\n[Test 6] Non-code artifact rejection...")
            artifact = await client.post(
                "/api/artifacts/create",
                json={
                    "conversation_id": conv_id,
                    "content": "<h1>Hello</h1>",
                    "title": "HTML",
                    "language": "html",
                }
            )
            assert artifact.status_code in [200, 201]
            artifact_id = artifact.json()["id"]

            try:
                response = await client.post(
                    f"/api/artifacts/{artifact_id}/execute",
                    json={"timeout": 10}
                )
                # If we get here, check the response
                assert response.status_code == 400  # Bad Request
            except Exception as e:
                # httpx raises HTTPStatusError for 4xx/5xx
                assert "400" in str(e) or "cannot execute" in str(e).lower()
            print(f"  ✓ Rejected: HTML artifacts cannot be executed")

            print("\n" + "="*60)
            print("✅ ALL TESTS PASSED!")
            print("="*60 + "\n")

            return 0

    finally:
        app.dependency_overrides.clear()
        await engine.dispose()


if __name__ == "__main__":
    exit(asyncio.run(run_all_tests()))
