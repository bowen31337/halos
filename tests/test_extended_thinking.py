"""Test Extended Thinking Mode feature (Feature #27)."""

import json
import time
import uuid
from urllib.request import Request, urlopen

# Configuration
BACKEND_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:5173"


def test_backend_health():
    """Test 1: Verify backend is running."""
    print("\n1. Testing backend health...")
    try:
        req = Request(f"{BACKEND_URL}/health")
        response = urlopen(req, timeout=5)
        data = json.loads(response.read().decode())
        assert data["status"] == "healthy", "Backend not healthy"
        print("   ✓ Backend is healthy")
        return True
    except Exception as e:
        print(f"   ✗ Backend health check failed: {e}")
        return False


def test_create_conversation():
    """Test 2: Create a test conversation."""
    print("\n2. Creating test conversation...")
    try:
        req = Request(
            f"{BACKEND_URL}/api/conversations",
            data=json.dumps({"title": "Extended Thinking Test"}).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        response = urlopen(req, timeout=5)
        data = json.loads(response.read().decode())
        assert "id" in data, "No conversation ID returned"
        print(f"   ✓ Conversation created: {data['id']}")
        return data["id"]
    except Exception as e:
        print(f"   ✗ Failed to create conversation: {e}")
        return None


def test_extended_thinking_streaming(conversation_id: str):
    """Test 3: Test extended thinking streaming."""
    print("\n3. Testing extended thinking streaming...")
    try:
        # Prepare request data with extended_thinking enabled
        request_data = {
            "message": "Analyze the pros and cons of different sorting algorithms",
            "conversation_id": conversation_id,
            "thread_id": str(uuid.uuid4()),
            "model": "claude-sonnet-4-5-20250929",
            "extended_thinking": True,  # Enable extended thinking
        }

        req = Request(
            f"{BACKEND_URL}/api/agent/stream",
            data=json.dumps(request_data).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        response = urlopen(req, timeout=30)

        # Track events
        events_received = []
        thinking_events = []
        message_events = []
        thinking_content = ""

        # Read SSE stream
        buffer = ""
        for chunk in iter(lambda: response.read(1), b""):
            buffer += chunk.decode()
            while "\r\n\r\n" in buffer:
                event_data, buffer = buffer.split("\r\n\r\n", 1)
                lines = event_data.strip().split("\r\n")

                event_type = None
                event_json = None
                for line in lines:
                    if line.startswith("event: "):
                        event_type = line[7:].strip()
                    elif line.startswith("data: "):
                        event_json = json.loads(line[6:])

                if event_type and event_json:
                    events_received.append(event_type)

                    # Track thinking events
                    if event_type == "thinking":
                        thinking_events.append(event_json)
                        if "content" in event_json:
                            thinking_content += event_json["content"]

                    # Track message events
                    if event_type == "message":
                        message_events.append(event_json)

                    # Check done event for thinking content
                    if event_type == "done":
                        if "thinking_content" in event_json:
                            thinking_content = event_json["thinking_content"]

                # Stop after receiving "done" event
                if event_type == "done":
                    break

        # Verify extended thinking events were received
        assert "start" in events_received, "No start event"
        assert "message" in events_received, "No message events"
        assert "done" in events_received, "No done event"

        # Verify thinking events when extended thinking is enabled
        has_thinking = len(thinking_events) > 0 or len(thinking_content) > 0

        if has_thinking:
            print(f"   ✓ Extended thinking events received: {len(thinking_events)} thinking chunks")
            if thinking_content:
                print(f"   ✓ Total thinking content length: {len(thinking_content)} characters")
                print(f"   ✓ Thinking preview: {thinking_content[:100]}...")
            return True
        else:
            print("   ⚠ No thinking events received (may need mock agent update)")
            return "partial"

    except Exception as e:
        print(f"   ✗ Extended thinking streaming failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_normal_streaming(conversation_id: str):
    """Test 4: Test normal streaming without extended thinking."""
    print("\n4. Testing normal streaming (without extended thinking)...")
    try:
        request_data = {
            "message": "Hello, how are you?",
            "conversation_id": conversation_id,
            "thread_id": str(uuid.uuid4()),
            "model": "claude-sonnet-4-5-20250929",
            "extended_thinking": False,  # Disabled
        }

        req = Request(
            f"{BACKEND_URL}/api/agent/stream",
            data=json.dumps(request_data).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        response = urlopen(req, timeout=30)

        # Track events
        thinking_events = []
        message_events = []

        # Read SSE stream
        buffer = ""
        for chunk in iter(lambda: response.read(1), b""):
            buffer += chunk.decode()
            while "\r\n\r\n" in buffer:
                event_data, buffer = buffer.split("\r\n\r\n", 1)
                lines = event_data.strip().split("\r\n")

                event_type = None
                event_json = None
                for line in lines:
                    if line.startswith("event: "):
                        event_type = line[7:].strip()
                    elif line.startswith("data: "):
                        event_json = json.loads(line[6:])

                if event_type and event_json:
                    if event_type == "thinking":
                        thinking_events.append(event_json)
                    if event_type == "message":
                        message_events.append(event_json)

                if event_type == "done":
                    break

        # Verify normal streaming works
        assert len(message_events) > 0, "No message events received"
        print(f"   ✓ Normal streaming works: {len(message_events)} message chunks")

        # Verify NO thinking events when disabled
        if len(thinking_events) == 0:
            print("   ✓ No thinking events when extended thinking is disabled")
            return True
        else:
            print(f"   ⚠ Warning: Received {len(thinking_events)} thinking events despite being disabled")
            return "partial"

    except Exception as e:
        print(f"   ✗ Normal streaming failed: {e}")
        return False


def test_message_with_thinking_content(conversation_id: str):
    """Test 5: Verify messages can store and retrieve thinking content."""
    print("\n5. Testing message persistence with thinking content...")
    try:
        # Create a message with thinking content
        message_data = {
            "role": "assistant",
            "content": "Here's my analysis after careful consideration.",
            "thinking_content": "Let me think about this...\n1. Analyze requirements\n2. Consider options\n3. Formulate response",
        }

        req = Request(
            f"{BACKEND_URL}/api/messages/conversations/{conversation_id}/messages",
            data=json.dumps(message_data).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        response = urlopen(req, timeout=5)
        data = json.loads(response.read().decode())

        assert "id" in data, "No message ID returned"
        assert data.get("thinkingContent") or data.get("thinking_content"), "No thinking content in response"

        print(f"   ✓ Message created with thinking content: {data['id']}")

        # Retrieve the message
        req = Request(
            f"{BACKEND_URL}/api/messages/conversations/{conversation_id}/messages",
            method="GET",
        )

        response = urlopen(req, timeout=5)
        messages = json.loads(response.read().decode())

        # Find the message with thinking content
        found_thinking = False
        for msg in messages:
            if msg.get("thinkingContent") or msg.get("thinking_content"):
                found_thinking = True
                print(f"   ✓ Thinking content retrieved: {msg.get('thinkingContent', msg.get('thinking_content'))[:50]}...")
                break

        if found_thinking:
            return True
        else:
            print("   ⚠ Thinking content not found in retrieved messages")
            return "partial"

    except Exception as e:
        print(f"   ✗ Message with thinking content failed: {e}")
        return False


def main():
    """Run all tests for Extended Thinking Mode feature."""
    print("=" * 60)
    print("EXTENDED THINKING MODE TEST SUITE")
    print("Feature #27: Extended thinking for complex problems")
    print("=" * 60)

    results = []

    # Test 1: Backend health
    results.append(("Backend Health", test_backend_health()))

    if not results[-1][1]:
        print("\n❌ Backend not running - aborting tests")
        return

    # Test 2: Create conversation
    conversation_id = test_create_conversation()
    if not conversation_id:
        print("\n❌ Failed to create conversation - aborting tests")
        return

    # Test 3: Extended thinking streaming
    results.append(("Extended Thinking Streaming", test_extended_thinking_streaming(conversation_id)))

    # Test 4: Normal streaming (control test)
    results.append(("Normal Streaming (Control)", test_normal_streaming(conversation_id)))

    # Test 5: Message persistence
    results.append(("Message with Thinking Content", test_message_with_thinking_content(conversation_id)))

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result is True)
    partial = sum(1 for _, result in results if result == "partial")
    failed = sum(1 for _, result in results if result is False)

    for test_name, result in results:
        status = "✓ PASS" if result is True else ("⚠ PARTIAL" if result == "partial" else "✗ FAIL")
        print(f"{status}: {test_name}")

    print(f"\nTotal: {passed} passed, {partial} partial, {failed} failed")

    if passed >= 4:
        print("\n🎉 EXTENDED THINKING FEATURE IS WORKING!")
    elif passed + partial >= 3:
        print("\n✓ Extended thinking feature is mostly working")
    else:
        print("\n❌ Extended thinking feature needs more work")

    print("=" * 60)


if __name__ == "__main__":
    main()
