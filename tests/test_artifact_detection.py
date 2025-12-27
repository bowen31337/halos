#!/usr/bin/env python3
"""Test artifact detection feature (Feature #39).

This test verifies that:
1. Code blocks are detected from AI responses
2. Language detection works correctly
3. Titles are extracted from code
4. Artifacts can be created and listed
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from src.core.database import Base, get_db
from src.main import app
from src.api.routes.artifacts import extract_code_blocks, detect_language, extract_title_from_code


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


class TestArtifactDetection:
    """Test artifact detection from content."""

    def test_extract_code_blocks_python(self):
        """Test extracting Python code blocks."""
        content = """
Here's some Python code:

```python
def hello_world():
    print("Hello, World!")
    return True
```

That's the code.
"""
        artifacts = extract_code_blocks(content)
        assert len(artifacts) == 1
        # Language hint "python" gets normalized to "py" via LANGUAGE_ALIASES
        assert artifacts[0]["language"] == "py"
        assert "def hello_world" in artifacts[0]["content"]
        assert artifacts[0]["title"] == "hello_world"

    def test_extract_code_blocks_react(self):
        """Test extracting React/JSX code blocks."""
        content = """
Here's a React component:

```jsx
import React from 'react';

const Button = ({ children, onClick }) => {
  return (
    <button onClick={onClick} className="btn">
      {children}
    </button>
  );
};

export default Button;
```
"""
        artifacts = extract_code_blocks(content)
        assert len(artifacts) == 1
        # React detection happens via code pattern matching, not hint
        assert artifacts[0]["language"] == "React/JSX"
        assert "import React" in artifacts[0]["content"]
        assert artifacts[0]["title"] == "Button"

    def test_extract_code_blocks_multiple(self):
        """Test extracting multiple code blocks."""
        content = """
First code:

```javascript
const x = 1;
```

Second code:

```python
y = 2
```
"""
        artifacts = extract_code_blocks(content)
        assert len(artifacts) == 2
        assert artifacts[0]["language"] == "js"  # javascript -> js
        assert artifacts[1]["language"] == "py"  # python -> py

    def test_extract_code_blocks_no_blocks(self):
        """Test with no code blocks."""
        content = "This is just regular text with no code."
        artifacts = extract_code_blocks(content)
        assert len(artifacts) == 0

    def test_extract_code_blocks_empty(self):
        """Test with empty code blocks."""
        content = "```python\n```"
        artifacts = extract_code_blocks(content)
        assert len(artifacts) == 0

    def test_detect_language_python(self):
        """Test Python language detection."""
        code = "def hello():\n    return True"
        assert detect_language(code) == "python"

    def test_detect_language_javascript(self):
        """Test JavaScript language detection."""
        code = "const x = () => { return true; }"
        assert detect_language(code) == "javascript"

    def test_detect_language_react(self):
        """Test React/JSX detection."""
        code = "import React from 'react';\nconst Button = () => <button>Click</button>;"
        # React detection happens via code pattern, not hint
        assert detect_language(code) == "React/JSX"

    def test_detect_language_with_hint(self):
        """Test language detection with hint."""
        code = "some code"
        # Hints get normalized via LANGUAGE_ALIASES
        assert detect_language(code, "python") == "py"
        assert detect_language(code, "javascript") == "js"

    def test_extract_title_function(self):
        """Test title extraction from function."""
        code = "function myFunction() { return true; }"
        assert extract_title_from_code(code, "javascript") == "myFunction"

    def test_extract_title_class(self):
        """Test title extraction from class."""
        code = "class MyClass { constructor() {} }"
        assert extract_title_from_code(code, "javascript") == "MyClass"

    def test_extract_title_python(self):
        """Test title extraction from Python function."""
        code = "def my_function():\n    pass"
        assert extract_title_from_code(code, "python") == "my_function"

    def test_extract_title_react_component(self):
        """Test title extraction from React component."""
        code = "const MyComponent = () => { return <div />; }"
        title = extract_title_from_code(code, "React/JSX")
        assert title == "MyComponent"  # Should be capitalized

    def test_extract_title_fallback(self):
        """Test title extraction fallback."""
        code = "some random code without clear structure"
        title = extract_title_from_code(code, "code")
        # Fallback returns first line if short
        assert title == "some random code without clear structure"


class TestArtifactDetectionAPI:
    """Test artifact detection API endpoints."""

    @pytest.mark.asyncio
    async def test_detect_artifacts_endpoint(self, client: AsyncClient):
        """Test the /api/artifacts/detect endpoint."""
        content = """
Here's some code:

