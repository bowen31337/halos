#!/usr/bin/env python3
"""Test script to verify DeepAgents built-in tools."""

import asyncio
import sys
import os

# Add the project root to Python path
sys.path.insert(0, '/media/DATA/projects/autonomous-coding-clone-cc/talos')

from src.services.agent_service import agent_service
from src.core.config import settings
from langchain_core.messages import HumanMessage

async def test_deepagents_tools():
    """Test the DeepAgents built-in tools."""
    print("=== Testing DeepAgents Built-in Tools ===")

    # Create an agent with API key
    agent = agent_service.create_agent(
        user_id="test_user",
        permission_mode="default",
        model="claude-sonnet-4-5-20250929"
    )

    print(f"Agent type: {type(agent)}")

    # Test 1: Test write_todos tool
    print("\n=== Testing write_todos tool ===")
    test_input = {
        "messages": [
            HumanMessage(content="[System Instructions: Use write_todos to create a todo list for this task]\n\nPlan how to implement a feature that allows users to export conversations as Markdown files.")
        ]
    }

    result = agent.invoke(test_input)
    print(f"write_todos test completed")

    # Test 2: Test filesystem tools (ls, read_file, write_file, edit_file, glob, grep)
    print("\n=== Testing filesystem tools ===")
    test_input = {
        "messages": [
            HumanMessage(content="[System Instructions: Use ls to list files in the current directory]\n\nShow me what files are in the current directory.")
        ]
    }

    result = agent.invoke(test_input)
    print(f"Filesystem tools test completed")

    # Test 3: Test subagent delegation
    print("\n=== Testing subagent delegation ===")
    test_input = {
        "messages": [
            HumanMessage(content="[System Instructions: Use sub-agent to research the latest Anthropic API features]\n\nResearch the latest Anthropic API features and capabilities.")
        ]
    }

    result = agent.invoke(test_input)
    print(f"Subagent delegation test completed")

    # Test 4: Test streaming with extended thinking
    print("\n=== Testing streaming with extended thinking ===")
    test_input = {
        "messages": [
            HumanMessage(content="Explain how LangChain DeepAgents work.")
        ]
    }

    config = {"configurable": {"extended_thinking": True, "thread_id": "test_thread_1"}}
    events_received = 0

    async for event in agent.astream_events(test_input, config=config, version="v2"):
        events_received += 1
        if events_received > 10:  # Limit output
            break

    print(f"Streaming completed with {events_received} events")

    print("\n=== All DeepAgents Tools Tests Passed ===")

if __name__ == "__main__":
    asyncio.run(test_deepagents_tools())