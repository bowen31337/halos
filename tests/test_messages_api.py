"""Test Messages API endpoints."""
import asyncio
from httpx import AsyncClient, ASGITransport
from src.main import app


async def test_messages_api():
    """Test all Messages API endpoints."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as client:
        # Create conversation
        conv = await client.post('/api/conversations', json={'title': 'Test Messages'})
        conv_id = conv.json()['id']
        print(f'✓ Created conversation: {conv_id}')

        # Test 1: Create message
        msg = await client.post(
            f'/api/conversations/{conv_id}/messages',
            json={'role': 'user', 'content': 'Hello from test'}
        )
        assert msg.status_code == 201, f"Expected 201, got {msg.status_code}"
        msg_data = msg.json()
        msg_id = msg_data['id']
        print(f'✓ POST /api/conversations/{{id}}/messages - Created message {msg_id}')

        # Test 2: List messages
        msgs = await client.get(f'/api/conversations/{conv_id}/messages')
        assert msgs.status_code == 200
        msgs_list = msgs.json()
        assert len(msgs_list) == 1
        print(f'✓ GET /api/conversations/{{id}}/messages - Listed {len(msgs_list)} message(s)')

        # Test 3: Get specific message
        single = await client.get(f'/api/messages/{msg_id}')
        assert single.status_code == 200
        assert single.json()['content'] == 'Hello from test'
        print(f'✓ GET /api/messages/{{id}} - Retrieved message')

        # Test 4: Update message
        update = await client.put(f'/api/messages/{msg_id}', json={'content': 'Updated message'})
        assert update.status_code == 200
        assert update.json()['content'] == 'Updated message'
        print(f'✓ PUT /api/messages/{{id}} - Updated message')

        # Test 5: Delete message
        delete = await client.delete(f'/api/messages/{msg_id}')
        assert delete.status_code == 204
        print(f'✓ DELETE /api/messages/{{id}} - Deleted message')

        # Verify deletion
        verify = await client.get(f'/api/messages/{msg_id}')
        assert verify.status_code == 404
        print(f'✓ Verified message was deleted (404)')

        print('\n✅ All Messages API tests PASSED!')


if __name__ == '__main__':
    asyncio.run(test_messages_api())
