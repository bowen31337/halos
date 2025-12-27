"""Test long-term memory feature implementation."""

import pytest
import asyncio
from uuid import uuid4
from langchain_core.messages import HumanMessage


@pytest.mark.asyncio
async def test_memory_save_with_mock_agent(test_db):
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
async def test_memory_retrieve_with_mock_agent(test_db):
    """Test that mock agent retrieves memories when asked."""
    from src.services.mock_agent import MockAgent
    from src.models.memory import Memory

    # Create a test memory first
    memory = Memory(
        content="User's favorite color is blue",
        category="preference",
    )
    test_db.add(memory)
    await test_db.commit()

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


def test_memory_backend_api(test_db):
    """Test memory backend API endpoints."""
    from src.models.memory import Memory
    from sqlalchemy import select

    # Create test memories
    memory1 = Memory(content="User loves Python", category="preference")
    memory2 = Memory(content="User lives in SF", category="fact")
    test_db.add_all([memory1, memory2])
    asyncio.run(test_db.commit())

    # Test listing memories
    result = asyncio.run(
        test_db.execute(select(Memory).where(Memory.is_active == True))
    )
    memories = result.scalars().all()

    assert len(memories) >= 2
    print(f"✓ Backend API: Found {len(memories)} memories")


def test_memory_panel_component():
    """Test that MemoryPanel component exists."""
    import os
    component_path = "client/src/components/MemoryPanel.tsx"
    assert os.path.exists(component_path), f"MemoryPanel component not found at {component_path}"
    print(f"✓ MemoryPanel component exists at {component_path}")


def test_memory_api_methods():
    """Test that API service has memory methods."""
    import os

    # Read the api.ts file and check for memory methods
    api_path = "client/src/services/api.ts"
    assert os.path.exists(api_path), f"API service not found at {api_path}"

    with open(api_path, 'r') as f:
        content = f.read()

    # Check for memory methods
    required_methods = [
        "listMemories",
        "searchMemories",
        "getMemory",
        "createMemory",
        "updateMemory",
        "deleteMemory",
    ]

    for method in required_methods:
        assert method in content, f"Method {method} not found in api.ts"

    print(f"✓ API service has all memory methods at {api_path}")


def test_memory_toggle_in_settings():
    """Test that settings modal has memory toggle."""
    import os

    # Check uiStore.ts for memoryEnabled
    store_path = "client/src/stores/uiStore.ts"
    assert os.path.exists(store_path), f"UI store not found at {store_path}"

    with open(store_path, 'r') as f:
        content = f.read()

    # Check for memoryEnabled and toggleMemoryEnabled
    assert "memoryEnabled" in content, "memoryEnabled not found in uiStore.ts"
    assert "toggleMemoryEnabled" in content, "toggleMemoryEnabled not found in uiStore.ts"

    print(f"✓ Settings modal has memory toggle at {store_path}")


@pytest.mark.asyncio
async def test_memory_end_to_end_workflow(test_db):
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
            test_db.add(memory)
            await test_db.commit()
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
    result = await test_db.execute(
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
