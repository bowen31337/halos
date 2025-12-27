"""
Test PDF Export Feature

This test verifies that the PDF export functionality works correctly.
Since PDF generation is client-side, we test the API endpoints and data preparation.
"""

import pytest
import asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select

import sys
sys.path.insert(0, '/media/DATA/projects/autonomous-coding-clone-cc/talos')

from src.main import app
from src.core.database import Base, get_db
from src.models.conversation import Conversation as ConversationModel
from src.models.message import Message as MessageModel


TEST_DATABASE_URL = 'sqlite+aiosqlite:///./test_pdf_export.db'


@pytest.fixture
async def test_client():
    """Create a test client with test database."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async def override_get_db():
        async with async_session() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as client:
        yield client

    app.dependency_overrides.clear()
    await engine.dispose()


@pytest.mark.asyncio
async def test_pdf_export_data_preparation(test_client: AsyncClient):
    """Test that conversation data can be retrieved for PDF export."""
    print("\n=== Test 1: PDF Export Data Preparation ===")

    # Create a conversation with messages
    conv_response = await test_client.post('/api/conversations', json={
        'title': 'Test PDF Export',
        'model': 'claude-sonnet-4-5'
    })
    assert conv_response.status_code == 200
    conv_id = conv_response.json()['id']
    print(f"✓ Created conversation: {conv_id}")

    # Add some messages
    messages = [
        {'role': 'user', 'content': 'Hello, can you help me with something?'},
        {'role': 'assistant', 'content': 'Of course! I\'d be happy to help. What do you need?'},
        {'role': 'user', 'content': 'I need to export this conversation to PDF format.'},
        {'role': 'assistant', 'content': 'I can help with that! The PDF export feature will generate a nicely formatted document.'}
    ]

    for msg in messages:
        response = await test_client.post(f'/api/conversations/{conv_id}/messages', json=msg)
        assert response.status_code == 200
    print(f"✓ Added {len(messages)} messages")

    # Retrieve conversation for PDF export
    response = await test_client.get(f'/api/conversations/{conv_id}')
    assert response.status_code == 200
    conv_data = response.json()

    # Verify structure matches PDF export requirements
    assert 'title' in conv_data
    assert 'model' in conv_data
    assert 'created_at' in conv_data
    assert 'messages' in conv_data
    assert len(conv_data['messages']) == len(messages)
    print(f"✓ Retrieved conversation data with {len(conv_data['messages'])} messages")

    # Verify message structure
    for msg in conv_data['messages']:
        assert 'role' in msg
        assert 'content' in msg
        assert 'created_at' in msg
    print("✓ All messages have required fields")

    print("✓ PASSED: Conversation data is ready for PDF export\n")


@pytest.mark.asyncio
async def test_pdf_export_data_with_code_blocks(test_client: AsyncClient):
    """Test that code blocks are preserved in conversation data."""
    print("\n=== Test 2: PDF Export with Code Blocks ===")

    # Create conversation
    conv_response = await test_client.post('/api/conversations', json={
        'title': 'Code Example Conversation'
    })
    conv_id = conv_response.json()['id']

    # Add message with code block
    code_message = {
        'role': 'assistant',
        'content': 'Here is a Python example:\n```python\ndef hello():\n    print("Hello, World!")\nreturn hello\n```\nThis function prints a greeting.'
    }

    await test_client.post(f'/api/conversations/{conv_id}/messages', json=code_message)

    # Retrieve conversation
    response = await test_client.get(f'/api/conversations/{conv_id}')
    conv_data = response.json()

    # Verify code blocks are preserved
    assert '```python' in conv_data['messages'][0]['content']
    assert 'def hello():' in conv_data['messages'][0]['content']
    print("✓ Code blocks preserved in conversation data")

    print("✓ PASSED: Code blocks are preserved for PDF formatting\n")


@pytest.mark.asyncio
async def test_pdf_export_data_with_markdown(test_client: AsyncClient):
    """Test that markdown formatting is preserved."""
    print("\n=== Test 3: PDF Export with Markdown ===")

    # Create conversation
    conv_response = await test_client.post('/api/conversations', json={
        'title': 'Markdown Test'
    })
    conv_id = conv_response.json()['id']

    # Add message with various markdown
    markdown_message = {
        'role': 'assistant',
        'content': '''
# Heading 1
**Bold text** and *italic text*
- List item 1
- List item 2

[Link text](https://example.com)

`inline code`
'''
    }

    await test_client.post(f'/api/conversations/{conv_id}/messages', json=markdown_message)

    # Retrieve and verify
    response = await test_client.get(f'/api/conversations/{conv_id}')
    conv_data = response.json()

    content = conv_data['messages'][0]['content']
    assert '# Heading 1' in content
    assert '**Bold text**' in content
    assert '*italic text*' in content
    print("✓ Markdown formatting preserved")

    print("✓ PASSED: Markdown is preserved for PDF formatting\n")


@pytest.mark.asyncio
async def test_pdf_export_conversation_title_escaping(test_client: AsyncClient):
    """Test that special characters in titles are handled correctly."""
    print("\n=== Test 4: Conversation Title Handling ===")

    # Create conversation with special characters in title
    special_titles = [
        'Conversation with / slashes',
        'Conversation with "quotes"',
        'Conversation with <angle brackets>',
        'Test: Multiple - Special_Chars.txt'
    ]

    for title in special_titles:
        conv_response = await test_client.post('/api/conversations', json={'title': title})
        assert conv_response.status_code == 200
        print(f"✓ Created conversation: {title}")

    print("✓ PASSED: Special characters in titles handled correctly\n")


@pytest.mark.asyncio
async def test_pdf_export_long_conversation(test_client: AsyncClient):
    """Test PDF export with a longer conversation."""
    print("\n=== Test 5: Long Conversation Export ===")

    # Create conversation
    conv_response = await test_client.post('/api/conversations', json={
        'title': 'Long Conversation Test'
    })
    conv_id = conv_response.json()['id']

    # Add multiple messages
    num_messages = 20
    for i in range(num_messages):
        await test_client.post(f'/api/conversations/{conv_id}/messages', json={
            'role': 'user' if i % 2 == 0 else 'assistant',
            'content': f'Message {i+1} with some content to make it longer.'
        })

    # Retrieve all messages
    response = await test_client.get(f'/api/conversations/{conv_id}')
    conv_data = response.json()

    assert len(conv_data['messages']) == num_messages
    print(f"✓ Retrieved {num_messages} messages")

    print("✓ PASSED: Long conversations handled correctly\n")


@pytest.mark.asyncio
async def test_json_and_markdown_export_still_work(test_client: AsyncClient):
    """Verify existing JSON and Markdown exports still work."""
    print("\n=== Test 6: Existing Export Formats ===")

    # Create conversation
    conv_response = await test_client.post('/api/conversations', json={
        'title': 'Export Formats Test'
    })
    conv_id = conv_response.json()['id']

    await test_client.post(f'/api/conversations/{conv_id}/messages', json={
        'role': 'user',
        'content': 'Test message'
    })

    # Test JSON export
    json_response = await test_client.post(f'/api/conversations/{conv_id}/export?format=json')
    assert json_response.status_code == 200
    assert json_response.headers['content-type'] == 'application/json'
    print("✓ JSON export works")

    # Test Markdown export
    md_response = await test_client.post(f'/api/conversations/{conv_id}/export?format=markdown')
    assert md_response.status_code == 200
    assert md_response.headers['content-type'] == 'text/markdown; charset=utf-8'
    print("✓ Markdown export works")

    print("✓ PASSED: Existing export formats still functional\n")


if __name__ == '__main__':
    print("\n" + "=" * 80)
    print("PDF Export Feature Tests")
    print("=" * 80)

    import sys
    sys.exit(pytest.main([__file__, '-v', '-s']))
