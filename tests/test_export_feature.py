#!/usr/bin/env python3
"""Test Feature #21: Export conversation as JSON or Markdown format.

This test verifies:
1. Backend export endpoint returns JSON with conversation metadata and messages
2. Backend export endpoint returns Markdown formatted conversation
3. Export includes all message fields (content, role, tool_calls, etc.)
4. Export handles conversations with multiple messages correctly
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
from src.models import Conversation, Message
from fastapi.testclient import TestClient
from src.main import app


async def test_export_json_format():
    """Test the backend export API returns valid JSON."""
    print("Testing Backend Export JSON Format...")

    # Create engine
    engine = create_async_engine(settings.database_url)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # Create a test conversation with messages
    async with async_session() as db:
        # Create conversation
        conv = Conversation(
            title="Test Export Conversation",
            model="claude-sonnet-4-5-20250929"
        )
        db.add(conv)
        await db.commit()
        await db.refresh(conv)

        # Add messages
        messages = [
            Message(
                conversation_id=conv.id,
                role="user",
                content="Hello, can you help me with Python?",
                input_tokens=10,
            ),
            Message(
                conversation_id=conv.id,
                role="assistant",
                content="I'd be happy to help! What specific Python question do you have?",
                output_tokens=20,
            ),
            Message(
                conversation_id=conv.id,
                role="user",
                content="How do I use list comprehensions?",
                input_tokens=15,
            ),
        ]

        for msg in messages:
            db.add(msg)
        await db.commit()

        print(f"✓ Created conversation: {conv.id} with {len(messages)} messages")

        # Test export via API
        client = TestClient(app)
        response = client.post(f"/api/conversations/{conv.id}/export?format=json")

        print(f"✓ Export response status: {response.status_code}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        # Verify response headers
        assert response.headers.get("content-type") == "application/json"
        assert "attachment; filename=" in response.headers.get("content-disposition", "")

        # Parse JSON
        data = json.loads(response.text)

        # Verify structure
        assert "id" in data
        assert "title" in data
        assert "model" in data
        assert "messages" in data
        assert "metadata" in data

        # Verify conversation data
        assert data["id"] == conv.id
        assert data["title"] == "Test Export Conversation"
        assert data["model"] == "claude-sonnet-4-5-20250929"

        # Verify messages
        assert len(data["messages"]) == 3
        assert data["messages"][0]["role"] == "user"
        assert data["messages"][0]["content"] == "Hello, can you help me with Python?"
        assert data["messages"][0]["input_tokens"] == 10
        assert data["messages"][1]["role"] == "assistant"
        assert data["messages"][2]["role"] == "user"

        # Verify metadata (uses actual message count from query, not conversation.message_count)
        print(f"  Metadata: {data['metadata']}")
        print(f"  Messages in data: {len(data['messages'])}")
        assert data["metadata"]["message_count"] == 3, f"Expected 3, got {data['metadata']['message_count']}"

        print(f"✓ JSON export contains all required fields")

        # Cleanup
        for msg in messages:
            await db.delete(msg)
        await db.delete(conv)
        await db.commit()
        print("✓ Cleaned up test data")

    await engine.dispose()
    print("\n✅ Backend export JSON format test PASSED")


async def test_export_markdown_format():
    """Test the backend export API returns valid Markdown."""
    print("\nTesting Backend Export Markdown Format...")

    # Create engine
    engine = create_async_engine(settings.database_url)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # Create a test conversation with messages
    async with async_session() as db:
        # Create conversation
        conv = Conversation(
            title="Markdown Export Test",
            model="claude-sonnet-4-5-20250929"
        )
        db.add(conv)
        await db.commit()
        await db.refresh(conv)

        # Add messages
        messages = [
            Message(
                conversation_id=conv.id,
                role="user",
                content="Show me a Python function.",
            ),
            Message(
                conversation_id=conv.id,
                role="assistant",
                content="Here's a Python function:\n\n```python\ndef hello():\n    print('Hello World')\n```",
                input_tokens=5,
                output_tokens=10,
            ),
        ]

        for msg in messages:
            db.add(msg)
        await db.commit()

        print(f"✓ Created conversation: {conv.id} with {len(messages)} messages")

        # Test export via API
        client = TestClient(app)
        response = client.post(f"/api/conversations/{conv.id}/export?format=markdown")

        print(f"✓ Export response status: {response.status_code}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        # Verify response headers
        assert "text/markdown" in response.headers.get("content-type", "")
        assert "attachment; filename=" in response.headers.get("content-disposition", "")

        # Parse Markdown
        md_content = response.text

        # Verify structure
        assert "# Markdown Export Test" in md_content
        assert "**Model:** claude-sonnet-4-5-20250929" in md_content
        assert "## 👤 User" in md_content
        assert "## 🤖 Assistant" in md_content
        assert "Show me a Python function." in md_content
        assert "```python" in md_content
        assert "**Message Count:** 2" in md_content

        print(f"✓ Markdown export contains all required sections")

        # Cleanup
        for msg in messages:
            await db.delete(msg)
        await db.delete(conv)
        await db.commit()
        print("✓ Cleaned up test data")

    await engine.dispose()
    print("\n✅ Backend export Markdown format test PASSED")


async def test_export_with_tool_calls():
    """Test export handles tool calls and tool results."""
    print("\nTesting Backend Export with Tool Calls...")

    engine = create_async_engine(settings.database_url)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        conv = Conversation(
            title="Tool Test Conversation",
            model="claude-sonnet-4-5-20250929"
        )
        db.add(conv)
        await db.commit()
        await db.refresh(conv)

        # Add message with tool call
        msg_with_tool = Message(
            conversation_id=conv.id,
            role="assistant",
            content="I'll search for that information.",
            tool_calls={"name": "search", "args": {"query": "python docs"}},
        )
        db.add(msg_with_tool)
        await db.commit()

        print(f"✓ Created conversation with tool call")

        # Test JSON export
        client = TestClient(app)
        response = client.post(f"/api/conversations/{conv.id}/export?format=json")
        data = json.loads(response.text)

        # Verify tool calls are included
        assert data["messages"][0]["tool_calls"] is not None
        assert data["messages"][0]["tool_calls"]["name"] == "search"

        print(f"✓ JSON export includes tool calls")

        # Test Markdown export
        response = client.post(f"/api/conversations/{conv.id}/export?format=markdown")
        md_content = response.text

        # Verify tool call section in markdown
        assert "**Tool Call:**" in md_content
        assert "\"name\": \"search\"" in md_content

        print(f"✓ Markdown export includes tool call section")

        # Cleanup
        await db.delete(msg_with_tool)
        await db.delete(conv)
        await db.commit()

    await engine.dispose()
    print("\n✅ Backend export with tool calls test PASSED")


async def main():
    await test_export_json_format()
    await test_export_markdown_format()
    await test_export_with_tool_calls()

    print("\n" + "="*60)
    print("FEATURE #21: EXPORT CONVERSATION")
    print("="*60)
    print("\nManual Testing Steps:")
    print("1. Open http://localhost:5173 in browser")
    print("2. Create a conversation and send a few messages")
    print("3. Hover over the conversation in the sidebar")
    print("4. Click the 📄 (JSON) or 📝 (Markdown) export button")
    print("5. Verify the file downloads")
    print("6. Open the file and verify content")
    print("\nExpected behavior:")
    print("- 📄 button exports as JSON with all message data")
    print("- 📝 button exports as Markdown with formatted conversation")
    print("- Export includes conversation title, model, and all messages")
    print("- Tool calls and thinking content are included")
    print("- Token counts are included")
    print("- File downloads with proper filename")


if __name__ == "__main__":
    asyncio.run(main())
