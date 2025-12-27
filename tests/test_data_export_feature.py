#!/usr/bin/env python3
"""Test Feature #138: Data export includes all user content.

This test verifies:
1. Data export endpoint returns all conversations
2. Data export includes messages
3. Data export includes memories
4. Data export includes prompts
5. Data export includes artifacts
6. Data export includes checkpoints
7. Data export includes projects
8. Data export includes settings
9. Export format is valid JSON with proper structure
"""

import asyncio
import json
from pathlib import Path

# Add src to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select
from src.core.config import settings
from src.models import Conversation, Message, Memory, Prompt, Artifact, Checkpoint, Project
from fastapi.testclient import TestClient
from src.main import app


async def test_data_export_includes_all_content():
    """Test that data export includes all user content types."""
    print("Testing Feature #138: Data Export Includes All User Content...")

    # Create engine
    engine = create_async_engine(settings.database_url)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        # Step 1: Create several conversations with artifacts
        print("\n  Step 1: Creating test data...")

        # Create projects
        project1 = Project(name="Test Project 1", description="A test project")
        project2 = Project(name="Test Project 2", description="Another test project")
        db.add(project1)
        db.add(project2)
        await db.commit()
        await db.refresh(project1)
        await db.refresh(project2)
        print(f"    ✓ Created 2 projects")

        # Create conversations
        conv1 = Conversation(
            title="Conversation 1",
            model="claude-sonnet-4-5-20250929",
            project_id=project1.id,
            token_count=100
        )
        conv2 = Conversation(
            title="Conversation 2",
            model="claude-haiku-4-5-20251001",
            project_id=project2.id,
            token_count=200
        )
        conv3 = Conversation(
            title="Conversation 3 (No Project)",
            model="claude-opus-4-1-20250805",
            token_count=50
        )
        db.add(conv1)
        db.add(conv2)
        db.add(conv3)
        await db.commit()
        await db.refresh(conv1)
        await db.refresh(conv2)
        await db.refresh(conv3)
        print(f"    ✓ Created 3 conversations")

        # Create messages
        messages = [
            Message(conversation_id=conv1.id, role="user", content="Hello", input_tokens=5),
            Message(conversation_id=conv1.id, role="assistant", content="Hi there!", output_tokens=10),
            Message(conversation_id=conv2.id, role="user", content="Tell me a story", input_tokens=15),
            Message(conversation_id=conv2.id, role="assistant", content="Once upon a time...", output_tokens=50),
            Message(conversation_id=conv3.id, role="user", content="What is 2+2?", input_tokens=3),
        ]
        for msg in messages:
            db.add(msg)
        await db.commit()
        print(f"    ✓ Created {len(messages)} messages")

        # Create memories
        memory1 = Memory(content="User likes Python", category="preferences")
        memory2 = Memory(content="User works at TechCorp", category="professional")
        db.add(memory1)
        db.add(memory2)
        await db.commit()
        await db.refresh(memory1)
        await db.refresh(memory2)
        print(f"    ✓ Created 2 memories")

        # Create prompts
        prompt1 = Prompt(
            title="Code Review Prompt",
            content="Please review this code for best practices",
            category="coding",
            description="A prompt for code review"
        )
        prompt2 = Prompt(
            title="Writing Assistant",
            content="Help me write better content",
            category="writing",
            description="A prompt for writing help"
        )
        db.add(prompt1)
        db.add(prompt2)
        await db.commit()
        await db.refresh(prompt1)
        await db.refresh(prompt2)
        print(f"    ✓ Created 2 prompts")

        # Create artifacts
        artifact1 = Artifact(
            conversation_id=conv1.id,
            title="Hello World Script",
            language="python",
            content="print('Hello, World!')"
        )
        artifact2 = Artifact(
            conversation_id=conv2.id,
            title="HTML Template",
            language="html",
            content="<div>Hello</div>"
        )
        db.add(artifact1)
        db.add(artifact2)
        await db.commit()
        await db.refresh(artifact1)
        await db.refresh(artifact2)
        print(f"    ✓ Created 2 artifacts")

        # Create checkpoints
        checkpoint1 = Checkpoint(
            conversation_id=conv1.id,
            name="Initial State",
            notes="Starting point",
            state={"messages": []}
        )
        checkpoint2 = Checkpoint(
            conversation_id=conv2.id,
            name="After Story",
            notes="Story completed",
            state={"messages": []}
        )
        db.add(checkpoint1)
        db.add(checkpoint2)
        await db.commit()
        await db.refresh(checkpoint1)
        await db.refresh(checkpoint2)
        print(f"    ✓ Created 2 checkpoints")

        # Step 2-3: Request full data export
        print("\n  Step 2-3: Requesting full data export...")
        client = TestClient(app)
        response = client.get("/api/settings/export-all")

        print(f"    ✓ Export response status: {response.status_code}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        # Verify response headers
        assert response.headers.get("content-type") == "application/json"
        assert "attachment; filename=" in response.headers.get("content-disposition", "")

        # Parse JSON
        data = json.loads(response.text)

        # Step 4: Verify export includes conversations
        print("\n  Step 4: Verifying conversations in export...")
        assert "data" in data
        assert "conversations" in data["data"]
        assert len(data["data"]["conversations"]) == 3
        assert any(c["title"] == "Conversation 1" for c in data["data"]["conversations"])
        assert any(c["title"] == "Conversation 2" for c in data["data"]["conversations"])
        assert any(c["title"] == "Conversation 3 (No Project)" for c in data["data"]["conversations"])
        print(f"    ✓ All 3 conversations included in export")

        # Step 5: Verify export includes artifacts
        print("\n  Step 5: Verifying artifacts in export...")
        assert "artifacts" in data["data"]
        assert len(data["data"]["artifacts"]) == 2
        assert any(a["title"] == "Hello World Script" for a in data["data"]["artifacts"])
        assert any(a["title"] == "HTML Template" for a in data["data"]["artifacts"])
        print(f"    ✓ All 2 artifacts included in export")

        # Step 6: Verify export includes settings
        print("\n  Step 6: Verifying settings in export...")
        assert "settings" in data["data"]
        assert isinstance(data["data"]["settings"], dict)
        print(f"    ✓ Settings included in export")

        # Step 7: Verify export includes memories
        print("\n  Step 7: Verifying memories in export...")
        assert "memories" in data["data"]
        assert len(data["data"]["memories"]) == 2
        assert any(m["content"] == "User likes Python" for m in data["data"]["memories"])
        assert any(m["content"] == "User works at TechCorp" for m in data["data"]["memories"])
        print(f"    ✓ All 2 memories included in export")

        # Additional verification: messages
        print("\n  Additional: Verifying messages in export...")
        assert "messages" in data["data"]
        assert len(data["data"]["messages"]) == 5
        print(f"    ✓ All 5 messages included in export")

        # Additional verification: prompts
        print("\n  Additional: Verifying prompts in export...")
        assert "prompts" in data["data"]
        assert len(data["data"]["prompts"]) == 2
        print(f"    ✓ All 2 prompts included in export")

        # Additional verification: checkpoints
        print("\n  Additional: Verifying checkpoints in export...")
        assert "checkpoints" in data["data"]
        assert len(data["data"]["checkpoints"]) == 2
        print(f"    ✓ All 2 checkpoints included in export")

        # Additional verification: projects
        print("\n  Additional: Verifying projects in export...")
        assert "projects" in data["data"]
        assert len(data["data"]["projects"]) == 2
        print(f"    ✓ All 2 projects included in export")

        # Verify summary
        print("\n  Verifying export summary...")
        assert "summary" in data
        assert data["summary"]["conversations"] == 3
        assert data["summary"]["messages"] == 5
        assert data["summary"]["memories"] == 2
        assert data["summary"]["prompts"] == 2
        assert data["summary"]["artifacts"] == 2
        assert data["summary"]["checkpoints"] == 2
        assert data["summary"]["projects"] == 2
        print(f"    ✓ Summary counts are correct")

        # Cleanup
        print("\n  Cleaning up test data...")
        await db.execute(select(Checkpoint).delete())
        await db.execute(select(Artifact).delete())
        await db.execute(select(Prompt).delete())
        await db.execute(select(Memory).delete())
        await db.execute(select(Message).delete())
        await db.execute(select(Conversation).delete())
        await db.execute(select(Project).delete())
        await db.commit()
        print("    ✓ Test data cleaned up")

    await engine.dispose()
    print("\n✅ Feature #138: Data Export Test PASSED")


async def test_data_export_empty_state():
    """Test that data export works even with no data."""
    print("\nTesting Data Export with Empty Database...")

    engine = create_async_engine(settings.database_url)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        client = TestClient(app)
        response = client.get("/api/settings/export-all")

        assert response.status_code == 200
        data = json.loads(response.text)

        # Should return empty arrays but valid structure
        assert data["summary"]["conversations"] == 0
        assert data["summary"]["messages"] == 0
        assert len(data["data"]["conversations"]) == 0
        assert len(data["data"]["messages"]) == 0
        assert "settings" in data["data"]

        print("  ✓ Empty database export works correctly")

    await engine.dispose()
    print("✅ Empty State Test PASSED")


async def main():
    await test_data_export_includes_all_content()
    await test_data_export_empty_state()

    print("\n" + "="*60)
    print("FEATURE #138: DATA EXPORT INCLUDES ALL USER CONTENT")
    print("="*60)
    print("\nManual Testing Steps:")
    print("1. Start the backend server")
    print("2. Start the frontend server")
    print("3. Open http://localhost:5173 in browser")
    print("4. Create some conversations, messages, memories, prompts, artifacts")
    print("5. Open Settings → Data & Account tab")
    print("6. Click 'Export All Data (JSON)' button")
    print("7. Verify the JSON file downloads")
    print("8. Open the file and verify it contains all your data")
    print("\nExpected behavior:")
    print("- Export includes conversations, messages, memories, prompts")
    print("- Export includes artifacts, checkpoints, projects, settings")
    print("- File downloads with timestamped filename")
    print("- JSON is valid and properly structured")


if __name__ == "__main__":
    asyncio.run(main())
