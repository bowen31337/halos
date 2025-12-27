"""Debug script to test share viewing logic."""

import sys
import asyncio
sys.path.insert(0, '.')

from sqlalchemy import select
from src.core.database import async_session_factory
from src.models import SharedConversation, Conversation, Message

async def debug_view():
    async with async_session_factory() as db:
        # Get the most recent share
        result = await db.execute(
            select(SharedConversation)
            .order_by(SharedConversation.created_at.desc())
            .limit(1)
        )
        share = result.scalar_one_or_none()

        if not share:
            print("No shares found")
            return

        print(f"✅ Found share:")
        print(f"   ID: {share.id}")
        print(f"   Token: {share.share_token[:30]}...")
        print(f"   Conversation ID: {share.conversation_id}")
        print(f"   Access: {share.access_level}")
        print(f"   Public: {share.is_public}")
        print(f"   Expires: {share.expires_at}")

        # Get conversation
        result = await db.execute(
            select(Conversation).where(Conversation.id == share.conversation_id)
        )
        conv = result.scalar_one_or_none()

        if conv:
            print(f"\n✅ Found conversation:")
            print(f"   Title: {conv.title}")
            print(f"   Model: {conv.model}")

            # Get messages
            result = await db.execute(
                select(Message)
                .where(Message.conversation_id == share.conversation_id)
                .order_by(Message.created_at)
            )
            messages = result.scalars().all()
            print(f"\n✅ Found {len(messages)} messages")

            # Try to build the response like the API does
            messages_data = [
                {
                    "id": msg.id,
                    "role": msg.role,
                    "content": msg.content[:50] + "..." if msg.content and len(msg.content) > 50 else msg.content,
                    "created_at": msg.created_at.isoformat(),
                    "attachments": msg.attachments,
                    "thinking_content": msg.thinking_content,
                }
                for msg in messages
            ]

            print(f"\n✅ Built response data:")
            print(f"   Messages in response: {len(messages_data)}")
        else:
            print(f"\n❌ Conversation not found")

asyncio.run(debug_view())
