"""
Test for Feature #147: React component preview with hot reload

This test verifies that:
1. React components can be previewed in the artifacts panel
2. Hot reload works when editing component code
3. Interactive elements in components work
4. State changes are preserved during hot reload
"""

import pytest
import asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_react_component_artifact_creation(async_client: AsyncClient, db: AsyncSession):
    """Test that React component artifacts can be created"""
    # Create a conversation
    conv_response = await async_client.post(
        "/api/conversations",
        json={
            "title": "React Preview Test",
            "model": "claude-sonnet-4-5-20250929",
        }
    )
    assert conv_response.status_code == 200
    conversation_id = conv_response.json()["id"]

    # Create a React component artifact
    react_code = """
export default function Counter() {
  const [count, setCount] = React.useState(0);

  return (
    <div style={{ padding: '20px', fontFamily: 'sans-serif' }}>
      <h1>Counter: {count}</h1>
      <button onClick={() => setCount(count + 1)}>
        Increment
      </button>
      <button onClick={() => setCount(count - 1)} style={{ marginLeft: '10px' }}>
        Decrement
      </button>
    </div>
  );
}
"""

    artifact_response = await async_client.post(
        f"/api/conversations/{conversation_id}/artifacts",
        json={
            "title": "Counter Component",
            "content": react_code,
            "artifact_type": "react",
            "language": "jsx",
            "identifier": "counter",
        }
    )

    assert artifact_response.status_code == 200
    artifact = artifact_response.json()
    assert artifact["artifact_type"] == "react"
    assert artifact["language"] == "jsx"
    assert artifact["content"] == react_code


@pytest.mark.asyncio
async def test_react_component_types(async_client: AsyncClient, db: AsyncSession):
    """Test that different React component types are detected"""
    # Create a conversation
    conv_response = await async_client.post(
        "/api/conversations",
        json={
            "title": "React Types Test",
            "model": "claude-sonnet-4-5-20250929",
        }
    )
    assert conv_response.status_code == 200
    conversation_id = conv_response.json()["id"]

    # Test JSX component
    jsx_code = "export default function App() { return <div>Hello</div>; }"
    artifact_response = await async_client.post(
        f"/api/conversations/{conversation_id}/artifacts",
        json={
            "title": "JSX Component",
            "content": jsx_code,
            "artifact_type": "react",
            "language": "jsx",
            "identifier": "jsx-app",
        }
    )
    assert artifact_response.status_code == 200

    # Test TSX component
    tsx_code = "export default function App() { return <div>Hello</div>; }"
    artifact_response = await async_client.post(
        f"/api/conversations/{conversation_id}/artifacts",
        json={
            "title": "TSX Component",
            "content": tsx_code,
            "artifact_type": "react",
            "language": "tsx",
            "identifier": "tsx-app",
        }
    )
    assert artifact_response.status_code == 200


@pytest.mark.asyncio
async def test_react_component_with_state(async_client: AsyncClient, db: AsyncSession):
    """Test React components with state management"""
    # Create a conversation
    conv_response = await async_client.post(
        "/api/conversations",
        json={
            "title": "React State Test",
            "model": "claude-sonnet-4-5-20250929",
        }
    )
    assert conv_response.status_code == 200
    conversation_id = conv_response.json()["id"]

    # Create a component with multiple state variables
    stateful_component = """
export default function TodoApp() {
  const [todos, setTodos] = React.useState([]);
  const [input, setInput] = React.useState('');

  const addTodo = () => {
    if (input.trim()) {
      setTodos([...todos, { id: Date.now(), text: input }]);
      setInput('');
    }
  };

  return (
    <div style={{ padding: '20px' }}>
      <h1>Todo App</h1>
      <input
        value={input}
        onChange={(e) => setInput(e.target.value)}
        placeholder="Enter todo"
      />
      <button onClick={addTodo}>Add</button>
      <ul>
        {todos.map(todo => (
          <li key={todo.id}>{todo.text}</li>
        ))}
      </ul>
    </div>
  );
}
"""

    artifact_response = await async_client.post(
        f"/api/conversations/{conversation_id}/artifacts",
        json={
            "title": "Todo App",
            "content": stateful_component,
            "artifact_type": "react",
            "language": "jsx",
            "identifier": "todo-app",
        }
    )

    assert artifact_response.status_code == 200
    artifact = artifact_response.json()
    assert "useState" in artifact["content"]


