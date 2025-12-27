#!/usr/bin/env python3
"""Test project creation and management feature."""

import urllib.request
import json


def test_projects_feature():
    """Test the projects API end-to-end."""
    base_url = "http://localhost:8000/api"

    print("=" * 60)
    print("PROJECT CREATION AND MANAGEMENT TEST")
    print("=" * 60)

    # Step 1: List projects (should be empty or have our test project)
    print("\n1. Listing projects...")
    try:
        with urllib.request.urlopen(f"{base_url}/projects", timeout=5) as response:
            projects = json.loads(response.read().decode())
            print(f"   ✓ Found {len(projects)} existing project(s)")
    except Exception as e:
        print(f"   ✗ Failed to list projects: {e}")
        return False

    # Step 2: Create a new project
    print("\n2. Creating a new project...")
    project_data = {
        "name": "Test Project",
        "description": "A project for testing the feature",
        "color": "#10B981",
        "icon": "🚀",
        "custom_instructions": "Be helpful and concise"
    }

    req = urllib.request.Request(
        f"{base_url}/projects",
        data=json.dumps(project_data).encode('utf-8'),
        headers={'Content-Type': 'application/json'},
        method='POST'
    )

    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            new_project = json.loads(response.read().decode())
            print(f"   ✓ Created project:")
            print(f"     - ID: {new_project['id']}")
            print(f"     - Name: {new_project['name']}")
            print(f"     - Color: {new_project['color']}")
            print(f"     - Icon: {new_project['icon']}")
            project_id = new_project['id']
    except Exception as e:
        print(f"   ✗ Failed to create project: {e}")
        return False

    # Step 3: Get the project by ID
    print("\n3. Retrieving project by ID...")
    try:
        with urllib.request.urlopen(f"{base_url}/projects/{project_id}", timeout=5) as response:
            project = json.loads(response.read().decode())
            print(f"   ✓ Retrieved: {project['name']}")
            assert project['id'] == project_id
    except Exception as e:
        print(f"   ✗ Failed to retrieve project: {e}")
        return False

    # Step 4: Update the project
    print("\n4. Updating project...")
    update_data = {
        "name": "Updated Test Project",
        "description": "Updated description"
    }

    req = urllib.request.Request(
        f"{base_url}/projects/{project_id}",
        data=json.dumps(update_data).encode('utf-8'),
        headers={'Content-Type': 'application/json'},
        method='PUT'
    )

    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            updated = json.loads(response.read().decode())
            print(f"   ✓ Updated project name to: {updated['name']}")
            assert updated['name'] == "Updated Test Project"
    except Exception as e:
        print(f"   ✗ Failed to update project: {e}")
        return False

    # Step 5: List project conversations (should be empty)
    print("\n5. Listing project conversations...")
    try:
        with urllib.request.urlopen(f"{base_url}/projects/{project_id}/conversations", timeout=5) as response:
            convs = json.loads(response.read().decode())
            print(f"   ✓ Project has {len(convs)} conversation(s)")
    except Exception as e:
        print(f"   ✗ Failed to list conversations: {e}")
        return False

    # Step 6: List all projects again
    print("\n6. Listing all projects after update...")
    try:
        with urllib.request.urlopen(f"{base_url}/projects", timeout=5) as response:
            projects = json.loads(response.read().decode())
            print(f"   ✓ Total projects: {len(projects)}")
            for p in projects:
                print(f"     - {p['name']} ({p['id'][:8]}...)")
    except Exception as e:
        print(f"   ✗ Failed to list projects: {e}")
        return False

    print("\n" + "=" * 60)
    print("✓ ALL PROJECT TESTS PASSED")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = test_projects_feature()
    exit(0 if success else 1)