```python
def hello():
    print("Hello")
```
"""
        response = await client.post("/api/artifacts/detect", json={"content": content})
        assert response.status_code == 200
        artifacts = response.json()
        assert len(artifacts) == 1
        assert artifacts[0]["language"] == "py"
        assert artifacts[0]["title"] == "hello"

    @pytest.mark.asyncio
    async def test_create_artifact_endpoint(self, client: AsyncClient):
        """Test the /api/artifacts/create endpoint."""
        # First create a conversation
        conv_response = await client.post("/api/conversations", json={"title": "Test"})
        conversation_id = conv_response.json()["id"]

        data = {
            "content": "def test(): pass",
            "title": "TestFunction",
            "language": "python",
            "conversation_id": conversation_id
        }
        response = await client.post("/api/artifacts/create", json=data)
        assert response.status_code == 200
        artifact = response.json()
        assert artifact["id"] is not None
        assert artifact["title"] == "TestFunction"
        assert artifact["language"] == "python"
        assert artifact["version"] == 1

    @pytest.mark.asyncio
    async def test_list_artifacts_endpoint(self, client: AsyncClient):
        """Test listing artifacts for a conversation."""
        # Create a conversation first
        conv_response = await client.post("/api/conversations", json={"title": "Test"})
        conversation_id = conv_response.json()["id"]

        # Create an artifact
        await client.post("/api/artifacts/create", json={
            "content": "code",
            "title": "Test",
            "language": "python",
            "conversation_id": conversation_id
        })

        # List artifacts
        response = await client.get(f"/api/artifacts/conversations/{conversation_id}/artifacts")
        assert response.status_code == 200
        artifacts = response.json()
        assert len(artifacts) == 1

    @pytest.mark.asyncio
    async def test_full_workflow(self, client: AsyncClient):
        """Test the complete artifact detection workflow."""
        print("\n" + "=" * 60)
        print("TEST: Full artifact detection workflow")
        print("=" * 60)

        # Step 1: Create a conversation
        print("\n1. Creating conversation...")
        conv_response = await client.post("/api/conversations", json={"title": "React Test"})
        assert conv_response.status_code == 201
        conversation = conv_response.json()
        conversation_id = conversation["id"]
        print(f"   ✓ Created conversation: {conversation['title']}")

        # Step 2: Simulate AI response with code
        ai_response = """
Here's a React button component:

```jsx
import React from 'react';

const PrimaryButton = ({ children, onClick }) => {
  return (
    <button
      onClick={onClick}
      className="bg-blue-500 text-white px-4 py-2 rounded"
    >
      {children}
    </button>
  );
};

export default PrimaryButton;
```

This component can be used anywhere in your app!
"""
        print("\n2. Detecting artifacts from AI response...")
        detect_response = await client.post("/api/artifacts/detect", json={
            "content": ai_response,
            "conversation_id": conversation_id
        })
        assert detect_response.status_code == 200
        detected = detect_response.json()
        print(f"   ✓ Detected {len(detected)} artifact(s)")
        for art in detected:
            print(f"     - {art['title']} ({art['language']})")

        # Step 3: Create the artifact
        print("\n3. Creating artifact from detection...")
        artifact_data = {
            "content": detected[0]["content"],
            "title": detected[0]["title"],
            "language": detected[0]["language"],
            "conversation_id": conversation_id
        }
        create_response = await client.post("/api/artifacts/create", json=artifact_data)
        assert create_response.status_code == 200
        artifact = create_response.json()
        print(f"   ✓ Created artifact: {artifact['title']} (ID: {artifact['id']})")

        # Step 4: List artifacts for conversation
        print("\n4. Listing conversation artifacts...")
        list_response = await client.get(f"/api/artifacts/conversations/{conversation_id}/artifacts")
        assert list_response.status_code == 200
        artifacts = list_response.json()
        assert len(artifacts) == 1
        print(f"   ✓ Found {len(artifacts)} artifact(s) in conversation")

        # Step 5: Verify artifact details
        print("\n5. Verifying artifact details...")
        assert artifacts[0]["title"] == "PrimaryButton"
        assert artifacts[0]["language"] == "React/JSX"
        assert "import React" in artifacts[0]["content"]
        print("   ✓ All details verified")

        print("\n" + "=" * 60)
        print("✓ FULL WORKFLOW TEST PASSED")
        print("=" * 60)


if __name__ == "__main__":
    import asyncio

    async def run_all_tests():
        """Run all tests sequentially."""
        print("\n" + "=" * 70)
        print("  FEATURE #39: Artifact Detection & Rendering")
        print("=" * 70)

        # Setup
        from httpx import ASGITransport

        engine = create_async_engine(TEST_DATABASE_URL, echo=False)
        async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        async with async_session() as session:
            # Override get_db
            async def override_get_db():
                yield session

            app.dependency_overrides[get_db] = override_get_db

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                # Run detection tests
                test_detection = TestArtifactDetection()
                print("\n--- Detection Logic Tests ---")
                test_detection.test_extract_code_blocks_python()
                print("✓ Python code block extraction")
                test_detection.test_extract_code_blocks_react()
                print("✓ React/JSX code block extraction")
                test_detection.test_extract_code_blocks_multiple()
                print("✓ Multiple code blocks")
                test_detection.test_detect_language_python()
                print("✓ Python language detection")
                test_detection.test_detect_language_react()
                print("✓ React language detection")
                test_detection.test_extract_title_react_component()
                print("✓ React component title extraction")

                # Run API tests
                test_api = TestArtifactDetectionAPI()
                print("\n--- API Tests ---")
                await test_api.test_detect_artifacts_endpoint(client)
                print("✓ Detect artifacts endpoint")
                await test_api.test_create_artifact_endpoint(client)
                print("✓ Create artifact endpoint")
                await test_api.test_list_artifacts_endpoint(client)
                print("✓ List artifacts endpoint")
                await test_api.test_full_workflow(client)

            app.dependency_overrides.clear()

        # Cleanup
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await engine.dispose()

        print("\n" + "=" * 70)
        print("  ALL TESTS COMPLETED SUCCESSFULLY!")
        print("=" * 70 + "\n")

    asyncio.run(run_all_tests())