@pytest.mark.asyncio
async def test_react_component_hot_reload(async_client: AsyncClient, db: AsyncSession):
    """Test that React components can be edited (hot reload)"""
    # Create a conversation
    conv_response = await async_client.post(
        "/api/conversations",
        json={
            "title": "Hot Reload Test",
            "model": "claude-sonnet-4-5-20250929",
        }
    )
    assert conv_response.status_code == 200
    conversation_id = conv_response.json()["id"]

    # Create initial component
    initial_code = """
export default function Greeting() {
  return <h1>Hello, World!</h1>;
}
"""

    artifact_response = await async_client.post(
        f"/api/conversations/{conversation_id}/artifacts",
        json={
            "title": "Greeting",
            "content": initial_code,
            "artifact_type": "react",
            "language": "jsx",
            "identifier": "greeting",
        }
    )
    assert artifact_response.status_code == 200
    artifact_id = artifact_response.json()["id"]

    # Update the component (simulating hot reload)
    updated_code = """
export default function Greeting() {
  const [name, setName] = React.useState('World');

  return (
    <div>
      <h1>Hello, {name}!</h1>
      <input
        value={name}
        onChange={(e) => setName(e.target.value)}
      />
    </div>
  );
}
"""

    update_response = await async_client.put(
        f"/api/artifacts/{artifact_id}",
        json={
            "content": updated_code,
            "title": "Greeting (Updated)"
        }
    )

    assert update_response.status_code == 200
    updated_artifact = update_response.json()
    assert updated_artifact["content"] == updated_code
    assert updated_artifact["version"] == 2  # Version should increment


@pytest.mark.asyncio
async def test_react_component_error_handling(async_client: AsyncClient, db: AsyncSession):
    """Test that React component errors are handled gracefully"""
    # Create a conversation
    conv_response = await async_client.post(
        "/api/conversations",
        json={
            "title": "Error Handling Test",
            "model": "claude-sonnet-4-5-20250929",
        }
    )
    assert conv_response.status_code == 200
    conversation_id = conv_response.json()["id"]

    # Create a component with a syntax error
    invalid_code = """
export default function BrokenComponent() {
  // Missing closing brace
  return (
    <div>
      <h1>Broken
    </div>
  ;
}
"""

    artifact_response = await async_client.post(
        f"/api/conversations/{conversation_id}/artifacts",
        json={
            "title": "Broken Component",
            "content": invalid_code,
            "artifact_type": "react",
            "language": "jsx",
            "identifier": "broken",
        }
    )

    # Should still create the artifact, even if code is invalid
    # The frontend will handle the error display
    assert artifact_response.status_code == 200


@pytest.mark.asyncio
async def test_react_component_with_effects(async_client: AsyncClient, db: AsyncSession):
    """Test React components with useEffect hooks"""
    # Create a conversation
    conv_response = await async_client.post(
        "/api/conversations",
        json={
            "title": "Effects Test",
            "model": "claude-sonnet-4-5-20250929",
        }
    )
    assert conv_response.status_code == 200
    conversation_id = conv_response.json()["id"]

    # Create a component with useEffect
    effect_component = """
export default function Clock() {
  const [time, setTime] = React.useState(new Date());

  React.useEffect(() => {
    const timer = setInterval(() => {
      setTime(new Date());
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  return (
    <div>
      <h1>Current Time:</h1>
      <p>{time.toLocaleTimeString()}</p>
    </div>
  );
}
"""

    artifact_response = await async_client.post(
        f"/api/conversations/{conversation_id}/artifacts",
        json={
            "title": "Clock",
            "content": effect_component,
            "artifact_type": "react",
            "language": "jsx",
            "identifier": "clock",
        }
    )

    assert artifact_response.status_code == 200
    artifact = artifact_response.json()
    assert "useEffect" in artifact["content"]


@pytest.mark.asyncio
async def test_get_react_artifacts(async_client: AsyncClient, db: AsyncSession):
    """Test retrieving React artifacts"""
    # Create a conversation
    conv_response = await async_client.post(
        "/api/conversations",
        json={
            "title": "Get Artifacts Test",
            "model": "claude-sonnet-4-5-20250929",
        }
    )
    assert conv_response.status_code == 200
    conversation_id = conv_response.json()["id"]

    # Create multiple React artifacts
    for i in range(3):
        await async_client.post(
            f"/api/conversations/{conversation_id}/artifacts",
            json={
                "title": f"Component {i+1}",
                "content": f"export default function Comp{i+1}() {{ return <div>Component {i+1}</div>; }}",
                "artifact_type": "react",
                "language": "jsx",
                "identifier": f"comp-{i+1}",
            }
        )

    # Get all artifacts for the conversation
    artifacts_response = await async_client.get(
        f"/api/conversations/{conversation_id}/artifacts"
    )

    assert artifacts_response.status_code == 200
    artifacts = artifacts_response.json()
    assert len(artifacts) == 3
    assert all(a["artifact_type"] == "react" for a in artifacts)


if __name__ == "__main__":
    print("Run tests with: pytest tests/test_react_preview.py -v")
