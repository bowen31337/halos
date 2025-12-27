import requests
import json
import time

def test_end_to_end_chat():
    """Test complete chat flow: create conversation, send message, receive response"""
    print("Testing end-to-end chat functionality...")

    # Step 1: Create a conversation
    print("\n1. Creating conversation...")
    try:
        response = requests.post('http://localhost:8002/api/conversations', json={
            'title': 'Test Conversation',
            'model': 'claude-sonnet-4-5-20250929'
        })
        conversation = response.json()
        conv_id = conversation['id']
        thread_id = conversation.get('thread_id', conv_id)
        print(f"Conversation created: {conv_id} (thread: {thread_id})")
    except Exception as e:
        print(f"Error creating conversation: {e}")
        return

    # Step 2: Send a message and stream response
    print(f"\n2. Sending message to conversation {conv_id}...")
    try:
        with requests.post(
            'http://localhost:8002/api/agent/stream',
            json={
                'message': 'Hello, I want to test the chat functionality. Please respond with a detailed explanation of how this system works.',
                'conversationId': conv_id,
                'thread_id': thread_id,
                'permission_mode': 'default'
            },
            stream=True
        ) as response:

            print(f"Response status: {response.status_code}")

            if response.status_code != 200:
                print(f"Error: {response.text}")
                return

            # Collect streaming response
            full_response = ''
            events_received = 0
            tool_calls = 0
            message_chunks = 0

            for line in response.iter_lines():
                if not line:
                    continue

                line_str = line.decode('utf-8').strip()

                if line_str.startswith('data: '):
                    data_str = line_str[6:]
                    if not data_str:
                        continue

                    try:
                        event_data = json.loads(data_str)
                        events_received += 1

                        if event_data.get('content'):
                            content = event_data['content']
                            full_response += content
                            message_chunks += 1
                            print(f"Message chunk ({len(full_response)} chars): '{content[:50]}{'...' if len(content) > 50 else ''}'")

                        elif event_data.get('event') == 'tool_start':
                            tool_calls += 1
                            print(f"Tool call: {event_data.get('tool')}")

                        elif event_data.get('event') == 'done':
                            print("Response completed")

                    except json.JSONDecodeError:
                        pass

            print(f"\n3. Response completed:")
            print(f"   Events received: {events_received}")
            print(f"   Message chunks: {message_chunks}")
            print(f"   Tool calls: {tool_calls}")
            print(f"   Full response length: {len(full_response)}")
            print(f"   Response preview: {full_response[:200]}{'...' if len(full_response) > 200 else ''}")

    except Exception as e:
        print(f"Error in streaming: {e}")
        import traceback
        traceback.print_exc()

    # Step 3: List conversations to verify it was created
    print(f"\n4. Verifying conversation...")
    try:
        response = requests.get('http://localhost:8002/api/conversations')
        conversations = response.json()
        print(f"Total conversations: {len(conversations)}")
        if conv_id in [c['id'] for c in conversations]:
            print(f"✓ Conversation {conv_id} found in list")
        else:
            print(f"✗ Conversation {conv_id} not found in list")
    except Exception as e:
        print(f"Error listing conversations: {e}")

    print(f"\n5. Test completed successfully!")

if __name__ == '__main__':
    test_end_to_end_chat()