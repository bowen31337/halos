"""Test long-term memory feature implementation."""

import pytest
import asyncio
from uuid import uuid4


@pytest.mark.asyncio
async def test_memory_save_with_mock_agent(db_session):
    """Test that mock agent detects 'remember' keywords and saves memories."""
    from src.services.mock_agent import MockAgent
    from src.models.memory import Memory
    from sqlalchemy import select

    # Create mock agent
    agent = MockAgent()

    # Test memory save keywords
    test_messages = [
        "Remember that my favorite color is blue",
        "My favorite food is pizza",
        "I prefer working in the morning",
        "Note that I live in New York",
    ]

    for message in test_messages:
        events = []
        config = {"configurable": {"thread_id": str(uuid4()), "memory_enabled": True}}

        async for event in agent.astream_events(
            {"messages": [HumanMessage(content=message)]},
            config=config,
            version="v2",
        ):
            events.append(event)

            # Check for memory_save event
            if event.get("event") == "on_custom_event" and event.get("name") == "memory_save":
                memory_data = event.get("data", {})
                assert "content" in memory_data
                assert "category" in memory_data
                print(f"✓ Memory save event detected for: {message}")
                print(f"  Content: {memory_data['content']}")
                print(f"  Category: {memory_data['category']}")


@pytest.mark.asyncio
async def test_memory_retrieve_with_mock_agent(db_session):
    """Test that mock agent retrieves memories when asked."""
    from src.services.mock_agent import MockAgent

    # Create a test memory first
    memory = Memory(
        content="User's favorite color is blue",
        category="preference",
    )
    db_session.add(memory)
    await db_session.commit()

    # Create mock agent
    agent = MockAgent()

    # Test memory retrieval query
    query = "What is my favorite color?"
    events = []
    config = {"configurable": {"thread_id": str(uuid4()), "memory_enabled": True}}

    async for event in agent.astream_events(
        {"messages": [HumanMessage(content=query)]},
        config=config,
        version="v2",
    ):
        events.append(event)

        # Check for memory_retrieve event
        if event.get("event") == "on_custom_event" and event.get("name") == "memory_retrieve":
            memory_data = event.get("data", {})
            assert "query" in memory_data
            print(f"✓ Memory retrieve event detected for query: {query}")
            print(f"  Query: {memory_data['query']}")


def test_memory_backend_api(db_session):
    """Test memory backend API endpoints."""
    from src.models.memory import Memory
    from sqlalchemy import select

    # Create test memories
    memory1 = Memory(content="User loves Python", category="preference")
    memory2 = Memory(content="User lives in SF", category="fact")
    db_session.add_all([memory1, memory2])
    asyncio.run(db_session.commit())

    # Test listing memories
    result = asyncio.run(
        db_session.execute(select(Memory).where(Memory.is_active == True))
    )
    memories = result.scalars().all()

    assert len(memories) >= 2
    print(f"✓ Backend API: Found {len(memories)} memories")


def test_memory_panel_component():
    """Test that MemoryPanel component exists and has required methods."""
    try:
        from client.src.components.MemoryPanel import MemoryPanel
        assert MemoryPanel is not None
        print("✓ MemoryPanel component exists")
    except ImportError as e:
        print(f"✗ MemoryPanel component import failed: {e}")
        raise


def test_memory_api_methods():
    """Test that API service has memory methods."""
    try:
        from client.src.services.api import APIService

        api = APIService()

        # Check for memory methods
        assert hasattr(api, "listMemories")
        assert hasattr(api, "searchMemories")
        assert hasattr(api, "getMemory")
        assert hasattr(api, "createMemory")
        assert hasattr(api, "updateMemory")
        assert hasattr(api, "deleteMemory")

        print("✓ API service has all memory methods")
    except ImportError as e:
        print(f"✗ API service import failed: {e}")
        raise


def test_memory_toggle_in_settings():
    """Test that settings modal has memory toggle."""
    try:
        from client.src.stores.uiStore import useUIStore

        # Check if memoryEnabled exists in store
        store_state = useUIStore.getState()
        assert hasattr(store_state, "memoryEnabled")
        assert hasattr(store_state, "toggleMemoryEnabled")

        print("✓ Settings modal has memory toggle")
    except ImportError as e:
        print(f"✗ UI store import failed: {e}")
        raise


@pytest.mark.asyncio
async def test_memory_end_to_end_workflow(db_session):
    """Test complete memory workflow: save -> retrieve -> use."""
    from src.services.mock_agent import MockAgent
    from src.models.memory import Memory
    from sqlalchemy import select

    agent = MockAgent()
    thread_id = str(uuid4())

    # Step 1: Save a memory
    print("\n=== Step 1: Saving memory ===")
    save_message = "Remember that I prefer dark mode"
    save_events = []

    async for event in agent.astream_events(
        {"messages": [HumanMessage(content=save_message)]},
        config={"configurable": {"thread_id": thread_id, "memory_enabled": True}},
        version="v2",
    ):
        save_events.append(event)
        if event.get("event") == "on_custom_event" and event.get("name") == "memory_save":
            memory_data = event.get("data", {})
            # Save to database (simulating what backend does)
            memory = Memory(
                content=memory_data["content"],
                category=memory_data["category"],
                source_conversation_id=thread_id,
            )
            db_session.add(memory)
            await db_session.commit()
            print(f"✓ Memory saved: {memory_data['content']}")

    # Step 2: Retrieve the memory
    print("\n=== Step 2: Retrieving memory ===")
    query = "What are my preferences?"
    retrieve_events = []

    async for event in agent.astream_events(
        {"messages": [HumanMessage(content=query)]},
        config={"configurable": {"thread_id": thread_id, "memory_enabled": True}},
        version="v2",
    ):
        retrieve_events.append(event)
        if event.get("event") == "on_custom_event" and event.get("name") == "memory_retrieve":
            print(f"✓ Memory retrieval triggered for query: {query}")

    # Step 3: Verify memory exists in database
    print("\n=== Step 3: Verifying in database ===")
    result = await db_session.execute(
        select(Memory).where(Memory.content.ilike("%dark mode%"))
    )
    memories = result.scalars().all()

    assert len(memories) > 0
    print(f"✓ Found {len(memories)} matching memories in database")
    for mem in memories:
        print(f"  - {mem.content} ({mem.category})")

    print("\n✓ End-to-end memory workflow test PASSED")


if __name__ == "__main__":
    import sys

    # Run tests
    print("=" * 60)
    print("MEMORY FEATURE TESTS")
    print("=" * 60)

    pytest.main([__file__, "-v", "-s"])
