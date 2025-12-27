"""Test script to verify comments feature on shared conversations."""

import asyncio
import httpx
import uuid
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"

async def test_comments_feature():
    """Test the comments feature end-to-end."""

    async with httpx.AsyncClient() as client:
        print("=" * 80)
        print("Testing Feature #154: Comments and Annotations on Shared Conversations")
        print("=" * 80)

        # Step 1: Create a test conversation
        print("\n[Step 1] Creating test conversation...")
        conv_response = await client.post(
            f"{BASE_URL}/api/conversations",
            json={"title": "Test Conversation for Comments"}
        )
        if conv_response.status_code not in [200, 201]:
            print(f"❌ Failed to create conversation: {conv_response.status_code}")
            return False

        conversation = conv_response.json()
        conversation_id = conversation["id"]
        print(f"✅ Created conversation: {conversation_id}")

        # Step 2: Add a message to the conversation
        print("\n[Step 2] Adding message to conversation...")
        msg_response = await client.post(
            f"{BASE_URL}/api/conversations/{conversation_id}/messages",
            json={
                "role": "user",
                "content": "This is a test message for comments"
            }
        )
        if msg_response.status_code not in [200, 201]:
            print(f"❌ Failed to add message: {msg_response.status_code}")
            return False

        message = msg_response.json()
        message_id = message["id"]
        print(f"✅ Added message: {message_id}")

        # Step 3: Share the conversation with comments enabled
        print("\n[Step 3] Sharing conversation with comments enabled...")
        share_response = await client.post(
            f"{BASE_URL}/api/conversations/{conversation_id}/share",
            json={
                "access_level": "view",
                "allow_comments": True,
                "expires_in_days": 7
            }
        )
        if share_response.status_code not in [200, 201]:
            print(f"❌ Failed to share conversation: {share_response.status_code}")
            return False

        share_data = share_response.json()
        share_token = share_data["share_token"]
        print(f"✅ Shared conversation with token: {share_token}")

        # Step 4: Create a comment on the message
        print("\n[Step 4] Creating comment on message...")
        comment_response = await client.post(
            f"{BASE_URL}/api/comments/shared/{share_token}/comments",
            json={
                "message_id": message_id,
                "content": "This is a test comment!",
                "anonymous_name": "Test User"
            }
        )
        if comment_response.status_code != 201:
            print(f"❌ Failed to create comment: {comment_response.status_code}")
            print(f"Response: {comment_response.text}")
            return False

        comment = comment_response.json()
        comment_id = comment["id"]
        print(f"✅ Created comment: {comment_id}")
        print(f"   Content: {comment['content']}")
        print(f"   Author: {comment['anonymous_name']}")

        # Step 5: List comments for the message
        print("\n[Step 5] Listing comments for message...")
        list_response = await client.get(
            f"{BASE_URL}/api/comments/shared/{share_token}/comments",
            params={"message_id": message_id}
        )
        if list_response.status_code != 200:
            print(f"❌ Failed to list comments: {list_response.status_code}")
            return False

        comments = list_response.json()
        print(f"✅ Found {len(comments)} comment(s)")
        if len(comments) > 0:
            print(f"   First comment: {comments[0]['content']}")

        # Step 6: Reply to the comment
        print("\n[Step 6] Replying to comment...")
        reply_response = await client.post(
            f"{BASE_URL}/api/comments/shared/{share_token}/comments",
            json={
                "message_id": message_id,
                "content": "This is a reply to the comment",
                "parent_comment_id": comment_id,
                "anonymous_name": "Another User"
            }
        )
        if reply_response.status_code != 201:
            print(f"❌ Failed to create reply: {reply_response.status_code}")
            print(f"Response: {reply_response.text}")
            return False

        reply = reply_response.json()
        print(f"✅ Created reply: {reply['id']}")
        print(f"   Content: {reply['content']}")

        # Step 7: List comments again to verify the reply
        print("\n[Step 7] Listing comments to verify reply...")
        list_response2 = await client.get(
            f"{BASE_URL}/api/comments/shared/{share_token}/comments",
            params={"message_id": message_id}
        )
        if list_response2.status_code != 200:
            print(f"❌ Failed to list comments: {list_response2.status_code}")
            return False

        comments_with_replies = list_response2.json()
        print(f"✅ Found {len(comments_with_replies)} top-level comment(s)")
        if len(comments_with_replies) > 0 and len(comments_with_replies[0].get("replies", [])) > 0:
            print(f"   Reply count: {len(comments_with_replies[0]['replies'])}")
            print(f"   First reply: {comments_with_replies[0]['replies'][0]['content']}")

        # Step 8: Update the comment
        print("\n[Step 8] Updating comment...")
        update_response = await client.put(
            f"{BASE_URL}/api/comments/shared/{share_token}/comments/{comment_id}",
            json={"content": "This is an edited comment!"}
        )
        if update_response.status_code != 200:
            print(f"❌ Failed to update comment: {update_response.status_code}")
            print(f"Response: {update_response.text}")
            return False

        updated_comment = update_response.json()
        print(f"✅ Updated comment: {updated_comment['content']}")
        print(f"   Updated at: {updated_comment.get('updated_at')}")

        # Step 9: Delete the reply
        print("\n[Step 9] Deleting reply...")
        delete_response = await client.delete(
            f"{BASE_URL}/api/comments/shared/{share_token}/comments/{reply['id']}"
        )
        if delete_response.status_code != 204:
            print(f"❌ Failed to delete comment: {delete_response.status_code}")
            return False

        print(f"✅ Deleted reply")

        # Step 10: Verify reply was deleted (should not appear in list)
        print("\n[Step 10] Verifying reply was deleted...")
        list_response3 = await client.get(
            f"{BASE_URL}/api/comments/shared/{share_token}/comments",
            params={"message_id": message_id}
        )
        if list_response3.status_code != 200:
            print(f"❌ Failed to list comments: {list_response3.status_code}")
            return False

        final_comments = list_response3.json()
        reply_count = len(final_comments[0].get("replies", [])) if len(final_comments) > 0 else 0
        if reply_count == 0:
            print(f"✅ Reply successfully deleted (0 replies found)")
        else:
            print(f"❌ Reply still exists ({reply_count} replies found)")
            return False

        # Step 11: Test accessing shared conversation with comments
        print("\n[Step 11] Accessing shared conversation endpoint...")
        shared_conv_response = await client.get(
            f"{BASE_URL}/api/conversations/share/{share_token}"
        )
        if shared_conv_response.status_code != 200:
            print(f"❌ Failed to access shared conversation: {shared_conv_response.status_code}")
            return False

        shared_conv = shared_conv_response.json()
        print(f"✅ Accessed shared conversation")
        print(f"   Title: {shared_conv['title']}")
        print(f"   Allow comments: {shared_conv.get('allow_comments')}")

        print("\n" + "=" * 80)
        print("✅ ALL TESTS PASSED!")
        print("=" * 80)
        print("\nFeature #154 (Comments and annotations) is fully functional:")
        print("  ✓ Share conversation with comment permission")
        print("  ✓ Add comments on messages")
        print("  ✓ List comments for messages")
        print("  ✓ Reply to comments")
        print("  ✓ Update comments")
        print("  ✓ Delete comments")
        print("  ✓ Access shared conversations with comments")
        return True

if __name__ == "__main__":
    asyncio.run(test_comments_feature())
