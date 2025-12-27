#!/usr/bin/env python3
"""Test Feature #139: Account deletion removes all user data.

This test verifies:
1. Account deletion requires correct confirmation string
2. Account deletion removes all conversations (soft delete)
3. Account deletion removes all messages
4. Account deletion removes all memories
5. Account deletion removes all prompts
6. Account deletion removes all artifacts
7. Account deletion removes all checkpoints
8. Account deletion removes all projects
9. Account deletion logs the action in audit log
10. Returns proper confirmation with counts
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
from src.core.database import Base
from src.models import Conversation, Message, Memory, Prompt, Artifact, Checkpoint, Project, AuditLog
from fastapi.testclient import TestClient
from src.main import app


async def test_account_deletion_removes_all_data():
    """Test that account deletion removes all user data."""
    print("Testing Feature #139: Account Deletion Removes All User Data...")

    # Create engine
    engine = create_async_engine(settings.database_url)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # Create tables if they don't exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as db:
        # Step 1-2: Create test data and open account settings
        print("\n  Step 1-2: Creating test data...")

        # Create projects
        project1 = Project(name="Project to Delete", description="Will be deleted")
        project2 = Project(name="Another Project", description="Also deleted")
        db.add(project1)
        db.add(project2)
        await db.commit()
        await db.refresh(project1)
        await db.refresh(project2)

        # Create conversations
        conv1 = Conversation(title="Conversation 1", model="claude-sonnet", project_id=project1.id)
        conv2 = Conversation(title="Conversation 2", model="claude-haiku", project_id=project2.id)
        conv3 = Conversation(title="Conversation 3", model="claude-opus")
        db.add(conv1)
        db.add(conv2)
        db.add(conv3)
        await db.commit()
        await db.refresh(conv1)
        await db.refresh(conv2)
        await db.refresh(conv3)

        # Create messages
        messages = [
            Message(conversation_id=conv1.id, role="user", content="Hello"),
            Message(conversation_id=conv1.id, role="assistant", content="Hi"),
            Message(conversation_id=conv2.id, role="user", content="Test"),
            Message(conversation_id=conv3.id, role="user", content="Another"),
        ]
        for msg in messages:
            db.add(msg)
        await db.commit()

        # Create memories
        memory1 = Memory(content="Memory 1", category="test")
        memory2 = Memory(content="Memory 2", category="test")
        db.add(memory1)
        db.add(memory2)
        await db.commit()

        # Create prompts
        prompt1 = Prompt(title="Prompt 1", content="Content 1", category="test")
        prompt2 = Prompt(title="Prompt 2", content="Content 2", category="test")
        db.add(prompt1)
        db.add(prompt2)
        await db.commit()

        # Create artifacts
        artifact1 = Artifact(conversation_id=conv1.id, title="Artifact 1", language="python", content="code")
        artifact2 = Artifact(conversation_id=conv2.id, title="Artifact 2", language="js", content="code")
        db.add(artifact1)
        db.add(artifact2)
        await db.commit()

        # Create checkpoints
        checkpoint1 = Checkpoint(conversation_id=conv1.id, name="CP1", state_snapshot={})
        checkpoint2 = Checkpoint(conversation_id=conv2.id, name="CP2", state_snapshot={})
        db.add(checkpoint1)
        db.add(checkpoint2)
        await db.commit()

        # Verify initial state
        initial_conv_count = (await db.execute(select(Conversation).where(Conversation.is_deleted == False))).scalar_count()
        initial_msg_count = (await db.execute(select(Message))).scalar_count()
        initial_memory_count = (await db.execute(select(Memory).where(Memory.is_active == True))).scalar_count()
        initial_prompt_count = (await db.execute(select(Prompt).where(Prompt.is_active == True))).scalar_count()
        initial_artifact_count = (await db.execute(select(Artifact))).scalar_count()
        initial_checkpoint_count = (await db.execute(select(Checkpoint))).scalar_count()
        initial_project_count = (await db.execute(select(Project))).scalar_count()

        print(f"    ✓ Created {initial_conv_count} conversations")
        print(f"    ✓ Created {initial_msg_count} messages")
        print(f"    ✓ Created {initial_memory_count} memories")
        print(f"    ✓ Created {initial_prompt_count} prompts")
        print(f"    ✓ Created {initial_artifact_count} artifacts")
        print(f"    ✓ Created {initial_checkpoint_count} checkpoints")
        print(f"    ✓ Created {initial_project_count} projects")

        # Step 3: Initiate deletion process (without confirmation - should fail)
        print("\n  Step 3: Testing deletion without confirmation...")
        client = TestClient(app)
        response = client.delete("/api/settings/account")

        assert response.status_code == 400
        error_data = response.json()
        assert "DELETE_ACCOUNT" in error_data["detail"]
        print(f"    ✓ Deletion blocked without confirmation")

        # Step 4: Complete confirmation steps
        print("\n  Step 4: Testing deletion with wrong confirmation...")
        response = client.delete("/api/settings/account?confirm=WRONG_STRING")

        assert response.status_code == 400
        print(f"    ✓ Deletion blocked with wrong confirmation")

        # Step 5: Verify account is deleted with correct confirmation
        print("\n  Step 5: Deleting account with correct confirmation...")
        response = client.delete("/api/settings/account?confirm=DELETE_ACCOUNT")

        print(f"    ✓ Deletion response status: {response.status_code}")
        assert response.status_code == 200

        result = response.json()
        assert result["status"] == "success"
        assert "message" in result
        assert "deleted_items" in result
        assert "total_deleted" in result

        # Verify counts match
        assert result["deleted_items"]["conversations"] == initial_conv_count
        assert result["deleted_items"]["messages"] == initial_msg_count
        assert result["deleted_items"]["memories"] == initial_memory_count
        assert result["deleted_items"]["prompts"] == initial_prompt_count
        assert result["deleted_items"]["artifacts"] == initial_artifact_count
        assert result["deleted_items"]["checkpoints"] == initial_checkpoint_count
        assert result["deleted_items"]["projects"] == initial_project_count

        total_calculated = sum(result["deleted_items"].values())
        assert result["total_deleted"] == total_calculated

        print(f"    ✓ Deletion returned correct counts")
        print(f"    ✓ Total deleted: {result['total_deleted']} items")

        # Step 6: Verify data cannot be recovered (soft delete for conversations, hard delete for others)
        print("\n  Step 6: Verifying data is removed...")

        # Conversations should be soft-deleted (is_deleted=True)
        remaining_convs = (await db.execute(
            select(Conversation).where(Conversation.is_deleted == False)
        )).scalar_count()
        assert remaining_convs == 0
        print(f"    ✓ All conversations soft-deleted (is_deleted=True)")

        # Messages should be permanently deleted
        remaining_messages = (await db.execute(select(Message))).scalar_count()
        assert remaining_messages == 0
        print(f"    ✓ All messages permanently deleted")

        # Memories should be permanently deleted
        remaining_memories = (await db.execute(select(Memory))).scalar_count()
        assert remaining_memories == 0
        print(f"    ✓ All memories permanently deleted")

        # Prompts should be permanently deleted
        remaining_prompts = (await db.execute(select(Prompt))).scalar_count()
        assert remaining_prompts == 0
        print(f"    ✓ All prompts permanently deleted")

        # Artifacts should be permanently deleted
        remaining_artifacts = (await db.execute(select(Artifact))).scalar_count()
        assert remaining_artifacts == 0
        print(f"    ✓ All artifacts permanently deleted")

        # Checkpoints should be permanently deleted
        remaining_checkpoints = (await db.execute(select(Checkpoint))).scalar_count()
        assert remaining_checkpoints == 0
        print(f"    ✓ All checkpoints permanently deleted")

        # Projects should be permanently deleted
        remaining_projects = (await db.execute(select(Project))).scalar_count()
        assert remaining_projects == 0
        print(f"    ✓ All projects permanently deleted")

        # Step 7: Verify login is not possible (session management would be handled by auth system)
        # For this test, we verify that the audit log was created
        print("\n  Step 7: Verifying audit log was created...")
        audit_logs = (await db.execute(
            select(AuditLog).where(AuditLog.action == "account_deletion")
        )).scalars().all()

        assert len(audit_logs) > 0
        audit_log = audit_logs[0]
        assert audit_log.user_id == "default-user"
        assert audit_log.action == "account_deletion"
        assert audit_log.resource_type == "user"
        assert audit_log.resource_id == "default-user"
        assert "items_to_delete" in audit_log.details
        print(f"    ✓ Audit log created for account deletion")

        # Cleanup (nothing to clean since everything is deleted)
        print("\n  Cleanup: No data remaining to clean up")

    await engine.dispose()
    print("\n✅ Feature #139: Account Deletion Test PASSED")


async def test_account_deletion_with_no_data():
    """Test that account deletion works even with no data."""
    print("\nTesting Account Deletion with Empty Database...")

    engine = create_async_engine(settings.database_url)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # Create tables if they don't exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as db:
        client = TestClient(app)
        response = client.delete("/api/settings/account?confirm=DELETE_ACCOUNT")

        assert response.status_code == 200
        data = response.json()

        # Should return zero counts
        assert data["status"] == "success"
        assert data["total_deleted"] == 0
        assert all(count == 0 for count in data["deleted_items"].values())

        print("  ✓ Empty database deletion works correctly")

    await engine.dispose()
    print("✅ Empty State Test PASSED")


async def main():
    await test_account_deletion_removes_all_data()
    await test_account_deletion_with_no_data()

    print("\n" + "="*60)
    print("FEATURE #139: ACCOUNT DELETION REMOVES ALL USER DATA")
    print("="*60)
    print("\nManual Testing Steps:")
    print("1. Start the backend server")
    print("2. Start the frontend server")
    print("3. Open http://localhost:5173 in browser")
    print("4. Create some conversations, messages, memories, etc.")
    print("5. Open Settings → Data & Account tab")
    print("6. Scroll to Danger Zone section")
    print("7. Type 'DELETE_ACCOUNT' in the confirmation input")
    print("8. Click 'Delete Account Permanently' button")
    print("9. Confirm the browser confirmation dialog")
    print("10. Verify success message with deletion counts")
    print("\nExpected behavior:")
    print("- Must type exactly 'DELETE_ACCOUNT' to enable button")
    print("- Browser shows confirmation dialog with warning")
    print("- Success message shows all deleted item counts")
    print("- User is redirected to home page")
    print("- All data is permanently removed")


if __name__ == "__main__":
    asyncio.run(main())
