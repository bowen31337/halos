"""Test Conversations API CRUD Operations

This test suite verifies that the Conversations API endpoints work correctly.
"""

import pytest
import urllib.request
import json
from typing import Dict, Any


BASE_URL = "http://localhost:8000"


def api_request(method: str, path: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
    """Helper to make API requests."""
    url = f"{BASE_URL}{path}"
    headers = {'Content-Type': 'application/json'}

    if method == 'GET':
        req = urllib.request.Request(url, headers=headers)
    elif method == 'POST':
        req = urllib.request.Request(url, data=json.dumps(data).encode(), headers=headers, method='POST')
    elif method == 'PUT':
        req = urllib.request.Request(url, data=json.dumps(data).encode(), headers=headers, method='PUT')
    elif method == 'DELETE':
        req = urllib.request.Request(url, headers=headers, method='DELETE')
    else:
        raise ValueError(f"Unknown method: {method}")

    try:
        response = urllib.request.urlopen(req)
        body = response.read().decode()
        # DELETE returns 204 No Content with empty body
        if not body:
            return {'status': 'success', 'code': response.code}
        return json.loads(body)
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        return {'error': e.code, 'message': error_body}


def test_list_conversations():
    """Test GET /api/conversations returns list."""
    result = api_request('GET', '/api/conversations')
    assert 'error' not in result, f"Should not return error: {result}"
    assert isinstance(result, list), "Should return a list"
    print(f"✓ Listed {len(result)} conversations")


def test_create_conversation():
    """Test POST /api/conversations creates a new conversation."""
    new_conv = api_request('POST', '/api/conversations', {
        'title': 'Test Conversation',
        'model': 'claude-sonnet-4-5-20250929'
    })
    assert 'error' not in new_conv, f"Should not return error: {new_conv}"
    assert 'id' in new_conv, "Should have conversation ID"
    assert new_conv['title'] == 'Test Conversation', "Title should match"
    print(f"✓ Created conversation: {new_conv['id']}")


def test_get_conversation_by_id():
    """Test GET /api/conversations/{id} returns specific conversation."""
    # First create a conversation
    created = api_request('POST', '/api/conversations', {
        'title': 'Get Test',
        'model': 'claude-sonnet-4-5-20250929'
    })

    # Then get it
    result = api_request('GET', f"/api/conversations/{created['id']}")
    assert 'error' not in result, f"Should not return error: {result}"
    assert result['id'] == created['id'], "ID should match"
    assert result['title'] == 'Get Test', "Title should match"
    print(f"✓ Retrieved conversation by ID")


def test_update_conversation():
    """Test PUT /api/conversations/{id} updates conversation."""
    # Create a conversation
    created = api_request('POST', '/api/conversations', {
        'title': 'Original Title',
        'model': 'claude-sonnet-4-5-20250929'
    })

    # Update it
    updated = api_request('PUT', f"/api/conversations/{created['id']}", {
        'title': 'Updated Title'
    })
    assert 'error' not in updated, f"Should not return error: {updated}"
    assert updated['title'] == 'Updated Title', "Title should be updated"
    print(f"✓ Updated conversation title")


def test_delete_conversation():
    """Test DELETE /api/conversations/{id} removes conversation."""
    # Create a conversation
    created = api_request('POST', '/api/conversations', {
        'title': 'To Be Deleted',
        'model': 'claude-sonnet-4-5-20250929'
    })

    # Delete it
    result = api_request('DELETE', f"/api/conversations/{created['id']}")
    assert 'error' not in result, f"Should not return error: {result}"

    # Verify it's gone
    result = api_request('GET', f"/api/conversations/{created['id']}")
    assert 'error' in result, "Should return error for deleted conversation"
    print(f"✓ Deleted conversation")


def test_conversation_has_required_fields():
    """Test that conversations have all required fields."""
    created = api_request('POST', '/api/conversations', {
        'title': 'Field Test',
        'model': 'claude-sonnet-4-5-20250929'
    })

    required_fields = ['id', 'title', 'model', 'created_at', 'updated_at']
    for field in required_fields:
        assert field in created, f"Missing required field: {field}"
    print(f"✓ Conversation has all required fields")


def test_conversation_default_values():
    """Test that conversations have sensible defaults."""
    created = api_request('POST', '/api/conversations', {
        'title': 'Defaults Test'
    })

    assert created['title'] == 'Defaults Test', "Title should be set"
    assert 'model' in created, "Should have a model field"
    assert 'created_at' in created, "Should have created_at timestamp"
    print(f"✓ Conversation defaults are correct")


def test_conversation_pagination():
    """Test that list endpoint supports pagination."""
    # Create multiple conversations
    for i in range(5):
        api_request('POST', '/api/conversations', {
            'title': f'Pagination Test {i}',
            'model': 'claude-sonnet-4-5-20250929'
        })

    # Try getting with limit
    result = api_request('GET', '/api/conversations?limit=3')
    assert 'error' not in result, f"Should not return error: {result}"
    # Most endpoints return list, check length
    if isinstance(result, list):
        assert len(result) <= 3, "Should respect limit parameter"
    print(f"✓ Pagination parameters work")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
