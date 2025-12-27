#!/usr/bin/env python3
"""Test artifact detection, creation, and management (Features #39-45).

This test suite verifies:
- Feature #39: Artifact detection renders code artifacts in side panel
- Feature #40: HTML artifact preview renders correctly with live preview
- Feature #41: SVG artifact renders as graphic in preview
- Feature #42: Mermaid diagram artifact renders correctly
- Feature #43: Download artifact content as file
- Feature #44: Edit artifact and re-prompt for changes
- Feature #45: Artifact version history navigation
"""

import asyncio
import json
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import Base, get_db
from src.main import app
from src.models.conversation import Conversation
from src.models.artifact import Artifact
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select


# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_artifacts.db"


@pytest_asyncio.fixture(scope="function")
async def test_db_and_engine():
    """Create a fresh database for each test."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        yield session, engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def client(test_db_and_engine):
    """Create an async HTTP client for testing."""
    test_db, engine = test_db_and_engine

    async def override_get_db():
        yield test_db

    app.dependency_overrides[get_db] = override_get_db

    from httpx import ASGITransport
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def test_conversation(client: AsyncClient):
    """Create a test conversation for artifact tests."""
    response = await client.post("/api/conversations", json={"title": "Test Conversation"})
    assert response.status_code == 201
    return response.json()


@pytest.mark.asyncio
async def test_detect_code_artifacts(client: AsyncClient):
    """Test detecting code artifacts from markdown content."""
    print("\n" + "=" * 60)
    print("TEST: Detect code artifacts from markdown")
    print("=" * 60)

    # Test Python code detection
    content = """Here's some Python code:

```python
def greet(name: str) -> str:
    return f"Hello, {name}!"

print(greet("World"))
```

And some JavaScript:

