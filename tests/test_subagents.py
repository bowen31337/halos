"""Test SubAgent functionality.

This test verifies that the SubAgent system is properly integrated
including the database model, API routes, and frontend integration.
"""

import sys
import os
import asyncio
import json

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Ensure data directory exists
os.makedirs('/tmp/talos-data', exist_ok=True)

# Temporarily remove API key to force mock agent
original_api_key = os.environ.get('ANTHROPIC_API_KEY')
if 'ANTHROPIC_API_KEY' in os.environ:
    del os.environ['ANTHROPIC_API_KEY']
if 'ANTHROPIC_API_KEY_7' in os.environ:
    del os.environ['ANTHROPIC_API_KEY_7']

from src.core.config import settings
from src.core.database import init_db, get_db
from src.models.subagent import SubAgent, BUILTIN_SUBAGENTS
from src.services.mock_agent import MockAgent
from langchain_core.messages import HumanMessage
import asyncio


def test_subagent_model():
    """Test 1-5: Verify SubAgent model is properly defined."""
    print("\n=== Testing SubAgent Model ===\n")

    # Test 1: Model imports correctly
    from src.models.subagent import SubAgent
    print("✓ Step 1: SubAgent model imports correctly")

    # Test 2: Model has correct attributes
    assert hasattr(SubAgent, 'id')
    assert hasattr(SubAgent, 'user_id')
    assert hasattr(SubAgent, 'name')
    assert hasattr(SubAgent, 'description')
    assert hasattr(SubAgent, 'system_prompt')
    assert hasattr(SubAgent, 'model')
    assert hasattr(SubAgent, 'tools')
    assert hasattr(SubAgent, 'is_builtin')
    assert hasattr(SubAgent, 'is_active')
    print("✓ Step 2: SubAgent model has all required attributes")

    # Test 3: Built-in subagents are defined
    assert len(BUILTIN_SUBAGENTS) > 0
    print(f"✓ Step 3: {len(BUILTIN_SUBAGENTS)} built-in subagents defined")

    # Test 4: Built-in subagents have required fields
    for agent in BUILTIN_SUBAGENTS:
        assert 'name' in agent
        assert 'description' in agent
        assert 'system_prompt' in agent
        assert 'model' in agent
        assert 'tools' in agent
        assert 'is_builtin' in agent
    print("✓ Step 4: All built-in subagents have required fields")

    # Test 5: Built-in subagent names match expected format
    expected_names = ['research-agent', 'code-review-agent', 'documentation-agent', 'test-writing-agent']
    actual_names = [agent['name'] for agent in BUILTIN_SUBAGENTS]
    assert set(expected_names).issubset(set(actual_names))
    print(f"✓ Step 5: Built-in subagents include expected names: {expected_names}")

    print("\n✓ All SubAgent model tests passed!\n")


async def test_subagent_api_routes():
    """Test 6-12: Verify SubAgent API routes work correctly."""
    print("\n=== Testing SubAgent API Routes ===\n")

    from fastapi.testclient import TestClient
    from src.main import app

    client = TestClient(app)

    # Initialize database
    await init_db()

    # Test 6: Get built-in subagents
    response = client.get("/api/subagents/builtin")
    assert response.status_code == 200
    builtin_agents = response.json()
    assert len(builtin_agents) > 0
    print(f"✓ Step 6: GET /api/subagents/builtin returns {len(builtin_agents)} agents")

    # Test 7: Get all subagents (includes built-in)
    response = client.get("/api/subagents")
    assert response.status_code == 200
    all_agents = response.json()
    assert len(all_agents) >= len(builtin_agents)
    print(f"✓ Step 7: GET /api/subagents returns {len(all_agents)} agents")

    # Test 8: Create a custom subagent
    response = client.post("/api/subagents", json={
        "name": "test-custom-agent",
        "description": "A test custom agent",
        "system_prompt": "You are a test agent",
        "model": "claude-sonnet-4-5-20250929",
        "tools": ["read_file", "write_file"]
    })
    assert response.status_code == 201
    custom_agent = response.json()
    assert custom_agent['name'] == "test-custom-agent"
    assert custom_agent['is_builtin'] == False
    print("✓ Step 8: POST /api/subagents creates custom agent")

    # Test 9: Get the created custom agent
    agent_id = custom_agent['id']
    response = client.get(f"/api/subagents/{agent_id}")
    assert response.status_code == 200
    retrieved = response.json()
    assert retrieved['id'] == agent_id
    print("✓ Step 9: GET /api/subagents/{id} retrieves custom agent")

    # Test 10: Get subagent tools
    response = client.get(f"/api/subagents/{agent_id}/tools")
    assert response.status_code == 200
    tools = response.json()
    assert "read_file" in tools
    print(f"✓ Step 10: GET /api/subagents/{{id}}/tools returns {tools}")

    # Test 11: Update subagent
    response = client.put(f"/api/subagents/{agent_id}", json={
        "description": "Updated description"
    })
    assert response.status_code == 200
    updated = response.json()
    assert updated['description'] == "Updated description"
    print("✓ Step 11: PUT /api/subagents/{id} updates agent")

    # Test 12: Delete subagent
    response = client.delete(f"/api/subagents/{agent_id}")
    assert response.status_code == 204
    print("✓ Step 12: DELETE /api/subagents/{id} deletes agent")

    print("\n✓ All SubAgent API route tests passed!\n")


