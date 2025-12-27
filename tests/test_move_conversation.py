"""Test Feature #36: Move conversation between projects.

This test verifies:
1. User can create projects
2. User can create conversations in projects
3. User can move conversations between projects
4. Move operation updates project_id correctly
5. Conversation filtering works after move
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Conversation, Project


@pytest.mark.asyncio
async def test_move_conversation_endpoint(client: AsyncClient):
    """Test the move conversation endpoint."""
    print("Testing Move Conversation Endpoint...")

    # Create test projects
    project1_response = await client.post("/api/projects", json={
        "name": "Project Alpha",
        "description": "First test project",
        "color": "#FF0000"
    })
    assert project1_response.status_code == 201
    project1 = project1_response.json()

    project2_response = await client.post("/api/projects", json={
        "name": "Project Beta",
        "description": "Second test project",
        "color": "#00FF00"
    })
    assert project2_response.status_code == 201
    project2 = project2_response.json()

    print(f"✓ Created projects: {project1['name']} ({project1['id']}), {project2['name']} ({project2['id']})")

    # Create a test conversation in project1
    conv_response = await client.post("/api/conversations", json={
        "title": "Test Move Conversation",
        "model": "claude-sonnet-4-5-20250929",
        "project_id": project1['id']
    })
    assert conv_response.status_code == 201
    conv = conv_response.json()

    print(f"✓ Created conversation '{conv['title']}' in project '{project1['name']}'")

    # Verify initial state
    assert conv['project_id'] == project1['id'], f"Conversation should be in {project1['name']}"
    print(f"✓ Verified initial state: conversation in {project1['name']}")

    # Test move to project2
    move_response = await client.post(f"/api/conversations/{conv['id']}/move", json={
        "project_id": project2['id']
    })
    assert move_response.status_code == 200
    moved_conv = move_response.json()

    print(f"✓ Moved conversation to project '{project2['name']}'")

    # Verify move
    assert moved_conv['project_id'] == project2['id'], f"Conversation should now be in {project2['name']}"
    print(f"✓ Verified move: conversation now in {project2['name']}")

    # Test move to no project (remove from project)
    move_to_none_response = await client.post(f"/api/conversations/{conv['id']}/move", json={
        "project_id": None
    })
    assert move_to_none_response.status_code == 200
    moved_to_none_conv = move_to_none_response.json()

    print(f"✓ Moved conversation to no project")

    # Verify removal from project
    assert moved_to_none_conv['project_id'] is None, "Conversation should not be in any project"
    print(f"✓ Verified removal: conversation not in any project")

    # Test filtering by project
    # Create another conversation in project1
    conv2_response = await client.post("/api/conversations", json={
        "title": "Another Conversation",
        "model": "claude-sonnet-4-5-20250929",
        "project_id": project1['id']
    })
    assert conv2_response.status_code == 201
    conv2 = conv2_response.json()

    # Get conversations for project1
    project1_convs_response = await client.get(f"/api/projects/{project1['id']}/conversations")
    assert project1_convs_response.status_code == 200
    project1_conversations = project1_convs_response.json()

    assert len(project1_conversations) == 1, "Project1 should have 1 conversation"
    assert project1_conversations[0]['id'] == conv2['id'], "Only conv2 should be in project1"
    print(f"✓ Verified project filtering: {project1['name']} has {len(project1_conversations)} conversation(s)")

    # Get conversations for project2
    project2_convs_response = await client.get(f"/api/projects/{project2['id']}/conversations")
    assert project2_convs_response.status_code == 200
    project2_conversations = project2_convs_response.json()

    assert len(project2_conversations) == 0, "Project2 should have 0 conversations"
    print(f"✓ Verified project filtering: {project2['name']} has {len(project2_conversations)} conversation(s)")

    # Get conversations with no project
    all_convs_response = await client.get("/api/conversations")
    assert all_convs_response.status_code == 200
    all_conversations = all_convs_response.json()

    no_project_conversations = [c for c in all_conversations if c['project_id'] is None]
    assert len(no_project_conversations) == 1, "No project should have 1 conversation (only conv)"
    print(f"✓ Verified project filtering: no project has {len(no_project_conversations)} conversation(s)")

    print("\n✅ Move conversation endpoint test PASSED")


def test_move_conversation_manual():
    """Print manual testing instructions."""
    print("\n" + "="*60)
    print("FEATURE #36: MOVE CONVERSATION BETWEEN PROJECTS")
    print("="*60)
    print("\nManual Testing Steps:")
    print("1. Open http://localhost:5173 in browser")
    print("2. Create two projects (Project A, Project B)")
    print("3. Create a conversation in Project A")
    print("4. Open the conversation menu (hover over conversation)")
    print("5. Click the 📁 Move to Project button")
    print("6. Select Project B from the dropdown")
    print("7. Verify the conversation disappears from Project A view")
    print("8. Switch to Project B")
    print("9. Verify the conversation appears in Project B")

    print("\nExpected behavior:")
    print("- 📁 button opens a modal with project selection")
    print("- Dropdown shows all projects + 'No Project' option")
    print("- Selecting a project moves the conversation immediately")
    print("- Conversation disappears from old project view")
    print("- Conversation appears in new project view")
    print("- If current conversation is moved and not visible, navigate away")
    print("- Backend API updates project_id in database")

    print("\nAPI Endpoints:")
    print("- POST /api/conversations/{id}/move - Move conversation")
    print("- GET /api/conversations?project_id=xxx - Filter by project")
    print("- GET /api/projects/{id}/conversations - List project conversations")