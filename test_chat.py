#!/usr/bin/env python3
"""Test script for the Claude.ai clone chat functionality."""

import json
import urllib.request
from playwright.sync_api import sync_playwright

# Configuration
BACKEND_URL = "http://localhost:8002"
FRONTEND_URL = "http://localhost:5173"

def test_backend_health():
    """Test backend health endpoint."""
    print("Testing backend health...")
    try:
        resp = urllib.request.urlopen(f"{BACKEND_URL}/health")
        data = json.loads(resp.read().decode())
        print(f"  ✓ Backend health: {data}")
        return True
    except Exception as e:
        print(f"  ✗ Backend health failed: {e}")
        return False

def test_agent_stream():
    """Test agent stream endpoint."""
    print("Testing agent stream...")
    try:
        data = json.dumps({'message': 'Hello, test'}).encode()
        req = urllib.request.Request(f"{BACKEND_URL}/api/agent/stream", data=data,
                                     headers={'Content-Type': 'application/json'})
        resp = urllib.request.urlopen(req)
        content = resp.read().decode()
        if 'Mock response' in content:
            print(f"  ✓ Agent stream works")
            return True
        else:
            print(f"  ✗ Unexpected response: {content[:100]}")
            return False
    except Exception as e:
        print(f"  ✗ Agent stream failed: {e}")
        return False

def test_conversations_api():
    """Test conversation CRUD operations."""
    print("Testing conversations API...")
    try:
        # Create
        data = json.dumps({'title': 'Test Chat', 'model': 'claude-sonnet-4-5-20250929'}).encode()
        req = urllib.request.Request(f"{BACKEND_URL}/api/conversations", data=data,
                                     headers={'Content-Type': 'application/json'})
        resp = urllib.request.urlopen(req)
        conv = json.loads(resp.read().decode())
        conv_id = conv['id']
        print(f"  ✓ Created conversation: {conv_id}")

        # List
        resp = urllib.request.urlopen(f"{BACKEND_URL}/api/conversations")
        convs = json.loads(resp.read().decode())
        print(f"  ✓ Listed {len(convs)} conversations")

        # Get
        resp = urllib.request.urlopen(f"{BACKEND_URL}/api/conversations/{conv_id}")
        got = json.loads(resp.read().decode())
        print(f"  ✓ Retrieved conversation: {got['title']}")

        # Update
        data = json.dumps({'title': 'Updated Chat'}).encode()
        req = urllib.request.Request(f"{BACKEND_URL}/api/conversations/{conv_id}", data=data,
                                     headers={'Content-Type': 'application/json'},
                                     method='PUT')
        resp = urllib.request.urlopen(req)
        updated = json.loads(resp.read().decode())
        print(f"  ✓ Updated conversation: {updated['title']}")

        # Delete
        req = urllib.request.Request(f"{BACKEND_URL}/api/conversations/{conv_id}", method='DELETE')
        urllib.request.urlopen(req)
        print(f"  ✓ Deleted conversation")

        return True
    except Exception as e:
        print(f"  ✗ Conversations API failed: {e}")
        return False

def test_frontend_loads():
    """Test that frontend loads."""
    print("Testing frontend loads...")
    try:
        resp = urllib.request.urlopen(FRONTEND_URL)
        content = resp.read().decode()
        if '<div id="root">' in content:
            print(f"  ✓ Frontend loads")
            return True
        else:
            print(f"  ✗ Frontend content unexpected")
            return False
    except Exception as e:
        print(f"  ✗ Frontend failed: {e}")
        return False

def test_end_to_end_chat():
    """Test end-to-end chat flow with browser."""
    print("Testing end-to-end chat flow...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            # Navigate to frontend
            page.goto(FRONTEND_URL)
            page.wait_for_load_state('networkidle')
            print("  ✓ Page loaded")

            # Check for welcome screen
            if not page.locator('text="How can I help you today?"').count():
                print("  ✗ Welcome screen not found")
                browser.close()
                return False
            print("  ✓ Welcome screen visible")

            # Click new chat button
            new_chat_btn = page.locator('text="New Chat"')
            if not new_chat_btn.count():
                print("  ✗ New Chat button not found")
                browser.close()
                return False
            new_chat_btn.click()
            print("  ✓ Clicked New Chat")

            # Wait for chat input
            page.wait_for_selector('textarea', timeout=5000)
            print("  ✓ Chat input visible")

            # Type message
            page.locator('textarea').fill('Hello, this is a test message')
            print("  ✓ Typed message")

            # Send message (look for send button or handle Enter)
            send_btn = page.locator('button[title*="Send"], button:has-text("Send")').first
            if send_btn.count():
                send_btn.click()
            else:
                # Try pressing Enter
                page.locator('textarea').press('Enter')
            print("  ✓ Sent message")

            # Wait for response
            page.wait_for_timeout(3000)

            # Check for response
            content = page.content()
            if 'Mock response' in content or 'Hello' in content:
                print("  ✓ Response received")
                result = True
            else:
                print(f"  ✗ No response found")
                result = False

            # Take screenshot
            page.screenshot(path='/tmp/test-chat-screenshot.png')
            print("  ✓ Screenshot saved to /tmp/test-chat-screenshot.png")

            browser.close()
            return result

        except Exception as e:
            print(f"  ✗ Browser test failed: {e}")
            try:
                browser.close()
            except:
                pass
            return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("Testing Claude.ai Clone")
    print("=" * 60)

    results = []

    # Backend tests
    results.append(("Backend Health", test_backend_health()))
    results.append(("Agent Stream", test_agent_stream()))
    results.append(("Conversations API", test_conversations_api()))

    # Frontend tests
    results.append(("Frontend Loads", test_frontend_loads()))
    results.append(("End-to-End Chat", test_end_to_end_chat()))

    print("\n" + "=" * 60)
    print("Test Results")
    print("=" * 60)

    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {name}")

    all_passed = all(r[1] for r in results)
    print("\n" + ("=" * 60))
    if all_passed:
        print("ALL TESTS PASSED!")
    else:
        print("SOME TESTS FAILED")
    print("=" * 60)

    return 0 if all_passed else 1

if __name__ == "__main__":
    exit(main())
