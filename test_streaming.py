import asyncio
import aiohttp
import json
import sys
import os

# Add the project root to Python path
sys.path.insert(0, '/media/DATA/projects/autonomous-coding-clone-cc/talos')

async def test_agent_streaming():
    """Test the agent streaming endpoint directly"""
    print("Testing agent streaming endpoint...")

    async with aiohttp.ClientSession() as session:
        # Test data
        test_data = {
            "message": "Hello, this is a test message from the frontend!",
            "thread_id": f"test-thread-{int(asyncio.get_event_loop().time())}",
            "permission_mode": "default"
        }

        print(f"Sending request to http://localhost:8002/api/agent/stream")
        print(f"Data: {json.dumps(test_data, indent=2)}")

        try:
            async with session.post(
                'http://localhost:8002/api/agent/stream',
                json=test_data,
                headers={'Content-Type': 'application/json'}
            ) as response:

                print(f"Response status: {response.status}")
                print(f"Response headers: {dict(response.headers)}")

                if response.status != 200:
                    print(f"Error response: {await response.text()}")
                    return

                # Read streaming response
                buffer = ''
                received_events = []

                async for line in response.content:
                    if not line:
                        continue

                    line_str = line.decode('utf-8').strip()
                    print(f"Raw line: {line_str}")

                    if line_str.startswith('data: '):
                        data_str = line_str[6:]  # Remove 'data: ' prefix
                        if not data_str:
                            continue

                        try:
                            # Check if it's a proper JSON object
                            if data_str.startswith('{') and data_str.endswith('}'):
                                event_data = json.loads(data_str)
                                received_events.append(event_data)
                                print(f"Event received: {json.dumps(event_data, indent=2)}")

                                if event_data.get('content'):
                                    print(f"Message chunk: '{event_data['content']}'")
                                elif event_data.get('event'):
                                    print(f"Event type: {event_data['event']}")

                            else:
                                print(f"Non-JSON data: {data_str}")

                        except json.JSONDecodeError as e:
                            print(f"JSON decode error: {e}")
                            print(f"Data: {data_str}")

                print(f"\nTotal events received: {len(received_events)}")
                print("All events:")
                for i, event in enumerate(received_events):
                    print(f"  {i+1}: {json.dumps(event)}")

        except Exception as e:
            print(f"Error: {e}")

if __name__ == '__main__':
    asyncio.run(test_agent_streaming())