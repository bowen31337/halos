"""Test conversation branching functionality end-to-end."""

import asyncio
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select
from src.main import app
from src.core.database import get_db, AsyncSessionLocal
from src.models.conversation import Conversation
from src.models.message import Message


class TestConversationBranching:
    """Test suite for conversation branching feature."""

    @pytest.fixture
    async def client(self):
        """Create async test client."""
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as ac:
            yield ac

    @pytest.fixture
    async def db_session(self):
        """Create database session."""
        async with AsyncSessionLocal() as session:
            yield session
            await session.rollback()

    @pytest.fixture
    async def test_conversation(self, db_session: AsyncSessionLocal):
        """Create a test conversation with messages."""
        # Create conversation
        conversation = Conversation(
            user_id="test-user",
            title="Branching Test Conversation",
            model="claude-sonnet-4-5-20250929"
        )
        db_session.add(conversation)
        await db_session.commit()
        await db_session.refresh(conversation)

        # Add messages
        messages = [
            Message(
                conversation_id=conversation.id,
                role="user",
                content="What is Python?",
                input_tokens=10,
                output_tokens=0
            ),
            Message(
                conversation_id=conversation.id,
                role="assistant",
                content="Python is a programming language.",
                input_tokens=10,
                output_tokens=50
            ),
            Message(
                conversation_id=conversation.id,
                role="user",
                content="Tell me more about Python features.",
                input_tokens=15,
                output_tokens=0
            ),
            Message(
                conversation_id=conversation.id,
                role="assistant",
                content="Python has many features including dynamic typing, automatic memory management, and a large standard library.",
                input_tokens=15,
                output_tokens=80
            ),
            Message(
                conversation_id=conversation.id,
                role="user",
                content="What about Python frameworks?",
                input_tokens=12,
                output_tokens=0
            ),
        ]

        for msg in messages:
            db_session.add(msg)

        await db_session.commit()

        # Get message IDs for branching
        result = await db_session.execute(
            select(Message).where(Message.conversation_id == conversation.id)
        )
        messages_list = result.scalars().all()

        return {
            "conversation": conversation,
            "messages": messages_list
        }

    @pytest.mark.asyncio
    async def test_create_branch_from_message(self, client: AsyncClient, test_conversation):
        """Test creating a branch from a specific message."""
        conversation = test_conversation["conversation"]
        messages = test_conversation["messages"]

        # Branch from the second user message (index 2)
        branch_point_message = messages[2]  # "Tell me more about Python features."

        response = await client.post(
            f"/api/conversations/{conversation.id}/branch",
            params={
                "branch_point_message_id": branch_point_message.id,
                "branch_name": "Alternative Discussion",
                "branch_color": "#ff6b6b"
            }
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "message" in data
        assert "conversation" in data
        assert data["message"] == "Conversation branch created successfully"

        # Verify branch conversation data
        branch_conversation = data["conversation"]
        assert "id" in branch_conversation
        assert branch_conversation["parent_conversation_id"] == conversation.id
        assert branch_conversation["branch_point_message_id"] == branch_point_message.id
        assert branch_conversation["branch_name"] == "Alternative Discussion"
        assert branch_conversation["branch_color"] == "#ff6b6b"
        assert "Alternative Discussion" in branch_conversation["title"]

        print(f"✓ Created branch: {branch_conversation['id']}")
        print(f"  Parent: {branch_conversation['parent_conversation_id']}")
        print(f"  Branch point: {branch_conversation['branch_point_message_id']}")

    @pytest.mark.asyncio
    async def test_branch_copies_messages_up_to_branch_point(self, client: AsyncClient, test_conversation, db_session: AsyncSessionLocal):
        """Test that branch conversation contains messages up to branch point."""
        conversation = test_conversation["conversation"]
        messages = test_conversation["messages"]

        # Branch from the third message (index 2, "Tell me more...")
        branch_point_message = messages[2]

        response = await client.post(
            f"/api/conversations/{conversation.id}/branch",
            params={"branch_point_message_id": branch_point_message.id}
        )

        assert response.status_code == 200
        branch_conversation_id = response.json()["conversation"]["id"]

        # Verify messages were copied
        result = await db_session.execute(
            select(Message).where(Message.conversation_id == branch_conversation_id)
        )
        branch_messages = result.scalars().all()

        # Should have 3 messages (up to and including branch point)
        assert len(branch_messages) == 3

        # Verify message contents
        contents = [msg.content for msg in branch_messages]
        assert "What is Python?" in contents
        assert "Python is a programming language." in contents
        assert "Tell me more about Python features." in contents

        print(f"✓ Branch contains {len(branch_messages)} messages (up to branch point)")
        for msg in branch_messages:
            print(f"  - [{msg.role}] {msg.content[:50]}...")

    @pytest.mark.asyncio
    async def test_list_branches_for_conversation(self, client: AsyncClient, test_conversation, db_session: AsyncSessionLocal):
        """Test listing all branches for a conversation."""
        conversation = test_conversation["conversation"]
        messages = test_conversation["messages"]

        # Create multiple branches
        branch_ids = []
        for i, msg in enumerate([messages[1], messages[3]]):
            response = await client.post(
                f"/api/conversations/{conversation.id}/branch",
                params={
                    "branch_point_message_id": msg.id,
                    "branch_name": f"Branch {i+1}",
                    "branch_color": f"#color{i}"
                }
            )
            assert response.status_code == 200
            branch_ids.append(response.json()["conversation"]["id"])

        # List branches
        response = await client.get(f"/api/conversations/{conversation.id}/branches")

        assert response.status_code == 200
        data = response.json()

        assert "branches" in data
        assert data["count"] == 2
        assert len(data["branches"]) == 2

        print(f"✓ Listed {data['count']} branches:")
        for branch in data["branches"]:
            print(f"  - {branch['title']} ({branch['branch_name']})")

    @pytest.mark.asyncio
    async def test_get_branch_history(self, client: AsyncClient, test_conversation):
        """Test getting complete branch history."""
        conversation = test_conversation["conversation"]
        messages = test_conversation["messages"]

        # Create a branch
        response = await client.post(
            f"/api/conversations/{conversation.id}/branch",
            params={"branch_point_message_id": messages[2].id}
        )
        assert response.status_code == 200
        branch_id = response.json()["conversation"]["id"]

        # Create a branch from the branch
        response2 = await client.post(
            f"/api/conversations/{branch_id}/branch",
            params={"branch_point_message_id": messages[0].id}
        )
        assert response.status_code == 200
        branch2_id = response2.json()["conversation"]["id"]

        # Get branch history for the second-level branch
        response = await client.get(f"/api/conversations/{branch2_id}/branch-history")

        assert response.status_code == 200
        data = response.json()

        assert "branch_history" in data
        assert data["current_branch_depth"] == 3  # root -> branch -> branch2
        assert len(data["branch_history"]) == 3

        print(f"✓ Branch history depth: {data['current_branch_depth']}")
        for i, node in enumerate(data["branch_history"]):
            print(f"  {i+1}. {node['title']} (branch: {node['branch_name']})")

    @pytest.mark.asyncio
    async def test_get_branch_path(self, client: AsyncClient, test_conversation):
        """Test getting branch path from root to current."""
        conversation = test_conversation["conversation"]
        messages = test_conversation["messages"]

        # Create a branch
        response = await client.post(
            f"/api/conversations/{conversation.id}/branch",
            params={
                "branch_point_message_id": messages[1].id,
                "branch_name": "Feature Exploration",
                "branch_color": "#4ecdc4"
            }
        )
        assert response.status_code == 200
        branch_id = response.json()["conversation"]["id"]

        # Get branch path
        response = await client.get(f"/api/conversations/{branch_id}/branch-path")

        assert response.status_code == 200
        data = response.json()

        assert "branch_path" in data
        assert data["is_branch"] == True
        assert len(data["branch_path"]) == 2
        assert data["root_conversation_id"] == conversation.id

        # Verify path structure
        path = data["branch_path"]
        assert path[0]["id"] == conversation.id  # Root
        assert path[1]["id"] == branch_id  # Branch
        assert path[1]["branch_color"] == "#4ecdc4"

        print(f"✓ Branch path (is_branch={data['is_branch']}):")
        for i, node in enumerate(path):
            print(f"  {i+1}. {node['title']}")

    @pytest.mark.asyncio
    async def test_branch_with_custom_name_and_color(self, client: AsyncClient, test_conversation):
        """Test creating a branch with custom name and color."""
        conversation = test_conversation["conversation"]
        messages = test_conversation["messages"]

        custom_name = "Bug Fix Investigation"
        custom_color = "#9b59b6"

        response = await client.post(
            f"/api/conversations/{conversation.id}/branch",
            params={
                "branch_point_message_id": messages[0].id,
                "branch_name": custom_name,
                "branch_color": custom_color
            }
        )

        assert response.status_code == 200
        data = response.json()

        branch = data["conversation"]
        assert branch["branch_name"] == custom_name
        assert branch["branch_color"] == custom_color
        assert custom_name in branch["title"]

        print(f"✓ Custom branch created:")
        print(f"  Name: {branch['branch_name']}")
        print(f"  Color: {branch['branch_color']}")

    @pytest.mark.asyncio
    async def test_branch_from_nonexistent_message_fails(self, client: AsyncClient, test_conversation):
        """Test that branching from non-existent message returns 404."""
        conversation = test_conversation["conversation"]

        response = await client.post(
            f"/api/conversations/{conversation.id}/branch",
            params={"branch_point_message_id": "nonexistent-message-id"}
        )

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

        print(f"✓ Correctly returned 404 for nonexistent message")

    @pytest.mark.asyncio
    async def test_branch_from_nonexistent_conversation_fails(self, client: AsyncClient):
        """Test that branching from non-existent conversation returns 404."""
        response = await client.post(
            "/api/conversations/nonexistent-conversation/branch",
            params={"branch_point_message_id": "some-message-id"}
        )

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

        print(f"✓ Correctly returned 404 for nonexistent conversation")

    @pytest.mark.asyncio
    async def test_branch_inherits_parent_settings(self, client: AsyncClient, test_conversation):
        """Test that branch inherits model and settings from parent."""
        conversation = test_conversation["conversation"]
        messages = test_conversation["messages"]

        # Update parent with specific settings
        conversation.model = "claude-opus-4-1-20250805"
        conversation.extended_thinking_enabled = True

        response = await client.post(
            f"/api/conversations/{conversation.id}/branch",
            params={"branch_point_message_id": messages[1].id}
        )

        assert response.status_code == 200
        branch_id = response.json()["conversation"]["id"]

        # Verify branch inherited settings
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Conversation).where(Conversation.id == branch_id)
            )
            branch = result.scalar_one_or_none()

            assert branch is not None
            assert branch.model == "claude-opus-4-1-20250805"
            assert branch.extended_thinking_enabled == True
            assert branch.project_id == conversation.project_id

        print(f"✓ Branch inherited settings:")
        print(f"  Model: {conversation.model}")
        print(f"  Extended thinking: {conversation.extended_thinking_enabled}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
