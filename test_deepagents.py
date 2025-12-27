#!/usr/bin/env python3
"""Test script to verify DeepAgents integration."""

import asyncio
import sys
import os

# Add the project root to Python path
sys.path.insert(0, '/media/DATA/projects/autonomous-coding-clone-cc/talos')

from src.services.agent_service import agent_service
from src.core.config import settings

async def test_deepagents():
    """Test the DeepAgents integration."""
    print("=== Testing DeepAgents Integration ===")

    # Test 1: Check if API key is available
    api_key = settings.get_anthropic_api_key()
    print(f"API Key available: {bool(api_key)}")
    if api_key:
        print(f"API Key length: {len(api_key)}")

    # Test 2: Create an agent
    print("\n=== Creating Agent ===")
    try:
        agent = agent_service.create_agent(
            user_id="test_user",
            permission_mode="default",
            model="claude-sonnet-4-5-20250929"
        )
        print(f"✓ Agent created successfully: {type(agent)}")

        # Test 3: Check agent tools
        print("\n=== Checking Agent Tools ===")
        if hasattr(agent, 'tools'):
            print(f"Agent tools: {agent.tools}")
        else:
            print("Agent tools not directly accessible")

        # Test 4: Test synchronous invoke
        print("\n=== Testing Synchronous Invoke ===")
        from langchain_core.messages import HumanMessage
        test_input = {"messages": [HumanMessage(content="Hello, how are you?")]}
        result = agent.invoke(test_input)
        print(f"✓ Synchronous invoke successful")
        print(f"Result type: {type(result)}")
        if hasattr(result, 'get'):
            print(f"Result keys: {list(result.keys())}")

        # Test 5: Test streaming
        print("\n=== Testing Streaming ===")
        async for event in agent.astream_events(test_input, version="v2"):
            print(f"Event: {event.get('event', 'unknown')}")
            if event.get('event') == 'on_chat_model_stream':
                print("✓ Streaming event received")
                break

        print("\n=== All Tests Passed ===")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_deepagents())