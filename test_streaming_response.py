import requests
import json
import time

def test_streaming_response():
    """Test actual streaming response content"""
    print("Testing streaming response content...")

    try:
        with requests.post(
            'http://localhost:8002/api/agent/stream',
            json={
                'message': 'Hello, this is a test message from the frontend!',
                'thread_id': f'test-thread-{int(time.time())}',
                'permission_mode': 'default'
            },
            stream=True
        ) as response:

            print(f"Response status: {response.status_code}")
            print(f"Content-Type: {response.headers.get('content-type')}")

            if response.status_code != 200:
                print(f"Error: {response.text}")
                return

            # Read streaming response line by line
            buffer = ''
            received_events = []

            for line in response.iter_lines():
                if not line:
                    continue

                line_str = line.decode('utf-8').strip()
                print(f"Raw line: {line_str}")

                if line_str.startswith('data: '):
                    data_str = line_str[6:]  # Remove 'data: ' prefix
                    if not data_str:
                        continue

                    try:
                        # Parse JSON data
                        event_data = json.loads(data_str)
                        received_events.append(event_data)
                        print(f"Event: {json.dumps(event_data, indent=2)}")

                        if event_data.get('content'):
                            print(f"Message chunk: '{event_data['content']}'")
                        elif event_data.get('event'):
                            print(f"Event type: {event_data['event']}")

                    except json.JSONDecodeError as e:
                        print(f"JSON decode error: {e}")
                        print(f"Data: {data_str}")

            print(f"\nTotal events received: {len(received_events)}")
            if received_events:
                print("Sample events:")
                for i, event in enumerate(received_events[:3]):  # Show first 3
                    print(f"  {i+1}: {json.dumps(event)}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_streaming_response()