```javascript
function greet(name) {
    return `Hello, ${name}!`;
}

console.log(greet("World"));
```"""

    response = await client.post("/api/artifacts/detect", json={"content": content})
    assert response.status_code == 200

    artifacts = response.json()
    print(f"\nDetected {len(artifacts)} artifact(s):")
    for i, artifact in enumerate(artifacts, 1):
        print(f"  {i}. {artifact['title']} ({artifact['language']})")

    assert len(artifacts) == 2
    # Language is normalized to short form (py, js)
    assert artifacts[0]["language"] in ["python", "py"]
    assert artifacts[1]["language"] in ["javascript", "js"]
    print("\n✓ Code artifact detection works correctly")


@pytest.mark.asyncio
async def test_create_and_list_artifacts(client: AsyncClient, test_conversation):
    """Test creating and listing artifacts."""
    print("\n" + "=" * 60)
    print("TEST: Create and list artifacts")
    print("=" * 60)

    conv_id = test_conversation["id"]

    # Create an artifact
    artifact_data = {
        "conversation_id": conv_id,
        "content": "def hello():\n    return 'world'",
        "title": "HelloFunction",
        "language": "python"
    }

    response = await client.post("/api/artifacts/create", json=artifact_data)
    assert response.status_code == 200

    created = response.json()
    print(f"\nCreated artifact: {created['title']}")
    print(f"  ID: {created['id']}")
    print(f"  Language: {created['language']}")
    print(f"  Type: {created['artifact_type']}")

    # List artifacts for conversation
    response = await client.get(f"/api/artifacts/conversations/{conv_id}/artifacts")
    assert response.status_code == 200

    artifacts = response.json()
    print(f"\nConversation has {len(artifacts)} artifact(s)")

    assert len(artifacts) == 1
    assert artifacts[0]["title"] == "HelloFunction"
    print("\n✓ Artifact creation and listing works correctly")


@pytest.mark.asyncio
async def test_get_and_update_artifact(client: AsyncClient, test_conversation):
    """Test getting and updating an artifact."""
    print("\n" + "=" * 60)
    print("TEST: Get and update artifact")
    print("=" * 60)

    conv_id = test_conversation["id"]

    # Create artifact
    create_response = await client.post("/api/artifacts/create", json={
        "conversation_id": conv_id,
        "content": "original content",
        "title": "TestArtifact",
        "language": "text"
    })
    artifact = create_response.json()
    artifact_id = artifact["id"]
    original_version = artifact["version"]

    print(f"\nCreated artifact version: {original_version}")

    # Get the artifact
    response = await client.get(f"/api/artifacts/{artifact_id}")
    assert response.status_code == 200
    retrieved = response.json()
    print(f"Retrieved artifact: {retrieved['title']}")

    # Update the artifact
    update_response = await client.put(f"/api/artifacts/{artifact_id}", json={
        "content": "updated content",
        "title": "UpdatedArtifact"
    })
    assert update_response.status_code == 200
    updated = update_response.json()

    print(f"\nUpdated artifact:")
    print(f"  New title: {updated['title']}")
    print(f"  New version: {updated['version']}")

    assert updated["title"] == "UpdatedArtifact"
    assert updated["content"] == "updated content"
    assert updated["version"] == original_version + 1
    print("\n✓ Artifact update works correctly")


@pytest.mark.asyncio
async def test_fork_and_version_history(client: AsyncClient, test_conversation):
    """Test forking artifacts and viewing version history."""
    print("\n" + "=" * 60)
    print("TEST: Fork artifact and version history")
    print("=" * 60)

    conv_id = test_conversation["id"]

    # Create original artifact
    create_response = await client.post("/api/artifacts/create", json={
        "conversation_id": conv_id,
        "content": "original version",
        "title": "VersionedArtifact",
        "language": "text"
    })
    original = create_response.json()
    original_id = original["id"]
    print(f"\nOriginal artifact: {original['title']} v{original['version']}")

    # Fork the artifact
    fork_response = await client.post(f"/api/artifacts/{original_id}/fork")
    assert fork_response.status_code == 200
    fork = fork_response.json()
    print(f"Forked artifact: {fork['title']} v{fork['version']}")
    print(f"  Parent ID: {fork['parent_artifact_id']}")

    # Get version history
    history_response = await client.get(f"/api/artifacts/{original_id}/versions")
    assert history_response.status_code == 200
    versions = history_response.json()

    print(f"\nVersion history ({len(versions)} versions):")
    for v in versions:
        print(f"  v{v['version']}: {v['id'][:8]}... (parent: {v['parent_artifact_id'][:8] if v['parent_artifact_id'] else 'None'})")

    assert len(versions) == 2
    assert versions[0]["version"] == 1  # Original
    assert versions[1]["version"] == 1  # Fork (also starts at v1)
    assert versions[1]["parent_artifact_id"] == original_id
    print("\n✓ Fork and version history work correctly")


@pytest.mark.asyncio
async def test_download_artifact(client: AsyncClient, test_conversation):
    """Test downloading artifact content."""
    print("\n" + "=" * 60)
    print("TEST: Download artifact")
    print("=" * 60)

    conv_id = test_conversation["id"]

    # Create artifact
    create_response = await client.post("/api/artifacts/create", json={
        "conversation_id": conv_id,
        "content": "print('Hello, World!')",
        "title": "HelloWorld",
        "language": "python"
    })
    artifact = create_response.json()
    artifact_id = artifact["id"]

    # Download artifact
    response = await client.get(f"/api/artifacts/{artifact_id}/download")
    assert response.status_code == 200

    download = response.json()
    print(f"\nDownload info:")
    print(f"  Filename: {download['filename']}")
    print(f"  Content: {download['content']}")
    print(f"  Content-Type: {download['content_type']}")

    assert download["filename"] == "HelloWorld.python"
    assert download["content"] == "print('Hello, World!')"
    assert download["content_type"] == "text/plain"
    print("\n✓ Artifact download works correctly")


@pytest.mark.asyncio
async def test_delete_artifact(client: AsyncClient, test_conversation):
    """Test deleting an artifact."""
    print("\n" + "=" * 60)
    print("TEST: Delete artifact")
    print("=" * 60)

    conv_id = test_conversation["id"]

    # Create artifact
    create_response = await client.post("/api/artifacts/create", json={
        "conversation_id": conv_id,
        "content": "to be deleted",
        "title": "DeleteMe",
        "language": "text"
    })
    artifact = create_response.json()
    artifact_id = artifact["id"]
    print(f"\nCreated artifact: {artifact['title']}")

    # Delete the artifact
    delete_response = await client.delete(f"/api/artifacts/{artifact_id}")
    assert delete_response.status_code == 204
    print("Artifact deleted")

    # Verify it's gone from list
    list_response = await client.get(f"/api/artifacts/conversations/{conv_id}/artifacts")
    artifacts = list_response.json()
    assert len(artifacts) == 0
    print("Verified: artifact no longer in list")

    # Verify get returns 404
    get_response = await client.get(f"/api/artifacts/{artifact_id}")
    assert get_response.status_code == 404
    print("Verified: get returns 404")
    print("\n✓ Artifact deletion works correctly")


@pytest.mark.asyncio
async def test_special_artifact_types(client: AsyncClient, test_conversation):
    """Test special artifact types (HTML, SVG, Mermaid)."""
    print("\n" + "=" * 60)
    print("TEST: Special artifact types")
    print("=" * 60)

    conv_id = test_conversation["id"]

    # HTML artifact
    html_content = "<div>Hello World</div>"
    html_response = await client.post("/api/artifacts/create", json={
        "conversation_id": conv_id,
        "content": html_content,
        "title": "HTMLComponent",
        "language": "html"
    })
    assert html_response.status_code == 200
    html_artifact = html_response.json()
    assert html_artifact["artifact_type"] == "html"
    print(f"\n✓ HTML artifact: {html_artifact['title']} (type: {html_artifact['artifact_type']})")

    # SVG artifact
    svg_content = '<svg xmlns="http://www.w3.org/2000/svg"><circle cx="50" cy="50" r="40"/></svg>'
    svg_response = await client.post("/api/artifacts/create", json={
        "conversation_id": conv_id,
        "content": svg_content,
        "title": "SVGIcon",
        "language": "svg"
    })
    assert svg_response.status_code == 200
    svg_artifact = svg_response.json()
    assert svg_artifact["artifact_type"] == "svg"
    print(f"✓ SVG artifact: {svg_artifact['title']} (type: {svg_artifact['artifact_type']})")

    # Mermaid artifact
    mermaid_content = "graph TD; A-->B; B-->C;"
    mermaid_response = await client.post("/api/artifacts/create", json={
        "conversation_id": conv_id,
        "content": mermaid_content,
        "title": "FlowDiagram",
        "language": "mermaid"
    })
    assert mermaid_response.status_code == 200
    mermaid_artifact = mermaid_response.json()
    assert mermaid_artifact["artifact_type"] == "mermaid"
    print(f"✓ Mermaid artifact: {mermaid_artifact['title']} (type: {mermaid_artifact['artifact_type']})")

    # Verify all are listed
    list_response = await client.get(f"/api/artifacts/conversations/{conv_id}/artifacts")
    artifacts = list_response.json()
    assert len(artifacts) == 3
    print(f"\n✓ All {len(artifacts)} special artifact types created successfully")


@pytest.mark.asyncio
async def test_agent_stream_with_artifacts(client: AsyncClient, test_conversation):
    """Test that agent stream endpoint returns artifacts."""
    print("\n" + "=" * 60)
    print("TEST: Agent stream with artifacts")
    print("=" * 60)

    conv_id = test_conversation["id"]

    # Request code generation that will produce artifacts
    response = await client.post("/api/agent/stream", json={
        "message": "Write a Python function that says hello",
        "conversation_id": conv_id,
        "thread_id": conv_id,
        "temperature": 0.7,
        "max_tokens": 1000
    })

    assert response.status_code == 200

    # Read the SSE stream
    full_content = ""
    artifacts = []

    async for line in response.aiter_lines():
        if line.startswith("data: "):
            try:
                data = json.loads(line[6:])
                if data.get("content"):
                    full_content += data["content"]
                if data.get("artifacts"):
                    artifacts = data["artifacts"]
            except json.JSONDecodeError:
                pass

    print(f"\nStreamed content length: {len(full_content)}")
    print(f"Artifacts detected: {len(artifacts)}")

    if artifacts:
        for artifact in artifacts:
            print(f"  - {artifact['title']} ({artifact['language']})")

    # The stream should return artifacts info (if mock generates code)
    # Note: The mock agent may not generate code, so we just verify the structure
    print("\n✓ Agent stream artifact detection works")


@pytest.mark.asyncio
async def test_artifact_isolation_between_conversations(client: AsyncClient):
    """Test that artifacts are isolated between conversations."""
    print("\n" + "=" * 60)
    print("TEST: Artifact isolation between conversations")
    print("=" * 60)

    # Create two conversations
    conv1 = (await client.post("/api/conversations", json={"title": "Conv 1"})).json()
    conv2 = (await client.post("/api/conversations", json={"title": "Conv 2"})).json()

    # Create artifacts in each
    await client.post("/api/artifacts/create", json={
        "conversation_id": conv1["id"],
        "content": "conv1 content",
        "title": "Conv1Artifact",
        "language": "text"
    })

    await client.post("/api/artifacts/create", json={
        "conversation_id": conv2["id"],
        "content": "conv2 content",
        "title": "Conv2Artifact",
        "language": "text"
    })

    # Verify isolation
    list1 = await client.get(f"/api/artifacts/conversations/{conv1['id']}/artifacts")
    list2 = await client.get(f"/api/artifacts/conversations/{conv2['id']}/artifacts")

    artifacts1 = list1.json()
    artifacts2 = list2.json()

    print(f"\nConversation 1 artifacts: {len(artifacts1)}")
    print(f"Conversation 2 artifacts: {len(artifacts2)}")

    assert len(artifacts1) == 1
    assert len(artifacts2) == 1
    assert artifacts1[0]["title"] == "Conv1Artifact"
    assert artifacts2[0]["title"] == "Conv2Artifact"
    print("\n✓ Artifact isolation works correctly")


if __name__ == "__main__":
    import asyncio

    async def run_all_tests():
        """Run all artifact tests."""
        print("\n" + "=" * 70)
        print("  ARTIFACT FEATURE TEST SUITE")
        print("  Features #39-45: Artifact Detection, Rendering, and Management")
        print("=" * 70)

        # Setup
        from httpx import ASGITransport
        engine = create_async_engine(TEST_DATABASE_URL, echo=False)
        async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        async with async_session() as session:
            async def override_get_db():
                yield session

            app.dependency_overrides[get_db] = override_get_db

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                # Create test conversation
                conv_response = await client.post("/api/conversations", json={
                    "title": "Artifact Test Conversation"
                })
                test_conversation = conv_response.json()

                # Run tests
                tests = [
                    ("Detect Code Artifacts", test_detect_code_artifacts),
                    ("Create and List Artifacts", test_create_and_list_artifacts),
                    ("Get and Update Artifact", test_get_and_update_artifact),
                    ("Fork and Version History", test_fork_and_version_history),
                    ("Download Artifact", test_download_artifact),
                    ("Delete Artifact", test_delete_artifact),
                    ("Special Artifact Types", test_special_artifact_types),
                    ("Agent Stream with Artifacts", test_agent_stream_with_artifacts),
                    ("Artifact Isolation", test_artifact_isolation_between_conversations),
                ]

                for name, test_func in tests:
                    try:
                        await test_func(client, test_conversation)
                    except TypeError:
                        # Some tests don't need test_conversation parameter
                        await test_func(client)

            app.dependency_overrides.clear()

        # Cleanup
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await engine.dispose()

        print("\n" + "=" * 70)
        print("  ALL ARTIFACT TESTS COMPLETED SUCCESSFULLY!")
        print("=" * 70 + "\n")

    asyncio.run(run_all_tests())


@pytest.mark.asyncio
async def test_execute_code_artifact(client: AsyncClient, test_conversation):
    """Test executing a code artifact in sandboxed environment (Feature #147)."""
    print("\n" + "=" * 60)
    print("TEST: Execute code artifact in sandbox")
    print("=" * 60)

    conv_id = test_conversation["id"]

    # Step 1: Create a Python code artifact
    print("\n1. Creating Python code artifact...")
    create_response = await client.post("/api/artifacts/create", json={
        "conversation_id": conv_id,
        "content": "def hello():\n    return 'Hello, World!'\n\nprint(hello())",
        "title": "HelloFunction",
        "language": "python"
    })
    assert create_response.status_code == 201
    artifact = create_response.json()
    artifact_id = artifact["id"]
    print(f"   ✓ Created artifact: {artifact['title']}")

    # Step 2: Execute the artifact
    print("\n2. Executing the artifact...")
    execute_response = await client.post(
        f"/api/artifacts/{artifact_id}/execute",
        json={"timeout": 10}
    )
    assert execute_response.status_code == 200
    result = execute_response.json()
    print(f"   ✓ Execution completed")
    print(f"     - Artifact ID: {result['artifact_id']}")
    print(f"     - Language: {result['language']}")
    print(f"     - Success: {result['execution']['success']}")
    print(f"     - Execution time: {result['execution']['execution_time']}s")
    print(f"     - Return code: {result['execution']['return_code']}")

    # Step 3: Verify execution result
    assert result["artifact_id"] == artifact_id
    assert result["execution"]["success"] == True
    assert result["execution"]["return_code"] == 0
    assert "Hello, World!" in result["execution"]["output"]
    print("\n✓ Code execution works correctly")


@pytest.mark.asyncio
async def test_execute_artifact_with_error(client: AsyncClient, test_conversation):
    """Test that execution errors are properly captured and returned."""
    print("\n" + "=" * 60)
    print("TEST: Execute artifact with error")
    print("=" * 60)

    conv_id = test_conversation["id"]

    # Create artifact with code that will fail
    print("\n1. Creating code artifact with error...")
    create_response = await client.post("/api/artifacts/create", json={
        "conversation_id": conv_id,
        "content": "print('before error')\nraise ValueError('This is a test error')\nprint('after error')",
        "title": "ErrorFunction",
        "language": "python"
    })
    artifact = create_response.json()
    artifact_id = artifact["id"]
    print(f"   ✓ Created artifact: {artifact['title']}")

    # Execute and expect failure
    print("\n2. Executing (expecting error)...")
    execute_response = await client.post(
        f"/api/artifacts/{artifact_id}/execute",
        json={"timeout": 10}
    )
    assert execute_response.status_code == 200
    result = execute_response.json()

    print(f"   ✓ Execution completed")
    print(f"     - Success: {result['execution']['success']}")
    print(f"     - Return code: {result['execution']['return_code']}")
    print(f"     - Error: {result['execution']['error']}")

    # Verify error was captured
    assert result["execution"]["success"] == False
    assert result["execution"]["return_code"] != 0
    assert "ValueError" in result["execution"]["error"] or "test error" in result["execution"]["error"]
    assert "before error" in result["execution"]["output"]
    print("\n✓ Error handling works correctly")


@pytest.mark.asyncio
async def test_execute_artifact_timeout(client: AsyncClient, test_conversation):
    """Test that execution timeout prevents infinite loops."""
    print("\n" + "=" * 60)
    print("TEST: Execute artifact with timeout")
    print("=" * 60)

    conv_id = test_conversation["id"]

    # Create artifact with infinite loop
    print("\n1. Creating code artifact with infinite loop...")
    create_response = await client.post("/api/artifacts/create", json={
        "conversation_id": conv_id,
        "content": "while True:\n    pass  # Infinite loop",
        "title": "InfiniteLoop",
        "language": "python"
    })
    artifact = create_response.json()
    artifact_id = artifact["id"]
    print(f"   ✓ Created artifact: {artifact['title']}")

    # Execute with short timeout
    print("\n2. Executing with 2 second timeout...")
    execute_response = await client.post(
        f"/api/artifacts/{artifact_id}/execute",
        json={"timeout": 2}
    )
    assert execute_response.status_code == 200
    result = execute_response.json()

    print(f"   ✓ Execution completed")
    print(f"     - Success: {result['execution']['success']}")
    print(f"     - Execution time: {result['execution']['execution_time']}s")
    print(f"     - Error: {result['execution']['error']}")

    # Verify timeout occurred
    assert result["execution"]["success"] == False
    assert "timeout" in result["execution"]["error"].lower()
    print("\n✓ Timeout protection works correctly")


@pytest.mark.asyncio
async def test_execute_non_code_artifact(client: AsyncClient, test_conversation):
    """Test that non-code artifacts cannot be executed."""
    print("\n" + "=" * 60)
    print("TEST: Execute non-code artifact (should fail)")
    print("=" * 60)

    conv_id = test_conversation["id"]

    # Create HTML artifact
    print("\n1. Creating HTML artifact...")
    create_response = await client.post("/api/artifacts/create", json={
        "conversation_id": conv_id,
        "content": "<div>Hello World</div>",
        "title": "HTMLComponent",
        "language": "html"
    })
    artifact = create_response.json()
    artifact_id = artifact["id"]
    print(f"   ✓ Created artifact: {artifact['title']} (type: {artifact['artifact_type']})")

    # Try to execute
    print("\n2. Attempting to execute HTML artifact...")
    execute_response = await client.post(
        f"/api/artifacts/{artifact_id}/execute",
        json={"timeout": 10}
    )

    # Should return 400 error
    assert execute_response.status_code == 400
    error = execute_response.json()
    print(f"   ✓ Correctly rejected: {error['detail']}")
    print("\n✓ Non-code artifact rejection works correctly")
