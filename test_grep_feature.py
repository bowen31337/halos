"""Test Feature #178: Grep search finds patterns within files

This test verifies that the grep tool is available and working in the agent.
"""

import asyncio
import sys
from langchain_core.messages import HumanMessage

# Add src to path
sys.path.insert(0, '.')

from src.services.agent_service import agent_service


async def test_grep_tool():
    """Test that the agent can use grep to search file contents."""

    print("=" * 60)
    print("Testing Feature #178: Grep Search")
    print("=" * 60)

    # Create an agent
    print("\n1. Creating agent...")
    agent = agent_service.create_agent(
        user_id="test",
        permission_mode="auto",  # No approvals needed for testing
    )
    print(f"✓ Agent created: {type(agent).__name__}")

    # Test message that should trigger grep usage
    test_message = "Search for 'main' in all files using grep"

    print(f"\n2. Sending message: '{test_message}'")
    print("\n3. Streaming response...")

    # Track if grep tool is called
    grep_called = False
    grep_pattern = None

    try:
        config = {
            "configurable": {
                "thread_id": "test_grep_thread",
                "permission_mode": "auto",
            }
        }

        events = []
        async for event in agent.astream_events(
            {"messages": [HumanMessage(content=test_message)]},
            config=config,
            version="v2"
        ):
            events.append(event)
            event_kind = event.get("event", "")
            event_name = event.get("name", "")

            # Check for tool calls
            if event_kind == "on_tool_start":
                tool_name = event_name
                print(f"\n   📦 Tool called: {tool_name}")

                if tool_name == "grep":
                    grep_called = True
                    tool_input = event.get("data", {}).get("input", {})
                    grep_pattern = tool_input.get("pattern", "")
                    print(f"   ✓ GREP tool detected!")
                    print(f"   Pattern: {grep_pattern}")

            # Check for streaming content
            elif event_kind == "on_chat_model_stream":
                chunk = event.get("data", {}).get("chunk", {})
                content = chunk.content if hasattr(chunk, 'content') else ""
                if content:
                    print(content, end="", flush=True)

            # Check for completion
            elif event_kind == "on_chain_end":
                tokens = event.get("data", {})
                print(f"\n\n✓ Response complete")
                print(f"   Input tokens: {tokens.get('input_tokens', 'N/A')}")
                print(f"   Output tokens: {tokens.get('output_tokens', 'N/A')}")

        # Verification
        print("\n" + "=" * 60)
        print("VERIFICATION RESULTS:")
        print("=" * 60)

        if grep_called:
            print("✅ PASS: Grep tool was called by the agent")
            if grep_pattern:
                print(f"✅ PASS: Grep pattern was used: {grep_pattern}")
            else:
                print("⚠️  WARNING: Grep was called but no pattern detected")
        else:
            print("❌ FAIL: Grep tool was NOT called by the agent")
            print("   Note: This may be expected if agent chose a different approach")

        # Test different grep patterns
        print("\n" + "=" * 60)
        print("Testing specific grep patterns...")
        print("=" * 60)

        test_patterns = [
            ("Find all references to 'def' in files", "def"),
            ("Search for 'import' statements", "import"),
            ("Find 'TODO' comments", "TODO"),
        ]

        for description, expected_pattern in test_patterns:
            print(f"\nTest: {description}")
            print(f"Expected pattern: {expected_pattern}")

            async for event in agent.astream_events(
                {"messages": [HumanMessage(content=description)]},
                config={"configurable": {f"thread_id": f"test_grep_{expected_pattern}"}},
                version="v2"
            ):
                if event.get("event") == "on_tool_start" and event.get("name") == "grep":
                    tool_input = event.get("data", {}).get("input", {})
                    pattern = tool_input.get("pattern", "")
                    print(f"   Actual pattern: {pattern}")
                    break

        print("\n" + "=" * 60)
        print("FEATURE #178 TEST COMPLETE")
        print("=" * 60)

        return grep_called

    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    result = asyncio.run(test_grep_tool())
    sys.exit(0 if result else 1)
