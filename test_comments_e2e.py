"""End-to-end test for comments on shared conversations."""

import asyncio
import httpx
from datetime import datetime, timedelta
import uuid

BASE_URL = "http://localhost:8000"

async def test_comments_feature():
    """Test the complete comments feature workflow."""

    async with httpx.AsyncClient(timeout=30.0) as client:
        print("=" * 60)
        print("Testing Feature: Comments on Shared Conversations")
        print("=" * 60)

        # Step 1: Create a test conversation with messages
        print("\n📝 Step 1: Creating test conversation...")
        response = await client.post(f"{BASE_URL}/api/conversations", json={
            "title": "Test Conversation for Comments",
            "model": "claude-sonnet-4-5-20250929"
        })
        assert response.status_code in [200, 201]
        conversation = response.json()
        conversation_id = conversation["id"]
        print(f"✓ Created conversation: {conversation_id}")

        # Step 2: Add a message to the conversation
        print("\n💬 Step 2: Adding message to conversation...")
        response = await client.post(
            f"{BASE_URL}/api/conversations/{conversation_id}/messages",
            json={
                "role": "user",
                "content": "This is a test message for comments"
            }
        )
        assert response.status_code in [200, 201]
        message = response.json()
        message_id = message["id"]
        print(f"✓ Created message: {message_id}")

        # Step 3: Share the conversation with comments enabled
        print("\n🔗 Step 3: Sharing conversation with comments enabled...")
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
        print(f"  Comments allowed: {shared['allow_comments']}")

        # Step 4: Verify shared conversation loads via public link
        print("\n🌐 Step 4: Verifying shared conversation loads...")
        response = await client.get(f"{BASE_URL}/api/conversations/share/{share_token}")
        assert response.status_code == 200
        shared_data = response.json()
        print(f"✓ Shared conversation loaded")
        print(f"  Title: {shared_data['title']}")
        print(f"  Allow comments: {shared_data['allow_comments']}")
        print(f"  Messages: {len(shared_data['messages'])}")

        # Step 5: Add a comment to the message
        print("\n💭 Step 5: Adding comment to message...")
        response = await client.post(
            f"{BASE_URL}/api/comments/shared/{share_token}/comments",
            json={
                "message_id": message_id,
                "content": "This is a test comment!",
                "anonymous_name": "Test User"
            }
        )
        assert response.status_code == 201
        comment = response.json()
        comment_id = comment["id"]
        print(f"✓ Created comment: {comment_id}")
        print(f"  Content: {comment['content']}")
        print(f"  Author: {comment['anonymous_name']}")

        # Step 6: List comments for the shared conversation
        print("\n📋 Step 6: Listing all comments...")
        response = await client.get(
            f"{BASE_URL}/api/comments/shared/{share_token}/comments"
        )
        assert response.status_code == 200
        comments = response.json()
        print(f"✓ Retrieved {len(comments)} top-level comment(s)")
        for c in comments:
            print(f"  - {c['content'][:50]}... (by {c.get('anonymous_name', 'Anonymous')})")

        # Step 7: Filter comments by message
        print("\n🔍 Step 7: Filtering comments by message...")
        response = await client.get(
            f"{BASE_URL}/api/comments/shared/{share_token}/comments?message_id={message_id}"
        )
        assert response.status_code == 200
        message_comments = response.json()
        print(f"✓ Found {len(message_comments)} comment(s) for message")
        assert len(message_comments) == 1

        # Step 8: Add a reply to the comment
        print("\n↩️ Step 8: Adding reply to comment...")
        response = await client.post(
            f"{BASE_URL}/api/comments/shared/{share_token}/comments",
            json={
                "message_id": message_id,
                "content": "This is a reply to the comment",
                "parent_comment_id": comment_id,
                "anonymous_name": "Reply User"
            }
        )
        assert response.status_code == 201
        reply = response.json()
        reply_id = reply["id"]
        print(f"✓ Created reply: {reply_id}")
        print(f"  Parent: {reply['parent_comment_id']}")

        # Step 9: Verify comment thread with replies
        print("\n🧵 Step 9: Verifying comment thread structure...")
        response = await client.get(
            f"{BASE_URL}/api/comments/shared/{share_token}/comments?message_id={message_id}"
        )
        assert response.status_code == 200
        thread = response.json()
        assert len(thread) == 1
        assert len(thread[0]['replies']) == 1
        print(f"✓ Comment thread structure correct")
        print(f"  Top-level: {len(thread)}")
        print(f"  Replies: {len(thread[0]['replies'])}")

        # Step 10: Update a comment
        print("\n✏️ Step 10: Updating comment...")
        response = await client.put(
            f"{BASE_URL}/api/comments/shared/{share_token}/comments/{comment_id}",
            json={"content": "This is the edited comment!"}
        )
        assert response.status_code == 200
        updated = response.json()
        print(f"✓ Updated comment")
        print(f"  New content: {updated['content']}")
        print(f"  Updated at: {updated['updated_at']}")
        assert "edited" in updated['content'].lower() or updated['updated_at'] is not None

        # Step 11: Delete the reply
        print("\n🗑️ Step 11: Deleting reply...")
        response = await client.delete(
            f"{BASE_URL}/api/comments/shared/{share_token}/comments/{reply_id}"
        )
        assert response.status_code == 204
        print(f"✓ Deleted reply")

        # Step 12: Verify reply is soft-deleted
        print("\n✅ Step 12: Verifying soft delete...")
        response = await client.get(
            f"{BASE_URL}/api/comments/shared/{share_token}/comments?message_id={message_id}"
        )
        assert response.status_code == 200
        thread = response.json()
        print(f"✓ Reply removed from thread")
        print(f"  Remaining replies: {len(thread[0]['replies'])}")
        assert len(thread[0]['replies']) == 0

        # Step 13: Test that comments are disabled when not allowed
        print("\n🚫 Step 13: Testing comments disabled...")
        response = await client.post(
            f"{BASE_URL}/api/conversations/{conversation_id}/share",
            json={
                "access_level": "read",
                "allow_comments": False,
                "expires_in_days": 7
            }
        )
        assert response.status_code in [200, 201]
        no_comments_share = response.json()
        no_comments_token = no_comments_share['share_token']

        response = await client.post(
            f"{BASE_URL}/api/comments/shared/{no_comments_token}/comments",
            json={
                "message_id": message_id,
                "content": "This should fail"
            }
        )
        assert response.status_code == 403
        print(f"✓ Comments correctly blocked when disabled")

        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)
        print("\n📊 Summary:")
        print("  ✓ Comments can be created on shared conversations")
        print("  ✓ Comments can be listed and filtered")
        print("  ✓ Nested replies work correctly")
        print("  ✓ Comments can be edited")
        print("  ✓ Comments can be soft-deleted")
        print("  ✓ Permission checks work (allow_comments flag)")

        # Cleanup
        print("\n🧹 Cleaning up...")
        await client.delete(f"{BASE_URL}/api/conversations/{conversation_id}")
        print("✓ Test conversation deleted")

if __name__ == "__main__":
    asyncio.run(test_comments_feature())
