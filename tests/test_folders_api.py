"""Test Feature #94: Folders API organizes conversations hierarchically.

This test verifies that the /api/folders endpoints properly create, manage,
and organize conversations in hierarchical folders.
"""

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from src.core.database import Base, get_db
from src.main import app
from src.models import Conversation


TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_folders.db"


@pytest.fixture
async def db_session():
    """Create a test database session."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        yield session

    await engine.dispose()


@pytest.fixture
async def client(db_session):
    """Create a test client with database dependency override."""
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_folders_api_workflow():
    """Test complete folders API workflow.

    Feature #94 Steps:
    1. POST to /api/folders to create folder
    2. Verify folder created
    3. POST to /api/folders/:id/items to add conversation
    4. Verify conversation associated with folder
    5. GET /api/folders to list all folders
    6. DELETE /api/folders/:id/items/:conversationId
    7. Verify conversation removed from folder
    8. DELETE /api/folders/:id
    9. Verify folder deleted
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # First, create a conversation to use for testing
        print("\n=== Setup: Create a test conversation ===")
        conv_response = await client.post(
            "/api/conversations",
            json={"title": "Test Conversation", "model": "claude-sonnet-4-5-20250929"}
        )
        assert conv_response.status_code == 201
        conversation = conv_response.json()
        conversation_id = conversation["id"]
        print(f"  ✓ Created conversation: {conversation_id}")

        # Step 1: POST to /api/folders to create folder
        print("\n=== Step 1: POST to /api/folders to create folder ===")
        folder_data = {
            "name": "My Project Folder",
            "description": "A test folder for organizing conversations"
        }
        response = await client.post("/api/folders", json=folder_data)
        assert response.status_code == 201
        folder = response.json()
        folder_id = folder["id"]
        print(f"  ✓ Folder created with ID: {folder_id}")
        print(f"    Response: {folder}")

        # Step 2: Verify folder created
        print("\n=== Step 2: Verify folder created ===")
        get_response = await client.get(f"/api/folders/{folder_id}")
        assert get_response.status_code == 200
        retrieved_folder = get_response.json()
        assert retrieved_folder["id"] == folder_id
        assert retrieved_folder["name"] == "My Project Folder"
        assert retrieved_folder["description"] == "A test folder for organizing conversations"
        print(f"  ✓ Folder verified: {retrieved_folder['name']}")

        # Step 3: POST to /api/folders/:id/items to add conversation
        print("\n=== Step 3: POST to /api/folders/:id/items to add conversation ===")
        item_data = {"conversation_id": conversation_id}
        response = await client.post(f"/api/folders/{folder_id}/items", json=item_data)
        assert response.status_code == 200
        folder_item = response.json()
        print(f"  ✓ Conversation added to folder")
        print(f"    Item: {folder_item}")

        # Step 4: Verify conversation associated with folder
        print("\n=== Step 4: Verify conversation associated with folder ===")
        items_response = await client.get(f"/api/folders/{folder_id}/items")
        assert items_response.status_code == 200
        items = items_response.json()
        assert len(items) == 1
        assert items[0]["conversation_id"] == conversation_id
        assert items[0]["folder_id"] == folder_id
        print(f"  ✓ Conversation found in folder")
        print(f"    Conversation: {items[0]['conversation']['title']}")

        # Step 5: GET /api/folders to list all folders
        print("\n=== Step 5: GET /api/folders to list all folders ===")
        list_response = await client.get("/api/folders")
        assert list_response.status_code == 200
        folders = list_response.json()
        assert len(folders) >= 1
        assert any(f["id"] == folder_id for f in folders)
        print(f"  ✓ Found {len(folders)} folder(s)")
        for f in folders:
            print(f"    - {f['name']} (ID: {f['id']})")

        # Step 6: DELETE /api/folders/:id/items/:conversationId
        print("\n=== Step 6: DELETE /api/folders/:id/items/:conversationId ===")
        delete_item_response = await client.delete(f"/api/folders/{folder_id}/items/{conversation_id}")
        assert delete_item_response.status_code == 204
        print(f"  ✓ Conversation removed from folder")

        # Step 7: Verify conversation removed from folder
        print("\n=== Step 7: Verify conversation removed from folder ===")
        items_after_delete = await client.get(f"/api/folders/{folder_id}/items")
        assert items_after_delete.status_code == 200
        assert len(items_after_delete.json()) == 0
        print(f"  ✓ Folder is now empty")

        # Step 8: DELETE /api/folders/:id
        print("\n=== Step 8: DELETE /api/folders/:id ===")
        delete_folder_response = await client.delete(f"/api/folders/{folder_id}")
        assert delete_folder_response.status_code == 204
        print(f"  ✓ Folder deleted")

        # Step 9: Verify folder deleted
        print("\n=== Step 9: Verify folder deleted ===")
        get_deleted_response = await client.get(f"/api/folders/{folder_id}")
        assert get_deleted_response.status_code == 404
        print(f"  ✓ Folder no longer exists (404 as expected)")

        print("\n" + "=" * 60)
        print("Feature #94 Test Summary:")
        print("=" * 60)
        print("✅ All 9 steps passed successfully!")
        print("✅ Folders API organizes conversations hierarchically")
        print("=" * 60)


@pytest.mark.asyncio
async def test_folders_hierarchical_structure():
    """Test that folders can have parent-child relationships."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        print("\n=== Testing Hierarchical Folders ===")

        # Create parent folder
        parent_response = await client.post("/api/folders", json={
            "name": "Parent Folder",
            "description": "Top level folder"
        })
        parent_id = parent_response.json()["id"]
        print(f"  ✓ Created parent folder: {parent_id}")

        # Create child folder
        child_response = await client.post("/api/folders", json={
            "name": "Child Folder",
            "description": "Nested folder",
            "parent_folder_id": parent_id
        })
        child_id = child_response.json()["id"]
        print(f"  ✓ Created child folder: {child_id}")

        # Get parent folder's children
        children_response = await client.get(f"/api/folders?parent_folder_id={parent_id}")
        children = children_response.json()
        assert len(children) == 1
        assert children[0]["id"] == child_id
        print(f"  ✓ Child folder correctly associated with parent")

        # Cleanup
        await client.delete(f"/api/folders/{child_id}")
        await client.delete(f"/api/folders/{parent_id}")
        print(f"  ✓ Cleanup complete")

        print("✅ Hierarchical structure test passed!")


if __name__ == "__main__":
    import sys
    pytest.main([__file__, "-v", "-s"] + sys.argv[1:])
