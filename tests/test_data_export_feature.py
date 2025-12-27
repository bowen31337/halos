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
        # Step 1: Create test data
        print("\n  Step 1: Creating test data...")

        # Get initial counts
        initial_conv_count = len((await db.execute(select(Conversation).where(Conversation.is_deleted == False))).scalars().all())
        initial_msg_count = len((await db.execute(select(Message))).scalars().all())
        initial_memory_count = len((await db.execute(select(Memory).where(Memory.is_active == True))).scalars().all())
        initial_prompt_count = len((await db.execute(select(Prompt).where(Prompt.is_active == True))).scalars().all())
        initial_artifact_count = len((await db.execute(select(Artifact))).scalars().all())
        initial_checkpoint_count = len((await db.execute(select(Checkpoint))).scalars().all())
        initial_project_count = len((await db.execute(select(Project))).scalars().all())

        # Create projects
        project1 = Project(name="Feature138_TestProject1", description="Test for data export")
        project2 = Project(name="Feature138_TestProject2", description="Another test")
        db.add(project1)
        db.add(project2)
        await db.commit()
        await db.refresh(project1)
        await db.refresh(project2)

        # Create conversations
        conv1 = Conversation(
            title="Feature138_TestConv1",
            model="claude-sonnet-4-5-20250929",
            project_id=project1.id,
            token_count=100
        )
        conv2 = Conversation(
            title="Feature138_TestConv2",
            model="claude-haiku-4-5-20251001",
            project_id=project2.id,
            token_count=200
        )
        db.add(conv1)
        db.add(conv2)
        await db.commit()
        await db.refresh(conv1)
        await db.refresh(conv2)

        # Create messages
        messages = [
            Message(conversation_id=conv1.id, role="user", content="Feature138 Hello", input_tokens=5),
            Message(conversation_id=conv1.id, role="assistant", content="Feature138 Hi", output_tokens=10),
            Message(conversation_id=conv2.id, role="user", content="Feature138 Test", input_tokens=15),
        ]
        for msg in messages:
            db.add(msg)
        await db.commit()

        # Create memories
        memory1 = Memory(content="Feature138 Memory 1", category="test")
        memory2 = Memory(content="Feature138 Memory 2", category="test")
        db.add(memory1)
        db.add(memory2)
        await db.commit()

        # Create prompts
        prompt1 = Prompt(title="Feature138 Prompt 1", content="Test content", category="test")
        prompt2 = Prompt(title="Feature138 Prompt 2", content="Test content 2", category="test")
        db.add(prompt1)
        db.add(prompt2)
        await db.commit()

        # Create artifacts
        artifact1 = Artifact(conversation_id=conv1.id, title="Feature138 Artifact 1", language="python", content="print('test')")
        artifact2 = Artifact(conversation_id=conv2.id, title="Feature138 Artifact 2", language="js", content="console.log('test')")
        db.add(artifact1)
        db.add(artifact2)
        await db.commit()

        # Create checkpoints
        checkpoint1 = Checkpoint(conversation_id=conv1.id, name="Feature138 CP1", state_snapshot={"test": True})
        checkpoint2 = Checkpoint(conversation_id=conv2.id, name="Feature138 CP2", state_snapshot={"test": True})
        db.add(checkpoint1)
        db.add(checkpoint2)
        await db.commit()

        # Get new counts
        new_conv_count = len((await db.execute(select(Conversation).where(Conversation.is_deleted == False))).scalars().all())
        new_msg_count = len((await db.execute(select(Message))).scalars().all())
        new_memory_count = len((await db.execute(select(Memory).where(Memory.is_active == True))).scalars().all())
        new_prompt_count = len((await db.execute(select(Prompt).where(Prompt.is_active == True))).scalars().all())
        new_artifact_count = len((await db.execute(select(Artifact))).scalars().all())
        new_checkpoint_count = len((await db.execute(select(Checkpoint))).scalars().all())
        new_project_count = len((await db.execute(select(Project))).scalars().all())

        print(f"    ✓ Created 2 projects (total: {new_project_count})")
        print(f"    ✓ Created 2 conversations (total: {new_conv_count})")
        print(f"    ✓ Created 3 messages (total: {new_msg_count})")
        print(f"    ✓ Created 2 memories (total: {new_memory_count})")
        print(f"    ✓ Created 2 prompts (total: {new_prompt_count})")
        print(f"    ✓ Created 2 artifacts (total: {new_artifact_count})")
        print(f"    ✓ Created 2 checkpoints (total: {new_checkpoint_count})")

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
        assert len(data["data"]["conversations"]) >= 2  # At least our 2 new ones
        # Check for our specific test conversations
        conv_titles = [c["title"] for c in data["data"]["conversations"]]
        assert "Feature138_TestConv1" in conv_titles
        assert "Feature138_TestConv2" in conv_titles
        print(f"    ✓ Test conversations included in export")

        # Step 5: Verify export includes artifacts
        print("\n  Step 5: Verifying artifacts in export...")
        assert "artifacts" in data["data"]
        artifact_titles = [a["title"] for a in data["data"]["artifacts"]]
        assert "Feature138 Artifact 1" in artifact_titles
        assert "Feature138 Artifact 2" in artifact_titles
        print(f"    ✓ Test artifacts included in export")

        # Step 6: Verify export includes settings
        print("\n  Step 6: Verifying settings in export...")
        assert "settings" in data["data"]
        assert isinstance(data["data"]["settings"], dict)
        print(f"    ✓ Settings included in export")

        # Step 7: Verify export includes memories
        print("\n  Step 7: Verifying memories in export...")
        assert "memories" in data["data"]
        memory_contents = [m["content"] for m in data["data"]["memories"]]
        assert "Feature138 Memory 1" in memory_contents
        assert "Feature138 Memory 2" in memory_contents
        print(f"    ✓ Test memories included in export")

        # Additional verification: messages
        print("\n  Additional: Verifying messages in export...")
        assert "messages" in data["data"]
        message_contents = [m["content"] for m in data["data"]["messages"]]
        assert "Feature138 Hello" in message_contents
        assert "Feature138 Hi" in message_contents
        assert "Feature138 Test" in message_contents
        print(f"    ✓ Test messages included in export")

        # Additional verification: prompts
        print("\n  Additional: Verifying prompts in export...")
        assert "prompts" in data["data"]
        prompt_titles = [p["title"] for p in data["data"]["prompts"]]
        assert "Feature138 Prompt 1" in prompt_titles
        assert "Feature138 Prompt 2" in prompt_titles
        print(f"    ✓ Test prompts included in export")

        # Additional verification: checkpoints
        print("\n  Additional: Verifying checkpoints in export...")
        assert "checkpoints" in data["data"]
        checkpoint_names = [c["name"] for c in data["data"]["checkpoints"]]
        assert "Feature138 CP1" in checkpoint_names
        assert "Feature138 CP2" in checkpoint_names
        print(f"    ✓ Test checkpoints included in export")

        # Additional verification: projects
        print("\n  Additional: Verifying projects in export...")
        assert "projects" in data["data"]
        project_names = [p["name"] for p in data["data"]["projects"]]
        assert "Feature138_TestProject1" in project_names
        assert "Feature138_TestProject2" in project_names
        print(f"    ✓ Test projects included in export")

        # Verify summary reflects our additions
        print("\n  Verifying export summary...")
        assert "summary" in data
        # The summary should include all data, not just our test data
        assert data["summary"]["conversations"] >= 2
        assert data["summary"]["messages"] >= 3
        assert data["summary"]["memories"] >= 2
        assert data["summary"]["prompts"] >= 2
        assert data["summary"]["artifacts"] >= 2
        assert data["summary"]["checkpoints"] >= 2
        assert data["summary"]["projects"] >= 2
        print(f"    ✓ Summary includes all data types")

        # Cleanup
        print("\n  Cleaning up test data...")
        # Delete by specific IDs to avoid affecting other tests
        await db.delete(checkpoint1)
        await db.delete(checkpoint2)
        await db.delete(artifact1)
        await db.delete(artifact2)
        await db.delete(prompt1)
        await db.delete(prompt2)
        await db.delete(memory1)
        await db.delete(memory2)
        for msg in messages:
            await db.delete(msg)
        await db.delete(conv1)
        await db.delete(conv2)
        await db.delete(project1)
        await db.delete(project2)
        await db.commit()
        print("    ✓ Test data cleaned up")

    await engine.dispose()
    print("\n✅ Feature #138: Data Export Test PASSED")


async def test_data_export_structure():
    """Test that data export has correct structure."""
    print("\nTesting Data Export Structure...")

    engine = create_async_engine(settings.database_url)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        client = TestClient(app)
        response = client.get("/api/settings/export-all")

        assert response.status_code == 200
        data = json.loads(response.text)

        # Verify structure
        assert "export_version" in data
        assert "export_date" in data
        assert "export_type" in data
        assert "summary" in data
        assert "data" in data

        # Verify data structure
        assert "conversations" in data["data"]
        assert "messages" in data["data"]
        assert "memories" in data["data"]
        assert "prompts" in data["data"]
        assert "artifacts" in data["data"]
        assert "checkpoints" in data["data"]
        assert "projects" in data["data"]
        assert "settings" in data["data"]

        print("  ✓ Export structure is correct")

    await engine.dispose()
    print("✅ Structure Test PASSED")


async def main():
    await test_data_export_includes_all_content()
    await test_data_export_structure()

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