def test_mock_agent_subagent_delegation():
    """Test 13-16: Verify MockAgent supports subagent delegation."""
    print("\n=== Testing MockAgent SubAgent Delegation ===\n")

    agent = MockAgent()

    # Test 13: MockAgent has astream_events method
    assert hasattr(agent, 'astream_events')
    print("✓ Step 13: MockAgent has astream_events method")

    # Test 14: Subagent delegation via "research" keyword
    async def test_research():
        messages = [HumanMessage(content="research the weather")]
        events = []
        async for event in agent.astream_events({"messages": messages}, {"configurable": {"thread_id": "test-1"}}):
            events.append(event)

        # Check for subagent events (emitted as on_custom_event with name subagent_start)
        subagent_start = [e for e in events if e.get('event') == 'on_custom_event' and e.get('name') == 'subagent_start']
        subagent_end = [e for e in events if e.get('event') == 'on_custom_event' and e.get('name') == 'subagent_end']

        assert len(subagent_start) > 0, "Should emit subagent_start event"
        assert len(subagent_end) > 0, "Should emit subagent_end event"

        # Check the subagent name uses hyphens
        start_event = subagent_start[0]
        start_data = start_event.get('data', {})
        assert 'research-agent' in start_data.get('subagent', ''), f"Expected 'research-agent', got {start_data.get('subagent')}"

        return True

    result = asyncio.run(test_research())
    assert result
    print("✓ Step 14: MockAgent emits subagent events for 'research' keyword")

    # Test 15: Subagent delegation via "review" keyword
    async def test_review():
        messages = [HumanMessage(content="review this code")]
        events = []
        async for event in agent.astream_events({"messages": messages}, {"configurable": {"thread_id": "test-2"}}):
            events.append(event)

        subagent_start = [e for e in events if e.get('event') == 'on_custom_event' and e.get('name') == 'subagent_start']
        assert len(subagent_start) > 0

        # Should use code-review-agent
        start_event = subagent_start[0]
        start_data = start_event.get('data', {})
        assert 'code-review-agent' in start_data.get('subagent', ''), f"Expected 'code-review-agent', got {start_data.get('subagent')}"

        return True

    result = asyncio.run(test_review())
    assert result
    print("✓ Step 15: MockAgent emits subagent events for 'review' keyword")

    # Test 16: Subagent result is included in response
    async def test_result():
        messages = [HumanMessage(content="research something")]
        response_text = ""
        async for event in agent.astream_events({"messages": messages}, {"configurable": {"thread_id": "test-3"}}):
            if event.get('event') == 'on_chat_model_stream':
                chunk = event.get('data', {}).get('chunk')
                if chunk:
                    response_text += chunk.content

        assert 'subagent' in response_text.lower() or 'delegated' in response_text.lower()
        return True

    result = asyncio.run(test_result())
    assert result
    print("✓ Step 16: MockAgent includes subagent result in response")

    print("\n✓ All MockAgent subagent delegation tests passed!\n")


def test_frontend_integration():
    """Test 17-20: Verify frontend components are properly integrated."""
    print("\n=== Testing Frontend Integration ===\n")

    # Test 17: SubAgentModal component exists
    modal_path = "/media/DATA/projects/autonomous-coding-clone-cc/talos/client/src/components/SubAgentModal.tsx"
    assert os.path.exists(modal_path), "SubAgentModal.tsx should exist"
    print("✓ Step 17: SubAgentModal.tsx component exists")

    # Test 18: SubAgentIndicator component exists
    indicator_path = "/media/DATA/projects/autonomous-coding-clone-cc/talos/client/src/components/SubAgentIndicator.tsx"
    assert os.path.exists(indicator_path), "SubAgentIndicator.tsx should exist"
    print("✓ Step 18: SubAgentIndicator.tsx component exists")

    # Test 19: chatStore has subagent state
    chatstore_path = "/media/DATA/projects/autonomous-coding-clone-cc/talos/client/src/stores/chatStore.ts"
    with open(chatstore_path, 'r') as f:
        content = f.read()
    assert 'SubAgentState' in content, "SubAgentState interface should be defined"
    assert 'setSubAgentDelegated' in content, "setSubAgentDelegated action should exist"
    assert 'subAgent:' in content, "subAgent state should be initialized"
    print("✓ Step 19: chatStore has subagent state and actions")

    # Test 20: API service has subagent methods
    api_path = "/media/DATA/projects/autonomous-coding-clone-cc/talos/client/src/services/api.ts"
    with open(api_path, 'r') as f:
        content = f.read()
    assert 'getSubagents' in content, "getSubagents method should exist"
    assert 'createSubagent' in content, "createSubagent method should exist"
    assert 'getBuiltinSubagents' in content, "getBuiltinSubagents method should exist"
    print("✓ Step 20: API service has subagent methods")

    print("\n✓ All frontend integration tests passed!\n")


def main():
    """Run all subagent tests."""
    print("\n" + "="*60)
    print("SUBAGENT FUNCTIONALITY TEST SUITE")
    print("="*60)

    try:
        # Run model tests
        test_subagent_model()

        # Run API tests (async)
        asyncio.run(test_subagent_api_routes())

        # Run mock agent tests
        test_mock_agent_subagent_delegation()

        # Run frontend integration tests
        test_frontend_integration()

        print("\n" + "="*60)
        print("ALL SUBAGENT TESTS PASSED!")
        print("="*60 + "\n")

        return True

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
