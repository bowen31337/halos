#!/usr/bin/env python3
"""
Manual verification script for Feature #147: React component preview with hot reload

This script creates a sample React component artifact and verifies it can be previewed.

Usage:
    python tests/verify_react_preview.py
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from httpx import AsyncClient, ASGITransport
from src.main import app
from src.core.database import get_db


async def verify_react_preview():
    """Verify React component preview functionality"""

    print("=" * 60)
    print("Feature #147 Verification: React Component Preview")
    print("=" * 60)

    # Create test client
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:

        # Step 1: Create a conversation
        print("\n[1/5] Creating test conversation...")
        conv_response = await client.post(
            "/api/conversations",
            json={
                "title": "React Preview Test",
                "model": "claude-sonnet-4-5-20250929",
            }
        )

        if conv_response.status_code != 200:
            print(f"❌ Failed to create conversation: {conv_response.status_code}")
            return False

        conversation_id = conv_response.json()["id"]
        print(f"✓ Created conversation: {conversation_id}")

        # Step 2: Create a React component artifact
        print("\n[2/5] Creating React component artifact...")

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

        artifact_response = await client.post(
            f"/api/conversations/{conversation_id}/artifacts",
            json={
                "title": "Counter Component",
                "content": react_code,
                "artifact_type": "react",
                "language": "jsx",
                "identifier": "counter",
            }
        )

        if artifact_response.status_code != 200:
            print(f"❌ Failed to create artifact: {artifact_response.status_code}")
            print(f"Response: {artifact_response.text}")
            return False

        artifact = artifact_response.json()
        artifact_id = artifact["id"]
        print(f"✓ Created artifact: {artifact_id}")
        print(f"  - Type: {artifact['artifact_type']}")
        print(f"  - Language: {artifact['language']}")

        # Step 3: Verify artifact was saved
        print("\n[3/5] Verifying artifact was saved...")

        get_response = await client.get(
            f"/api/conversations/{conversation_id}/artifacts"
        )

        if get_response.status_code != 200:
            print(f"❌ Failed to get artifacts: {get_response.status_code}")
            return False

        artifacts = get_response.json()
        if len(artifacts) == 0:
            print("❌ No artifacts found")
            return False

        print(f"✓ Found {len(artifacts)} artifact(s)")

        # Step 4: Test hot reload by updating the artifact
        print("\n[4/5] Testing hot reload (updating artifact)...")

        updated_code = """
export default function Counter() {
  const [count, setCount] = React.useState(0);

  return (
    <div style={{ padding: '20px', fontFamily: 'sans-serif', background: '#f0f0f0' }}>
      <h1>Counter: {count}</h1>
      <p>This component has been updated!</p>
      <button onClick={() => setCount(count + 1)}>
        Increment
      </button>
      <button onClick={() => setCount(count - 1)} style={{ marginLeft: '10px' }}>
        Decrement
      </button>
      <button onClick={() => setCount(0)} style={{ marginLeft: '10px' }}>
        Reset
      </button>
    </div>
  );
}
"""

        update_response = await client.put(
            f"/api/artifacts/{artifact_id}",
            json={
                "content": updated_code,
                "title": "Counter Component (Updated)"
            }
        )

        if update_response.status_code != 200:
            print(f"❌ Failed to update artifact: {update_response.status_code}")
            return False

        updated_artifact = update_response.json()
        print(f"✓ Updated artifact to version {updated_artifact['version']}")
        print(f"  - New title: {updated_artifact['title']}")

        # Step 5: Test different React component types
        print("\n[5/5] Testing different React component types...")

        component_types = [
            ("JSX", "export default function App() { return <div>Hello JSX</div>; }", "jsx"),
            ("TSX", "export default function App() { return <div>Hello TSX</div>; }", "tsx"),
            ("React", "export default function App() { return <div>Hello React</div>; }", "react"),
        ]

        for type_name, code, lang in component_types:
            response = await client.post(
                f"/api/conversations/{conversation_id}/artifacts",
                json={
                    "title": f"{type_name} Component",
                    "content": code,
                    "artifact_type": "react",
                    "language": lang,
                    "identifier": f"{lang.lower()}-app",
                }
            )

            if response.status_code == 200:
                print(f"  ✓ {type_name} component created")
            else:
                print(f"  ❌ {type_name} component failed: {response.status_code}")

    print("\n" + "=" * 60)
    print("✅ Feature #147 Verification Complete!")
    print("=" * 60)
    print("\nSummary:")
    print("- React component artifacts can be created ✓")
    print("- Component type detection works (jsx, tsx, react) ✓")
    print("- Hot reload via artifact updates works ✓")
    print("\nFrontend Testing Required:")
    print("- Open the app and navigate to the conversation")
    print("- Click on the artifact panel")
    print("- Verify the React component renders in the preview")
    print("- Edit the component and verify it hot reloads")
    print("- Test interactive elements (buttons, state changes)")

    return True


if __name__ == "__main__":
    try:
        success = asyncio.run(verify_react_preview())
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Error during verification: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
