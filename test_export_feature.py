#!/usr/bin/env python3
"""Test export conversation feature (JSON and Markdown formats)."""

import json
import urllib.request
import urllib.parse
import tempfile
import os

def test_export_json():
    """Test exporting a conversation as JSON."""
    print("\n" + "=" * 70)
    print("Testing JSON Export")
    print("=" * 70)

    # Step 1: Create a test conversation with messages
    print("\n1. Creating test conversation...")
    data = json.dumps({'title': 'Test JSON Export'}).encode('utf-8')
    req = urllib.request.Request(
        'http://localhost:8000/api/conversations',
        data=data,
        headers={'Content-Type': 'application/json'}
    )
    response = urllib.request.urlopen(req, timeout=5)
    conv = json.loads(response.read().decode())
    conv_id = conv['id']
    print(f"✓ Created conversation: {conv_id}")

    # Step 2: Add a message
    print("\n2. Adding test message...")
    data = json.dumps({
        'role': 'user',
        'content': 'This is a test message for JSON export'
    }).encode('utf-8')
    req = urllib.request.Request(
        f'http://localhost:8000/api/messages/conversations/{conv_id}/messages',
        data=data,
        headers={'Content-Type': 'application/json'}
    )
    response = urllib.request.urlopen(req, timeout=5)
    msg = json.loads(response.read().decode())
    print(f"✓ Added message: {msg['id']}")

    # Step 3: Export as JSON
    print("\n3. Exporting conversation as JSON...")
    export_url = f'http://localhost:8000/api/conversations/{conv_id}/export?format=json'
    req = urllib.request.Request(export_url, method='POST')
    response = urllib.request.urlopen(req, timeout=5)

    # Verify content type
    content_type = response.headers.get('Content-Type')
    assert 'application/json' in content_type, f"Expected JSON content type, got {content_type}"
    print(f"✓ Content-Type: {content_type}")

    # Get filename from Content-Disposition
    content_disp = response.headers.get('Content-Disposition')
    print(f"✓ Content-Disposition: {content_disp}")
    assert 'attachment' in content_disp, "Expected attachment disposition"
    assert '.json' in content_disp, "Expected .json filename extension"

    # Parse and verify JSON content
    export_data = json.loads(response.read().decode())
    assert export_data['id'] == conv_id, "Export data should have correct conversation ID"
    assert export_data['title'] == 'Test JSON Export', "Export data should have correct title"
    assert 'messages' in export_data, "Export data should contain messages"
    assert len(export_data['messages']) == 1, "Should have 1 message"
    assert export_data['messages'][0]['content'] == 'This is a test message for JSON export'
    print("✓ JSON export content verified")
    print(f"  - Title: {export_data['title']}")
    print(f"  - Messages: {len(export_data['messages'])}")
    print(f"  - Model: {export_data['model']}")

    # Clean up
    req = urllib.request.Request(
        f'http://localhost:8000/api/conversations/{conv_id}',
        method='DELETE'
    )
    urllib.request.urlopen(req, timeout=5)
    print(f"\n✓ Cleaned up test conversation")

    print("\n✅ JSON Export Test PASSED")
    return True

