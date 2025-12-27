"""Simple test for comments on shared conversations."""

import asyncio
import httpx

BASE_URL = "http://localhost:8000"

async def test_comments_feature():
    """Test the comments feature with minimal setup."""

    async with httpx.AsyncClient(timeout=30.0) as client:
        print("=" * 60)
        print("Testing Feature: Comments on Shared Conversations")
        print("=" * 60)

        # Step 1: Create a conversation
        print("\n📝 Step 1: Creating test conversation...")
        response = await client.post(f"{BASE_URL}/api/conversations", json={
            "title": "Test Comments",
            "model": "claude-sonnet-4-5-20250929"
        })
        assert response.status_code in [200, 201]
        conversation = response.json()
        conversation_id = conversation["id"]
        print(f"✓ Created conversation: {conversation_id}")

        # Step 2: Share the conversation with comments enabled
        print("\n🔗 Step 2: Sharing conversation with comments enabled...")
        response = await client.post(
            f"{BASE_URL}/api/conversations/{conversation_id}/share",
            json={
                "access_level": "read",
                "allow_comments": True,
                "expires_in_days": 7
            }
        )
        assert response.status_code in [200, 201]
        shared = response.json()
        share_token = shared["share_token"]
        print(f"✓ Created share link: {share_token}")
        print(f"  Allow comments: {shared['allow_comments']}")

        # Step 3: Get the conversation to find a message ID
        print("\n🌐 Step 3: Loading shared conversation...")
        response = await client.get(f"{BASE_URL}/api/conversations/share/{share_token}")
        assert response.status_code == 200
        shared_data = response.json()
        print(f"✓ Loaded shared conversation")
        print(f"  Title: {shared_data['title']}")
        print(f"  Messages: {len(shared_data.get('messages', []))}")

        # If there are no messages, we'll create a test message in the DB
        if not shared_data.get('messages') or len(shared_data['messages']) == 0:
            print("\n⚠️  No messages found. Creating test message in database...")
            # For testing purposes, we'll insert a message directly
            from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
            from sqlalchemy.orm import sessionmaker
            from src.models import Message
            from src.core.config import settings
            import uuid

            engine = create_async_engine(settings.database_url)
            async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

            async with async_session() as session:
                message = Message(
                    id=str(uuid.uuid4()),
                    conversation_id=conversation_id,
                    role="user",
                    content="This is a test message for comments"
                )
                session.add(message)
                await session.commit()

                # Update conversation
                from src.models import Conversation
                from sqlalchemy import select
                result = await session.execute(
                    select(Conversation).where(Conversation.id == conversation_id)
                )
                conv = result.scalar_one_or_none()
                if conv:
                    conv.message_count = 1
                    conv.last_message_at = message.created_at
                    await session.commit()

                message_id = message.id
                print(f"✓ Created message: {message_id}")
        else:
            message_id = shared_data['messages'][0]['id']
            print(f"✓ Using existing message: {message_id}")

        # Step 4: Add a comment
        print("\n💭 Step 4: Adding comment to message...")
        response = await client.post(
            f"{BASE_URL}/api/comments/shared/{share_token}/comments",
            json={
                "message_id": message_id,
                "content": "This is a test comment!",
                "anonymous_name": "Test User"
            }
        )
        if response.status_code != 201:
            print(f"✗ Failed to create comment: {response.status_code}")
            print(f"  Response: {response.text}")
            return
        comment = response.json()
        comment_id = comment["id"]
        print(f"✓ Created comment: {comment_id}")
        print(f"  Content: {comment['content']}")

        # Step 5: List comments
        print("\n📋 Step 5: Listing comments...")
        response = await client.get(
            f"{BASE_URL}/api/comments/shared/{share_token}/comments"
        )
        assert response.status_code == 200
        comments = response.json()
        print(f"✓ Retrieved {len(comments)} comment(s)")

        # Step 6: Add a reply
        print("\n↩️ Step 6: Adding reply...")
        response = await client.post(
            f"{BASE_URL}/api/comments/shared/{share_token}/comments",
            json={
                "message_id": message_id,
                "content": "This is a reply",
                "parent_comment_id": comment_id,
                "anonymous_name": "Reply User"
            }
        )
        assert response.status_code == 201
        reply = response.json()
        print(f"✓ Created reply: {reply['id']}")

        # Step 7: Verify thread structure
        print("\n🧵 Step 7: Verifying thread structure...")
        response = await client.get(
            f"{BASE_URL}/api/comments/shared/{share_token}/comments?message_id={message_id}"
        )
        assert response.status_code == 200
        thread = response.json()
        assert len(thread) == 1
        assert len(thread[0]['replies']) == 1
        print(f"✓ Thread structure correct")
        print(f"  Top-level: {len(thread)}")
        print(f"  Replies: {len(thread[0]['replies'])}")

        # Step 8: Update comment
        print("\n✏️ Step 8: Updating comment...")
        response = await client.put(
            f"{BASE_URL}/api/comments/shared/{share_token}/comments/{comment_id}",
            json={"content": "This is the edited comment!"}
        )
        assert response.status_code == 200
        print(f"✓ Updated comment")

        # Step 9: Delete reply
        print("\n🗑️ Step 9: Deleting reply...")
        response = await client.delete(
            f"{BASE_URL}/api/comments/shared/{share_token}/comments/{reply['id']}"
        )
        assert response.status_code == 204
        print(f"✓ Deleted reply")

        # Step 10: Test comments disabled
        print("\n🚫 Step 10: Testing comments disabled...")
        response = await client.post(
            f"{BASE_URL}/api/conversations/{conversation_id}/share",
            json={
                "access_level": "read",
                "allow_comments": False,
                "expires_in_days": 7
            }
        )
        assert response.status_code in [200, 201]
        no_comments = response.json()
        no_comments_token = no_comments['share_token']

        response = await client.post(
            f"{BASE_URL}/api/comments/shared/{no_comments_token}/comments",
            json={"message_id": message_id, "content": "Should fail"}
        )
        assert response.status_code == 403
        print(f"✓ Comments blocked when disabled")

        # Cleanup
        print("\n🧹 Cleaning up...")
        await client.delete(f"{BASE_URL}/api/conversations/{conversation_id}")
        print("✓ Test conversation deleted")

        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_comments_feature())
