"""Simple test for SubAgent functionality."""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Remove API key for mock mode
if 'ANTHROPIC_API_KEY' in os.environ:
    del os.environ['ANTHROPIC_API_KEY']

from src.models.subagent import SubAgent, BUILTIN_SUBAGENTS
from src.services.mock_agent import MockAgent
from langchain_core.messages import HumanMessage
import asyncio


def test_subagent_model():
    """Test SubAgent model."""
    print("\n=== Testing SubAgent Model ===\n")

    # Test imports
    from src.models.subagent import SubAgent, BUILTIN_SUBAGENTS
    print("✓ SubAgent model imports correctly")

    # Test built-in agents
    assert len(BUILTIN_SUBAGENTS) == 4
    print(f"✓ {len(BUILTIN_SUBAGENTS)} built-in subagents defined")

    # Check names use hyphens
    for agent in BUILTIN_SUBAGENTS:
        assert '-' in agent['name'], f"Name should use hyphens: {agent['name']}"
        print(f"  - {agent['name']}: {agent['description'][:50]}...")

    print("\n✓ SubAgent model tests passed!\n")


def test_mock_agent():
    """Test MockAgent subagent delegation."""
    print("\n=== Testing MockAgent SubAgent Delegation ===\n")

    agent = MockAgent()

    async def test():
        # Test with "research" keyword
        messages = [HumanMessage(content="research the weather in Paris")]
        events = []

        async for event in agent.astream_events(
            {"messages": messages},
            {"configurable": {"thread_id": "test-1"}}
        ):
            events.append(event)

        # Check for subagent events (mock agent uses on_custom_event format)
        subagent_start = [e for e in events if e.get('event') == 'on_custom_event' and e.get('name') == 'subagent_start']
        subagent_end = [e for e in events if e.get('event') == 'on_custom_event' and e.get('name') == 'subagent_end']

        assert len(subagent_start) > 0, "Should emit subagent_start custom event"
        assert len(subagent_end) > 0, "Should emit subagent_end custom event"

        # Check name uses hyphens
        start_data = subagent_start[0].get('data', {})
        end_data = subagent_end[0].get('data', {})
        name = start_data.get('subagent')
        assert 'research-agent' == name, f"Expected 'research-agent', got '{name}'"

        print(f"✓ Subagent delegation triggered: {name}")
        print(f"✓ Reason: {start_data.get('reason', 'N/A')}")
        print(f"✓ Output: {end_data.get('output', 'N/A')[:80]}...")

    asyncio.run(test())
    print("\n✓ MockAgent tests passed!\n")


def test_api_structure():
    """Test that API routes exist."""
    print("\n=== Testing API Structure ===\n")

    # Check route file exists
    route_path = "/media/DATA/projects/autonomous-coding-clone-cc/talos/src/api/routes/subagents.py"
    assert os.path.exists(route_path), "SubAgent route file should exist"
    print("✓ SubAgent route file exists")

    # Check route is registered
    init_path = "/media/DATA/projects/autonomous-coding-clone-cc/talos/src/api/__init__.py"
    with open(init_path, 'r') as f:
        content = f.read()
    assert 'subagents' in content, "SubAgent routes should be imported"
    assert '/subagents' in content, "SubAgent routes should be registered"
    print("✓ SubAgent routes registered in API")

    print("\n✓ API structure tests passed!\n")


def test_frontend_structure():
    """Test that frontend components exist."""
    print("\n=== Testing Frontend Structure ===\n")

    # Check components
    components = [
        "/media/DATA/projects/autonomous-coding-clone-cc/talos/client/src/components/SubAgentModal.tsx",
        "/media/DATA/projects/autonomous-coding-clone-cc/talos/client/src/components/SubAgentIndicator.tsx",
    ]

    for component in components:
        assert os.path.exists(component), f"Component should exist: {component}"
        print(f"✓ {os.path.basename(component)} exists")

    # Check stores
    chatstore = "/media/DATA/projects/autonomous-coding-clone-cc/talos/client/src/stores/chatStore.ts"
    with open(chatstore, 'r') as f:
        content = f.read()
    assert 'SubAgentState' in content
    assert 'subAgent:' in content
    print("✓ chatStore has subagent state")

    # Check API service
    api = "/media/DATA/projects/autonomous-coding-clone-cc/talos/client/src/services/api.ts"
    with open(api, 'r') as f:
        content = f.read()
    assert 'getSubagents' in content
    assert 'createSubagent' in content
    print("✓ API service has subagent methods")

    print("\n✓ Frontend structure tests passed!\n")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("SUBAGENT FUNCTIONALITY TESTS")
    print("="*60)

    try:
        test_subagent_model()
        test_mock_agent()
        test_api_structure()
        test_frontend_structure()

        print("\n" + "="*60)
        print("ALL TESTS PASSED!")
        print("="*60 + "\n")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
