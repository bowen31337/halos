"""Test Messages API CRUD Operations

This test suite verifies that the Messages API endpoints work correctly.
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


def get_or_create_conversation() -> str:
    """Helper to get or create a test conversation."""
    convs = api_request('GET', '/api/conversations')
    if isinstance(convs, list) and len(convs) > 0:
        return convs[0]['id']

    # Create new
    conv = api_request('POST', '/api/conversations', {
        'title': 'Message Test',
        'model': 'claude-sonnet-4-5-20250929'
    })
    return conv['id']


def test_list_messages():
    """Test GET /api/conversations/{id}/messages returns messages."""
    conv_id = get_or_create_conversation()
    result = api_request('GET', f"/api/conversations/{conv_id}/messages")
    assert 'error' not in result, f"Should not return error: {result}"
    assert isinstance(result, list), "Should return a list"
    print(f"✓ Listed {len(result)} messages")


def test_create_message():
    """Test POST /api/conversations/{id}/messages creates a message."""
    conv_id = get_or_create_conversation()
    message = api_request('POST', f"/api/conversations/{conv_id}/messages", {
        'role': 'user',
        'content': 'Test message content'
    })
    assert 'error' not in message, f"Should not return error: {message}"
    assert 'id' in message, "Should have message ID"
    assert message['role'] == 'user', "Role should match"
    assert message['content'] == 'Test message content', "Content should match"
    print(f"✓ Created message: {message['id']}")
    return message


def test_create_message_with_attachments():
    """Test creating a message with image attachments."""
    conv_id = get_or_create_conversation()
    message = api_request('POST', f"/api/conversations/{conv_id}/messages", {
        'role': 'user',
        'content': 'Message with image',
        'attachments': ['http://example.com/image.png']
    })
    assert 'error' not in message, f"Should not return error: {message}"
    assert 'attachments' in message, "Should have attachments field"
    print(f"✓ Created message with attachments")


def test_create_assistant_message():
    """Test creating an assistant message."""
    conv_id = get_or_create_conversation()
    message = api_request('POST', f"/api/conversations/{conv_id}/messages", {
        'role': 'assistant',
        'content': 'Assistant response'
    })
    assert 'error' not in message, f"Should not return error: {message}"
    assert message['role'] == 'assistant', "Role should be assistant"
    print(f"✓ Created assistant message")


def test_get_message_by_id():
    """Test GET /api/messages/{id} returns specific message."""
    conv_id = get_or_create_conversation()
    created = api_request('POST', f"/api/conversations/{conv_id}/messages", {
        'role': 'user',
        'content': 'Get by ID test'
    })

    result = api_request('GET', f"/api/messages/{created['id']}")
    assert 'error' not in result, f"Should not return error: {result}"
    assert result['id'] == created['id'], "ID should match"
    assert result['content'] == 'Get by ID test', "Content should match"
    print(f"✓ Retrieved message by ID")


def test_update_message():
    """Test PUT /api/messages/{id} updates message content."""
    conv_id = get_or_create_conversation()
    created = api_request('POST', f"/api/conversations/{conv_id}/messages", {
        'role': 'user',
        'content': 'Original content'
    })

    updated = api_request('PUT', f"/api/messages/{created['id']}", {
        'content': 'Updated content'
    })
    assert 'error' not in updated, f"Should not return error: {updated}"
    assert updated['content'] == 'Updated content', "Content should be updated"
    print(f"✓ Updated message content")


def test_delete_message():
    """Test DELETE /api/messages/{id} removes message."""
    conv_id = get_or_create_conversation()
    created = api_request('POST', f"/api/conversations/{conv_id}/messages", {
        'role': 'user',
        'content': 'To be deleted'
    })

    result = api_request('DELETE', f"/api/messages/{created['id']}")
    assert 'error' not in result, f"Should not return error: {result}"

    # Verify it's gone
    result = api_request('GET', f"/api/messages/{created['id']}")
    assert 'error' in result, "Should return error for deleted message"
    print(f"✓ Deleted message")


def test_message_has_required_fields():
    """Test that messages have all required fields."""
    conv_id = get_or_create_conversation()
    message = api_request('POST', f"/api/conversations/{conv_id}/messages", {
        'role': 'user',
        'content': 'Field check test'
    })

    required_fields = ['id', 'conversationId', 'role', 'content', 'createdAt']
    for field in required_fields:
        # Handle both camelCase and snake_case
        assert field in message or field.lower() in message, f"Missing required field: {field}"
    print(f"✓ Message has all required fields")


def test_message_ordering():
    """Test that messages are returned in correct order."""
    conv_id = get_or_create_conversation()

    # Create multiple messages
    msg1 = api_request('POST', f"/api/conversations/{conv_id}/messages", {
        'role': 'user',
        'content': 'First'
    })
    msg2 = api_request('POST', f"/api/conversations/{conv_id}/messages", {
        'role': 'assistant',
        'content': 'Second'
    })

    messages = api_request('GET', f"/api/conversations/{conv_id}/messages")
    assert 'error' not in messages, f"Should not return error: {messages}"
    assert isinstance(messages, list), "Should return a list"
    # Messages should be ordered by createdAt
    if len(messages) >= 2:
        assert messages[0]['id'] == msg1['id'], "First message should be first"
        assert messages[-1]['id'] == msg2['id'], "Last message should be last"
    print(f"✓ Messages are properly ordered")


def test_message_conversation_association():
    """Test that messages are correctly associated with conversations."""
    conv_id = get_or_create_conversation()
    message = api_request('POST', f"/api/conversations/{conv_id}/messages", {
        'role': 'user',
        'content': 'Association test'
    })

    # Check conversationId field
    assert 'conversationId' in message or 'conversation_id' in message, \
        "Message should have conversationId"
    conv_id_field = message.get('conversationId') or message.get('conversation_id')
    assert conv_id_field == conv_id, "Should be associated with correct conversation"
    print(f"✓ Message correctly associated with conversation")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
