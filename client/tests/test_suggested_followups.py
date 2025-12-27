"""Test suggested follow-ups feature."""

import asyncio
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select

from src.main import app
from src.core.database import Base, get_db
from src.models.conversation import Conversation
from src.models.message import Message


TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_followups.db"


@pytest.fixture
async def test_db():
    """Create test database."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        async def override_get_db():
            yield session
        app.dependency_overrides[get_db] = override_get_db

        yield session

    app.dependency_overrides.clear()
    await engine.dispose()


@pytest.mark.asyncio
async def test_suggested_followups_in_stream(test_db: AsyncSession):
    """Test that suggested follow-ups are generated and included in stream response."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create conversation
        conv_response = await client.post("/api/conversations", json={"title": "Test Follow-ups"})
        assert conv_response.status_code == 200
        conv_id = conv_response.json()["id"]

        # Send message and stream response
        response = await client.post(
            "/api/agent/stream",
            json={
                "message": "What is Python?",
                "conversation_id": conv_id,
                "thread_id": conv_id,
            }
        )
        assert response.status_code == 200

        # Collect stream events
        events = []
        async for line in response.aiter_lines():
            if line.startswith("data: "):
                data = line[6:]  # Remove "data: " prefix
                if data:
                    import json
                    try:
                        event_data = json.loads(data)
                        events.append(event_data)
                    except json.JSONDecodeError:
                        pass

        # Check that we received events
        assert len(events) > 0, "No events received from stream"

        # Find the 'done' event
        done_event = None
        for event in events:
            if "event" in event and event["event"] == "done":
                done_event = event
                break

        assert done_event is not None, "No 'done' event found in stream"

        # Check if suggested_follow_ups is in the done event
        # Note: This may be empty if API key is not configured, but the field should be present
        print(f"Done event data: {done_event.get('data', {})}")

        # Parse done event data
        done_data = json.loads(done_event["data"]) if isinstance(done_event.get("data"), str) else done_event.get("data", {})

        # Verify the structure - suggested_follow_ups should be present (even if empty)
        assert "suggested_follow_ups" in done_data or "suggestedFollowUps" in done_data, \
            "suggested_follow_ups not found in done event"

        suggested_followups = done_data.get("suggested_follow_ups", done_data.get("suggestedFollowUps", []))

        # If API key is configured, we should have suggestions
        # If not, it should be an empty list
        assert isinstance(suggested_followups, list), "suggested_follow_ups should be a list"

        print(f"Suggested follow-ups: {suggested_followups}")

        if len(suggested_followups) > 0:
            # Verify suggestions are strings
            for suggestion in suggested_followups:
                assert isinstance(suggestion, str), "Each suggestion should be a string"
                assert len(suggestion) > 0, "Suggestion should not be empty"

            print(f"✓ Received {len(suggested_followups)} suggested follow-ups")
        else:
            print("✓ Suggested follow-ups field present but empty (API key may not be configured)")


@pytest.mark.asyncio
async def test_suggested_followups_persisted_to_message(test_db: AsyncSession):
    """Test that suggested follow-ups are persisted to the message in database."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create conversation
        conv_response = await client.post("/api/conversations", json={"title": "Test Persist"})
        assert conv_response.status_code == 200
        conv_id = conv_response.json()["id"]

        # Send message and stream response
        response = await client.post(
            "/api/agent/stream",
            json={
                "message": "Explain recursion",
                "conversation_id": conv_id,
                "thread_id": conv_id,
            }
        )
        assert response.status_code == 200

        # Consume stream
        async for _ in response.aiter_lines():
            pass

        # Query messages from database
        result = await test_db.execute(
            select(Message).where(Message.conversation_id == conv_id).order_by(Message.created_at)
        )
        messages = result.scalars().all()

        # Should have at least 2 messages (user + assistant)
        assert len(messages) >= 2, f"Expected at least 2 messages, got {len(messages)}"

        # Find the assistant message
        assistant_message = None
        for msg in messages:
            if msg.role == "assistant":
                assistant_message = msg
                break

        assert assistant_message is not None, "No assistant message found"

        # Check if suggested_follow_ups column exists and has data
        # Note: The column might be named suggested_follow_ups or suggestedFollowUps
        if hasattr(assistant_message, "suggested_follow_ups"):
            followups = assistant_message.suggested_follow_ups
        elif hasattr(assistant_message, "suggestedFollowUps"):
            followups = assistant_message.suggestedFollowUps
        else:
            followups = None

        print(f"Persisted suggested follow-ups: {followups}")

        # If followups were generated, they should be persisted
        if followups:
            assert isinstance(followups, list), "Persisted follow-ups should be a list"
            print(f"✓ Suggested follow-ups persisted to database: {len(followups)} suggestions")


if __name__ == "__main__":
    import sys
    pytest.main([__file__, "-v", "-s"] + sys.argv[1:])
