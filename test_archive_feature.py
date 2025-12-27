#!/usr/bin/env python3
"""Test script for archive conversations feature."""

import json
import urllib.request
import time

def test_archive_conversation():
    """Test archiving a conversation."""
    print("Testing archive conversation feature...")

    # Create a test conversation
    data = json.dumps({'title': 'Test Archive Conversation'}).encode('utf-8')
    req = urllib.request.Request(
        'http://localhost:8000/api/conversations',
        data=data,
        headers={'Content-Type': 'application/json'}
    )
    response = urllib.request.urlopen(req, timeout=5)
    conv = json.loads(response.read().decode())
    conv_id = conv['id']
    print(f"✓ Created conversation: {conv_id}")

    # Archive the conversation
    data = json.dumps({'is_archived': True}).encode('utf-8')
    req = urllib.request.Request(
        f'http://localhost:8000/api/conversations/{conv_id}',
        data=data,
        headers={'Content-Type': 'application/json'},
        method='PUT'
    )
    response = urllib.request.urlopen(req, timeout=5)
    archived_conv = json.loads(response.read().decode())
    print(f"✓ Archived conversation: {conv_id}")

    # Verify it's archived
    assert archived_conv['is_archived'] == True, "Conversation should be archived"
    print("✓ Conversation is archived")

    # List conversations without archived (should not include it)
    response = urllib.request.urlopen('http://localhost:8000/api/conversations?archived=false', timeout=5)
    convs = json.loads(response.read().decode())
    archived_found = any(c['id'] == conv_id for c in convs)
    assert not archived_found, "Archived conversation should not appear in non-archived list"
    print("✓ Archived conversation hidden from main list")

    # List conversations with archived (should include it)
    response = urllib.request.urlopen('http://localhost:8000/api/conversations?archived=true', timeout=5)
    convs = json.loads(response.read().decode())
    archived_found = any(c['id'] == conv_id for c in convs)
    assert archived_found, "Archived conversation should appear in archived list"
    print("✓ Archived conversation found in archived list")

    # Unarchive the conversation
    data = json.dumps({'is_archived': False}).encode('utf-8')
    req = urllib.request.Request(
        f'http://localhost:8000/api/conversations/{conv_id}',
        data=data,
        headers={'Content-Type': 'application/json'},
        method='PUT'
    )
    response = urllib.request.urlopen(req, timeout=5)
    unarchived_conv = json.loads(response.read().decode())
    print(f"✓ Unarchived conversation: {conv_id}")

    # Verify it's unarchived
    assert unarchived_conv['is_archived'] == False, "Conversation should be unarchived"
    print("✓ Conversation is unarchived")

    # List conversations without archived (should include it now)
    response = urllib.request.urlopen('http://localhost:8000/api/conversations?archived=false', timeout=5)
    convs = json.loads(response.read().decode())
    unarchived_found = any(c['id'] == conv_id for c in convs)
    assert unarchived_found, "Unarchived conversation should appear in non-archived list"
    print("✓ Unarchived conversation found in main list")

    # Clean up - delete the test conversation
    req = urllib.request.Request(
        f'http://localhost:8000/api/conversations/{conv_id}',
        method='DELETE'
    )
    response = urllib.request.urlopen(req, timeout=5)
    print(f"✓ Deleted test conversation: {conv_id}")

    print("✓ Archive feature test completed successfully!")
    return True

def main():
    print("=" * 60)
    print("Testing Archive Conversations Feature")
    print("=" * 60)

    try:
        success = test_archive_conversation()
        print("=" * 60)
        print("Archive Feature: PASSED")
        print("=" * 60)
        return True
    except Exception as e:
        print(f"✗ Archive feature test failed: {e}")
        print("=" * 60)
        print("Archive Feature: FAILED")
        print("=" * 60)
        return False

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)