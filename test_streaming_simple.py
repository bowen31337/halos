import urllib.request
import urllib.parse
import json
import time

def test_agent_streaming():
    """Test the agent streaming endpoint using standard library"""
    print("Testing agent streaming endpoint...")

    # Test data
    test_data = {
        "message": "Hello, this is a test message from the frontend!",
        "thread_id": f"test-thread-{int(time.time())}",
        "permission_mode": "default"
    }

    print(f"Sending request to http://localhost:8002/api/agent/stream")
    print(f"Data: {json.dumps(test_data, indent=2)}")

    try:
        # Create request
        url = 'http://localhost:8002/api/agent/stream'
        data = json.dumps(test_data).encode('utf-8')
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'text/event-stream',
            'Cache-Control': 'no-cache'
        }

        req = urllib.request.Request(url, data=data, headers=headers)

        with urllib.request.urlopen(req) as response:
            print(f"Response status: {response.status}")
            print(f"Response headers: {dict(response.headers)}")

            if response.status != 200:
                print(f"Error response: {response.read().decode('utf-8')}")
                return

            # Read streaming response
            buffer = ''
            received_events = []

            # Read line by line
            while True:
                try:
                    line = response.readline().decode('utf-8').strip()
                    if not line:
                        continue

                    print(f"Raw line: {line}")

                    if line.startswith('data: '):
                        data_str = line[6:]  # Remove 'data: ' prefix
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

                except Exception as e:
                    print(f"Read error: {e}")
                    break

            print(f"\nTotal events received: {len(received_events)}")
            print("All events:")
            for i, event in enumerate(received_events):
                print(f"  {i+1}: {json.dumps(event)}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    test_agent_streaming()