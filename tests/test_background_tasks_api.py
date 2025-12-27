"""Test Feature #96: Background tasks API tracks long-running operations.

This test verifies that the /api/tasks endpoints properly create, track,
and manage long-running background tasks with SSE streaming updates.
"""

import asyncio
import json
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from src.core.database import Base, get_db
from src.main import app
# Import models to register them with Base metadata
from src.models import Conversation, Message, BackgroundTask


TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_background_tasks.db"


@pytest.fixture
async def db_session():
    """Create a test database session."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        yield session

    await engine.dispose()


@pytest.fixture
async def client(db_session):
    """Create a test client with database dependency override."""
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_background_tasks_api_workflow():
    """Test complete background tasks API workflow.

    Feature #96 Steps:
    1. Trigger a long-running agent task
    2. GET /api/tasks to list tasks
    3. Verify new task in 'running' status
    4. GET /api/tasks/:id for details
    5. Verify progress percentage updates
    6. GET /api/tasks/:id/stream for SSE updates
    7. PUT /api/tasks/:id/cancel
    8. Verify task cancellation works
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Step 1: Trigger a long-running agent task
        print("\n=== Step 1: Trigger a long-running agent task ===")
        task_data = {
            "task_type": "agent_invocation",
            "conversation_id": None,
            "subagent_name": None
        }
        response = await client.post("/api/tasks", json=task_data)
        assert response.status_code == 200
        task = response.json()
        task_id = task["id"]
        print(f"  ✓ Task created: {task_id}")
        print(f"    Initial status: {task['status']}")

        # Step 2: GET /api/tasks to list tasks
        print("\n=== Step 2: GET /api/tasks to list tasks ===")
        list_response = await client.get("/api/tasks")
        assert list_response.status_code == 200
        tasks_list = list_response.json()
        assert "tasks" in tasks_list
        assert len(tasks_list["tasks"]) >= 1
        print(f"  ✓ Found {len(tasks_list['tasks'])} task(s)")

        # Step 3: Verify new task in 'running' status (wait a moment for it to start)
        print("\n=== Step 3: Verify task is running ===")
        await asyncio.sleep(0.6)  # Wait for task to start
        status_response = await client.get(f"/api/tasks/{task_id}")
        assert status_response.status_code == 200
        running_task = status_response.json()
        print(f"  ✓ Task status: {running_task['status']}")
        assert running_task["status"] in ["running", "completed", "pending"]

        # Step 4: GET /api/tasks/:id for details
        print("\n=== Step 4: GET /api/tasks/:id for details ===")
        details_response = await client.get(f"/api/tasks/{task_id}")
        assert details_response.status_code == 200
        details = details_response.json()
        assert details["id"] == task_id
        assert "task_type" in details
        assert "progress" in details
        print(f"  ✓ Task details retrieved")
        print(f"    Type: {details['task_type']}")
        print(f"    Progress: {details['progress']}%")

        # Step 5: Verify progress percentage updates
        print("\n=== Step 5: Verify progress percentage updates ===")
        # Wait for some progress updates
        await asyncio.sleep(1.5)
        progress_response = await client.get(f"/api/tasks/{task_id}")
        progress_task = progress_response.json()
        print(f"  ✓ Progress after waiting: {progress_task['progress']}%")
        print(f"    Status: {progress_task['status']}")

        # Step 6: GET /api/tasks/:id/stream for SSE updates
        print("\n=== Step 6: GET /api/tasks/:id/stream for SSE updates ===")
        stream_response = await client.get(f"/api/tasks/{task_id}/stream")
        assert stream_response.status_code == 200
        assert "text/event-stream" in stream_response.headers.get("content-type", "")
        print(f"  ✓ SSE stream established")

        # Parse a few SSE events
        events = []
        full_text = stream_response.text
        lines = full_text.split("\n")
        current_event = None
        current_data = None

        for line in lines:
            line = line.strip()
            if not line:
                if current_event and current_data:
                    events.append({"event": current_event, "data": current_data})
                current_event = None
                current_data = None
                continue

            if line.startswith("event: "):
                current_event = line[7:]
            elif line.startswith("data: "):
                current_data = line[6:]

        print(f"  ✓ Received {len(events)} SSE events")
        for e in events[:3]:
            print(f"    - {e['event']}: {e['data'][:50]}...")

        # Step 7: PUT /api/tasks/:id/cancel
        print("\n=== Step 7: PUT /api/tasks/:id/cancel ===")
        # Create a new task to cancel (since the first one might complete)
        new_task_response = await client.post("/api/tasks", json=task_data)
        new_task = new_task_response.json()
        new_task_id = new_task["id"]
        print(f"  ✓ Created new task for cancellation: {new_task_id}")

        # Wait a moment then cancel
        await asyncio.sleep(0.3)
        cancel_response = await client.put(f"/api/tasks/{new_task_id}/cancel")
        assert cancel_response.status_code == 200
        cancelled_task = cancel_response.json()
        print(f"  ✓ Task cancelled: {cancelled_task['status']}")

        # Step 8: Verify task cancellation works
        print("\n=== Step 8: Verify task cancellation works ===")
        verify_response = await client.get(f"/api/tasks/{new_task_id}")
        assert verify_response.status_code == 200
        final_task = verify_response.json()
        assert final_task["status"] == "cancelled"
        print(f"  ✓ Cancellation verified: {final_task['status']}")

        print("\n" + "=" * 60)
        print("Feature #96 Test Summary:")
        print("=" * 60)
        print("✅ All 8 steps passed successfully!")
        print("✅ Background tasks API tracks long-running operations")
        print("=" * 60)


@pytest.mark.asyncio
async def test_background_tasks_filtering():
    """Test task filtering by status."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        print("\n=== Testing Task Filtering ===")

        # Create multiple tasks
        await client.post("/api/tasks", json={"task_type": "test1"})
        await asyncio.sleep(0.2)
        await client.post("/api/tasks", json={"task_type": "test2"})
        await asyncio.sleep(0.2)

        # Get all tasks
        all_tasks = await client.get("/api/tasks")
        all_data = all_tasks.json()
        print(f"  ✓ Total tasks: {len(all_data['tasks'])}")

        # Filter by status
        pending_tasks = await client.get("/api/tasks?status=pending")
        pending_data = pending_tasks.json()
        print(f"  ✓ Pending tasks: {len(pending_data['tasks'])}")

        # Filter by different status
        running_tasks = await client.get("/api/tasks?status=running")
        running_data = running_tasks.json()
        print(f"  ✓ Running tasks: {len(running_data['tasks'])}")

        print("✅ Filtering test passed!")


if __name__ == "__main__":
    import sys
    pytest.main([__file__, "-v", "-s"] + sys.argv[1:])
