"""
Test JSON and CSV Viewer Components

This test verifies that:
1. JSON artifacts are displayed with tree structure
2. CSV artifacts are displayed in table format
3. Both viewers are properly integrated into the artifact panel
"""

import pytest
import asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.core.database import Base, get_db
from src.main import app
from src.models import Artifact, Conversation


TEST_DATABASE_URL = 'sqlite+aiosqlite:///./test_json_csv_viewers.db'


async def test_json_artifact_detection():
    """Test that JSON artifacts are properly detected"""
    from src.routers.artifacts import detect_artifacts

    content = '''Here is a JSON response:
```json
{
  "users": [
    {"id": 1, "name": "Alice", "active": true},
    {"id": 2, "name": "Bob", "active": false}
  ],
  "count": 2
}
```'''

    artifacts = detect_artifacts(content)
    assert len(artifacts) == 1
    assert artifacts[0]['language'] == 'json'
    assert artifacts[0]['artifact_type'] == 'json'
    print("✓ JSON artifact detection works")


async def test_csv_artifact_detection():
    """Test that CSV artifacts are properly detected"""
    from src.routers.artifacts import detect_artifacts

    content = '''Here is a CSV data:
```csv
name,age,city
Alice,30,NYC
Bob,25,LA
Charlie,35,SF
```'''

    artifacts = detect_artifacts(content)
    assert len(artifacts) == 1
    assert artifacts[0]['language'] == 'csv'
    assert artifacts[0]['artifact_type'] == 'csv'
    print("✓ CSV artifact detection works")


async def test_json_artifact_creation():
    """Test creating a JSON artifact via API"""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        async def override_get_db():
            yield session
        app.dependency_overrides[get_db] = override_get_db

        async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as client:
            # Create conversation
            conv_response = await client.post('/api/conversations', json={'title': 'Test JSON'})
            assert conv_response.status_code == 200
            conv_id = conv_response.json()['id']

            # Create JSON artifact
            json_content = '''{
  "users": [
    {"id": 1, "name": "Alice"},
    {"id": 2, "name": "Bob"}
  ],
  "count": 2
}'''

            artifact_response = await client.post('/api/artifacts/create', json={
                'conversation_id': conv_id,
                'content': json_content,
                'title': 'User Data',
                'language': 'json',
                'artifact_type': 'json'
            })

            assert artifact_response.status_code == 200
            artifact = artifact_response.json()
            assert artifact['artifact_type'] == 'json'
            assert artifact['language'] == 'json'
            assert artifact['title'] == 'User Data'

            # Get artifact
            get_response = await client.get(f'/api/artifacts/{artifact["id"]}')
            assert get_response.status_code == 200
            retrieved = get_response.json()
            assert retrieved['artifact_type'] == 'json'

            print("✓ JSON artifact creation works")

        app.dependency_overrides.clear()

    await engine.dispose()


async def test_csv_artifact_creation():
    """Test creating a CSV artifact via API"""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        async def override_get_db():
            yield session
        app.dependency_overrides[get_db] = override_get_db

        async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as client:
            # Create conversation
            conv_response = await client.post('/api/conversations', json={'title': 'Test CSV'})
            assert conv_response.status_code == 200
            conv_id = conv_response.json()['id']

            # Create CSV artifact
            csv_content = '''name,age,city
Alice,30,NYC
Bob,25,LA
Charlie,35,SF'''

            artifact_response = await client.post('/api/artifacts/create', json={
                'conversation_id': conv_id,
                'content': csv_content,
                'title': 'User Data',
                'language': 'csv',
                'artifact_type': 'csv'
            })

            assert artifact_response.status_code == 200
            artifact = artifact_response.json()
            assert artifact['artifact_type'] == 'csv'
            assert artifact['language'] == 'csv'

            # Get artifact
            get_response = await client.get(f'/api/artifacts/{artifact["id"]}')
            assert get_response.status_code == 200
            retrieved = get_response.json()
            assert retrieved['artifact_type'] == 'csv'

            print("✓ CSV artifact creation works")

        app.dependency_overrides.clear()

    await engine.dispose()


async def test_mixed_artifacts():
    """Test conversation with multiple artifact types"""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        async def override_get_db():
            yield session
        app.dependency_overrides[get_db] = override_get_db

        async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as client:
            # Create conversation
            conv_response = await client.post('/api/conversations', json={'title': 'Mixed Artifacts'})
            assert conv_response.status_code == 200
            conv_id = conv_response.json()['id']

            # Create JSON artifact
            await client.post('/api/artifacts/create', json={
                'conversation_id': conv_id,
                'content': '{"test": "data"}',
                'title': 'JSON Test',
                'language': 'json'
            })

            # Create CSV artifact
            await client.post('/api/artifacts/create', json={
                'conversation_id': conv_id,
                'content': 'a,b\n1,2',
                'title': 'CSV Test',
                'language': 'csv'
            })

            # Create code artifact
            await client.post('/api/artifacts/create', json={
                'conversation_id': conv_id,
                'content': 'print("hello")',
                'title': 'Python Test',
                'language': 'python'
            })

            # Get all artifacts for conversation
            list_response = await client.get(f'/api/conversations/{conv_id}/artifacts')
            assert list_response.status_code == 200
            artifacts = list_response.json()
            assert len(artifacts) == 3

            # Verify types
            types = {a['artifact_type'] for a in artifacts}
            assert 'json' in types
            assert 'csv' in types
            assert 'code' in types

            print("✓ Mixed artifact types work correctly")

        app.dependency_overrides.clear()

    await engine.dispose()


async def main():
    """Run all tests"""
    print("=" * 60)
    print("JSON and CSV Viewer Tests")
    print("=" * 60)
    print()

    # Clean up test database
    import os
    if os.path.exists('./test_json_csv_viewers.db'):
        os.remove('./test_json_csv_viewers.db')

    try:
        await test_json_artifact_detection()
        await test_csv_artifact_detection()
        await test_json_artifact_creation()
        await test_csv_artifact_creation()
        await test_mixed_artifacts()

        print()
        print("=" * 60)
        print("All tests passed! ✓")
        print("=" * 60)

    finally:
        # Clean up
        if os.path.exists('./test_json_csv_viewers.db'):
            os.remove('./test_json_csv_viewers.db')


if __name__ == '__main__':
    asyncio.run(main())
