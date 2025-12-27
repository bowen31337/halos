"""Simple test for code execution endpoint."""

import asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from src.main import app
from src.core.database import get_db, Base


async def test_execute_endpoint():
    """Test the execute endpoint works."""
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
            # Create conversation
            conv = await client.post("/api/conversations", json={"title": "Test"})
            print(f"1. Create conversation: {conv.status_code}")
            assert conv.status_code in [200, 201]
            conv_id = conv.json()["id"]

            # Create artifact
            artifact = await client.post(
                "/api/artifacts/create",
                json={
                    "conversation_id": conv_id,
                    "content": 'print("Hello from sandbox!")',
                    "title": "TestScript",
                    "language": "python",
                }
            )
            print(f"2. Create artifact: {artifact.status_code}")
            assert artifact.status_code in [200, 201]
            artifact_data = artifact.json()
            artifact_id = artifact_data["id"]
            print(f"   Artifact ID: {artifact_id}")
            print(f"   Artifact type: {artifact_data.get('artifact_type')}")

            # Execute code
            response = await client.post(
                f"/api/artifacts/{artifact_id}/execute",
                json={"timeout": 10}
            )
            print(f"3. Execute code: {response.status_code}")
            assert response.status_code == 200

            result = response.json()
            print(f"   Success: {result['execution']['success']}")
            print(f"   Output: {result['execution']['output']}")
            print(f"   Time: {result['execution']['execution_time']}s")

            assert result["execution"]["success"] == True
            assert "Hello from sandbox!" in result["execution"]["output"]

            print("\n✅ Code execution test PASSED!")

    finally:
        app.dependency_overrides.clear()
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(test_execute_endpoint())
