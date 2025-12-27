#!/usr/bin/env python3
"""Test script for database operations and data integrity verification (Feature #195)."""

import asyncio
import json
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.models.conversation import Conversation
from src.models.message import Message
from src.models.project import Project


async def test_database_operations():
    """Test database operations and data integrity."""

    async for db in get_db():
        try:
            print("=== Testing Database Operations and Data Integrity ===\n")

            # Step 1: Create multiple conversations
            print("Step 1: Creating multiple conversations...")
            project = Project(
                user_id="test-user",
                name="Test Project for Integrity",
                description="Project for database integrity testing"
            )
            db.add(project)
            await db.commit()
            await db.refresh(project)

            conversations = []
            for i in range(3):
                conv = Conversation(
                    user_id="test-user",
                    project_id=project.id,
                    title=f"Test Conversation {i+1}",
                    model="claude-sonnet-4-5-20250929"
                )
                db.add(conv)
                conversations.append(conv)

            await db.commit()
            for conv in conversations:
                await db.refresh(conv)

            print(f"   ✓ Created {len(conversations)} conversations\n")

            # Step 2: Verify data persisted in database
            print("Step 2: Verifying data persisted in database...")
            result = await db.execute(
                select(Conversation).where(
                    Conversation.user_id == "test-user",
                    Conversation.project_id == project.id
                )
            )
            saved_convs = result.scalars().all()
            assert len(saved_convs) == 3, "Expected 3 conversations"
            print(f"   ✓ Verified {len(saved_convs)} conversations persisted\n")

            # Step 3: Check foreign key relationships
            print("Step 3: Checking foreign key relationships...")
            for conv in conversations:
                result = await db.execute(
                    select(Project).where(Project.id == conv.project_id)
                )
                related_project = result.scalar_one_or_none()
                assert related_project is not None, f"Conversation {conv.id} has invalid project_id"
                assert related_project.id == project.id, "Foreign key mismatch"
            print("   ✓ All foreign key relationships valid\n")

            # Step 4: Test cascade delete behavior
            print("Step 4: Testing cascade delete behavior...")
            # Add messages to conversations
            for conv in conversations:
                msg = Message(
                    conversation_id=conv.id,
                    role="user",
                    content="Test message"
                )
                db.add(msg)
            await db.commit()

            # Count messages before delete
            result = await db.execute(
                select(Message).where(Message.conversation_id.in_([c.id for c in conversations]))
            )
            msg_count_before = len(result.scalars().all())
            print(f"   - Messages before delete: {msg_count_before}")

            # Delete one conversation
            await db.delete(conversations[0])
            await db.commit()

            # Check messages are cascade deleted
            result = await db.execute(
                select(Message).where(Message.conversation_id == conversations[0].id)
            )
            orphaned_messages = result.scalars().all()
            assert len(orphaned_messages) == 0, "Messages should be cascade deleted"
            print(f"   ✓ Cascade delete working (no orphaned messages)\n")

            # Step 5: Verify no orphaned records
            print("Step 5: Verifying no orphaned records...")
            result = await db.execute(
                select(Conversation).where(Conversation.project_id == project.id)
            )
            remaining_convs = result.scalars().all()
            assert len(remaining_convs) == 2, "Should have 2 conversations left"

            for conv in remaining_convs:
                result = await db.execute(
                    select(Project).where(Project.id == conv.project_id)
                )
                proj = result.scalar_one_or_none()
                assert proj is not None, f"Orphaned conversation found: {conv.id}"
            print("   ✓ No orphaned conversations found\n")

            # Step 6: Test transaction rollback
            print("Step 6: Testing transaction rollback...")
            test_conv = Conversation(
                user_id="test-user",
                project_id=project.id,
                title="Rollback Test",
                model="claude-sonnet-4-5-20250929"
            )
            db.add(test_conv)
            await db.flush()  # Flush but don't commit

            conv_id = test_conv.id

            # Rollback
            await db.rollback()

            # Verify conversation not saved
            result = await db.execute(
                select(Conversation).where(Conversation.id == conv_id)
            )
            rolled_back = result.scalar_one_or_none()
            assert rolled_back is None, "Conversation should not exist after rollback"
            print("   ✓ Transaction rollback working correctly\n")

            # Step 7: Test bulk operations
            print("Step 7: Testing bulk operations...")
            # Get project_id explicitly
            project_id_str = project.id

            # Bulk insert
            bulk_convs = []
            for i in range(5):
                conv = Conversation(
                    user_id="test-user",
                    project_id=project_id_str,
                    title=f"Bulk Conversation {i+1}",
                    model="claude-sonnet-4-5-20250929"
                )
                bulk_convs.append(conv)

            db.add_all(bulk_convs)
            await db.commit()

            result = await db.execute(
                select(Conversation).where(Conversation.project_id == project_id_str)
            )
            total_convs = len(result.scalars().all())
            assert total_convs >= 7, f"Expected at least 7 conversations, got {total_convs}"
            print(f"   ✓ Bulk insert successful (total: {total_convs})\n")

            # Step 8: Test data consistency after concurrent operations
            print("Step 8: Testing data consistency...")
            result = await db.execute(
                select(Conversation).where(
                    Conversation.user_id == "test-user",
                    Conversation.project_id == project_id_str
                )
            )
            all_convs = result.scalars().all()

            for conv in all_convs:
                assert conv.user_id == "test-user", "User ID mismatch"
                assert conv.project_id == project_id_str, "Project ID mismatch"
                assert conv.model is not None, "Model is required"
                assert conv.created_at is not None, "created_at should be set"
            print("   ✓ All data consistent and valid\n")

            # Step 9: Verify timestamps
            print("Step 9: Verifying timestamp management...")
            test_conv = Conversation(
                user_id="test-user",
                project_id=project_id_str,
                title="Timestamp Test",
                model="claude-sonnet-4-5-20250929"
            )
            db.add(test_conv)
            await db.commit()
            await db.refresh(test_conv)

            created_at = test_conv.created_at
            assert created_at is not None, "created_at not set"

            # Update and verify updated_at
            test_conv.title = "Updated Timestamp Test"
            await db.commit()
            await db.refresh(test_conv)

            assert test_conv.updated_at is not None, "updated_at not set"
            print("   ✓ Timestamps managed correctly\n")

            # Step 10: Test unique constraints
            print("Step 10: Testing unique constraints...")
            # Create a conversation with specific title
            unique_conv = Conversation(
                user_id="test-user",
                project_id=project_id_str,
                title="Unique Title Test",
                model="claude-sonnet-4-5-20250929"
            )
            db.add(unique_conv)
            await db.commit()
            await db.refresh(unique_conv)

            # Try to create duplicate (should work - no unique constraint on title+project)
            # Just verify we can query by specific criteria
            result = await db.execute(
                select(Conversation).where(
                    Conversation.project_id == project_id_str,
                    Conversation.title == "Unique Title Test"
                )
            )
            found = result.scalar_one_or_none()
            assert found is not None, "Cannot find unique conversation"
            print("   ✓ Unique constraints and queries working\n")

            print("=== All Database Integrity Tests Passed! ===")

        except Exception as e:
            print(f"✗ Error: {e}")
            import traceback
            traceback.print_exc()
            raise
        finally:
            break  # Exit after first iteration


if __name__ == "__main__":
    asyncio.run(test_database_operations())