def test_export_markdown():
    """Test exporting a conversation as Markdown."""
    print("\n" + "=" * 70)
    print("Testing Markdown Export")
    print("=" * 70)

    # Step 1: Create a test conversation
    print("\n1. Creating test conversation...")
    data = json.dumps({'title': 'Test Markdown Export'}).encode('utf-8')
    req = urllib.request.Request(
        'http://localhost:8000/api/conversations',
        data=data,
        headers={'Content-Type': 'application/json'}
    )
    response = urllib.request.urlopen(req, timeout=5)
    conv = json.loads(response.read().decode())
    conv_id = conv['id']
    print(f"✓ Created conversation: {conv_id}")

    # Step 2: Add messages with different roles
    print("\n2. Adding test messages...")
    messages = [
        {'role': 'user', 'content': 'What is Python?'},
        {'role': 'assistant', 'content': 'Python is a high-level programming language.'},
    ]

    for msg_data in messages:
        data = json.dumps(msg_data).encode('utf-8')
        req = urllib.request.Request(
            f'http://localhost:8000/api/messages/conversations/{conv_id}/messages',
            data=data,
            headers={'Content-Type': 'application/json'}
        )
        response = urllib.request.urlopen(req, timeout=5)
        print(f"✓ Added {msg_data['role']} message")

    # Step 3: Export as Markdown
    print("\n3. Exporting conversation as Markdown...")
    export_url = f'http://localhost:8000/api/conversations/{conv_id}/export?format=markdown'
    req = urllib.request.Request(export_url, method='POST')
    response = urllib.request.urlopen(req, timeout=5)

    # Verify content type
    content_type = response.headers.get('Content-Type')
    assert 'text/markdown' in content_type, f"Expected Markdown content type, got {content_type}"
    print(f"✓ Content-Type: {content_type}")

    # Get filename
    content_disp = response.headers.get('Content-Disposition')
    print(f"✓ Content-Disposition: {content_disp}")
    assert 'attachment' in content_disp, "Expected attachment disposition"
    assert '.md' in content_disp, "Expected .md filename extension"

    # Parse and verify Markdown content
    md_content = response.read().decode()
    assert '# Test Markdown Export' in md_content, "Should have title as h1"
    assert '## 👤 User' in md_content, "Should have user section"
    assert '## 🤖 Assistant' in md_content, "Should have assistant section"
    assert 'What is Python?' in md_content, "Should have user message"
    assert 'Python is a high-level programming language' in md_content, "Should have assistant message"
    assert '**Model:**' in md_content, "Should have model info"
    assert '**Created:**' in md_content, "Should have created date"
    print("✓ Markdown export content verified")
    print("\n  Markdown preview:")
    print("  " + "\n  ".join(md_content.split('\n')[:15]))

    # Clean up
    req = urllib.request.Request(
        f'http://localhost:8000/api/conversations/{conv_id}',
        method='DELETE'
    )
    urllib.request.urlopen(req, timeout=5)
    print(f"\n✓ Cleaned up test conversation")

    print("\n✅ Markdown Export Test PASSED")
    return True

def test_export_invalid_format():
    """Test that invalid format returns error."""
    print("\n" + "=" * 70)
    print("Testing Invalid Format Handling")
    print("=" * 70)

    # Create a test conversation
    print("\n1. Creating test conversation...")
    data = json.dumps({'title': 'Test Invalid Format'}).encode('utf-8')
    req = urllib.request.Request(
        'http://localhost:8000/api/conversations',
        data=data,
        headers={'Content-Type': 'application/json'}
    )
    response = urllib.request.urlopen(req, timeout=5)
    conv = json.loads(response.read().decode())
    conv_id = conv['id']
    print(f"✓ Created conversation: {conv_id}")

    # Try invalid format
    print("\n2. Testing invalid format 'pdf'...")
    try:
        export_url = f'http://localhost:8000/api/conversations/{conv_id}/export?format=pdf'
        req = urllib.request.Request(export_url, method='POST')
        response = urllib.request.urlopen(req, timeout=5)
        print("✗ Should have raised an error for invalid format")
        return False
    except urllib.error.HTTPError as e:
        assert e.code == 400, f"Expected 400 error, got {e.code}"
        print(f"✓ Correctly returned 400 error for invalid format")
        error_body = e.read().decode()
        assert 'Unsupported format' in error_body, "Error message should mention unsupported format"
        print(f"✓ Error message: {error_body[:100]}...")

    # Clean up
    req = urllib.request.Request(
        f'http://localhost:8000/api/conversations/{conv_id}',
        method='DELETE'
    )
    urllib.request.urlopen(req, timeout=5)
    print(f"\n✓ Cleaned up test conversation")

    print("\n✅ Invalid Format Test PASSED")
    return True

def main():
    print("=" * 70)
    print("Export Conversation Feature Test Suite")
    print("=" * 70)

    try:
        success1 = test_export_json()
        success2 = test_export_markdown()
        success3 = test_export_invalid_format()

        if success1 and success2 and success3:
            print("\n" + "=" * 70)
            print("🎉 EXPORT FEATURE: ALL TESTS PASSED")
            print("✓ JSON export working")
            print("✓ Markdown export working")
            print("✓ Invalid format handling working")
            print("✓ File downloads working")
            print("=" * 70)
            return True
        else:
            print("\n" + "=" * 70)
            print("❌ EXPORT FEATURE: SOME TESTS FAILED")
            print("=" * 70)
            return False

    except Exception as e:
        print(f"\n✗ Export feature test failed: {e}")
        import traceback
        traceback.print_exc()
        print("\n" + "=" * 70)
        print("❌ EXPORT FEATURE: FAILED")
        print("=" * 70)
        return False

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
