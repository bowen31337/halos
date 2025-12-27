#!/usr/bin/env python3
import requests
import json

def test_project_files_api():
    """Test project files API functionality"""
    base_url = "http://localhost:8000"

    print("Testing Project Files API...")

    # Test 1: Get projects
    try:
        response = requests.get(f"{base_url}/api/projects")
        if response.status_code == 200:
            projects = response.json()
            print(f"✓ Found {len(projects)} projects")

            if projects:
                project_id = projects[0]['id']
                print(f"✓ Using project ID: {project_id}")

                # Test 2: Check if project files routes are registered
                print("Testing project files routes...")

                # Test list files
                response = requests.get(f"{base_url}/api/projects/{project_id}/files")
                print(f"List files status: {response.status_code}")

                # Test upload file
                test_content = b"Test document content for project knowledge base"
                files = {'file': ('test.txt', test_content, 'text/plain')}

                response = requests.post(
                    f"{base_url}/api/projects/{project_id}/files",
                    files=files
                )
                print(f"Upload file status: {response.status_code}")

                if response.status_code == 201:
                    print("✓ Project files API is working!")
                else:
                    print(f"✗ Upload failed: {response.status_code}")
                    print(f"Response: {response.text}")
            else:
                print("No projects found")
        else:
            print(f"✗ Failed to get projects: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("✗ Cannot connect to server")
    except Exception as e:
        print(f"✗ Error: {e}")

    print("\nProject Files API Test Complete!")

if __name__ == "__main__":
    test_project_files_api()