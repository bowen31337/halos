#!/usr/bin/env python3
"""Simple test script to verify application features."""

import json
import urllib.request
import time

def test_backend_health():
    """Test 1: Backend is running and healthy."""
    try:
        response = urllib.request.urlopen('http://localhost:8000/health', timeout=5)
        data = json.loads(response.read().decode())
        assert data['status'] == 'healthy'
        print("✓ Backend is healthy")
        return True
    except Exception as e:
        print(f"✗ Backend health check failed: {e}")
        return False

def test_frontend_loaded():
    """Test 2: Frontend is accessible."""
    try:
        response = urllib.request.urlopen('http://localhost:5173/', timeout=5)
        html = response.read().decode()
        assert 'html' in html.lower()
        print("✓ Frontend is loaded")
        return True
    except Exception as e:
        print(f"✗ Frontend load failed: {e}")
        return False

def test_create_conversation():
    """Test 3: Create a conversation."""
    try:
        data = json.dumps({'title': 'Test Conversation'}).encode('utf-8')
        req = urllib.request.Request(
            'http://localhost:8000/api/conversations',
            data=data,
            headers={'Content-Type': 'application/json'}
        )
        response = urllib.request.urlopen(req, timeout=5)
        conv = json.loads(response.read().decode())
        assert 'id' in conv
        print(f"✓ Created conversation: {conv['id']}")
        return conv['id']
    except Exception as e:
        print(f"✗ Create conversation failed: {e}")
        return None

def test_list_conversations():
    """Test 4: List conversations."""
    try:
        response = urllib.request.urlopen('http://localhost:8000/api/conversations', timeout=5)
        convs = json.loads(response.read().decode())
        assert isinstance(convs, list)
        print(f"✓ Listed {len(convs)} conversations")
        return True
    except Exception as e:
        print(f"✗ List conversations failed: {e}")
        return False

def test_rename_conversation(conv_id):
    """Test 5: Rename conversation."""
    try:
        data = json.dumps({'title': 'Renamed Test Conversation'}).encode('utf-8')
        req = urllib.request.Request(
            f'http://localhost:8000/api/conversations/{conv_id}',
            data=data,
            headers={'Content-Type': 'application/json'},
            method='PUT'
        )
        response = urllib.request.urlopen(req, timeout=5)
        print(f"✓ Renamed conversation: {conv_id}")
        return True
    except Exception as e:
        print(f"✗ Rename conversation failed: {e}")
        return False

def test_delete_conversation(conv_id):
    """Test 6: Delete conversation."""
    try:
        req = urllib.request.Request(
            f'http://localhost:8000/api/conversations/{conv_id}',
            method='DELETE'
        )
        response = urllib.request.urlopen(req, timeout=5)
        print(f"✓ Deleted conversation: {conv_id}")
        return True
    except Exception as e:
        print(f"✗ Delete conversation failed: {e}")
        return False

def main():
    print("=" * 60)
    print("Testing Application Features")
    print("=" * 60)

    results = []

    # Test backend health
    results.append(test_backend_health())

    # Test frontend loaded
    results.append(test_frontend_loaded())

    # Test create conversation
    conv_id = test_create_conversation()
    results.append(conv_id is not None)

    # Test list conversations
    results.append(test_list_conversations())

    if conv_id:
        # Test rename conversation
        results.append(test_rename_conversation(conv_id))

        # Test delete conversation
        results.append(test_delete_conversation(conv_id))

    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 60)

    return all(results)

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
