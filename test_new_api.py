#!/usr/bin/env python3
import requests
import json

def test_project_files_api():
    """Test project files API functionality"""
    base_url = "http://localhost:8005"

    print("Testing Project Files API on port 8005...")

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

                if response.status_code == 200:
                    files = response.json()
                    print(f"✓ Project has {len(files)} files")

                    # Test upload file
                    test_content = b"Test document content for project knowledge base"
                    files = {'file': ('test.txt', test_content, 'text/plain')}

                    response = requests.post(
                        f"{base_url}/api/projects/{project_id}/files",
                        files=files
                    )
                    print(f"Upload file status: {response.status_code}")

                    if response.status_code == 201:
                        uploaded_file = response.json()
                        print(f"✓ Successfully uploaded file: {uploaded_file['original_filename']}")
                        print(f"  File URL: {uploaded_file['file_url']}")

                        # Test download
                        download_response = requests.get(uploaded_file['file_url'])
                        if download_response.status_code == 200:
                            if download_response.content == test_content:
                                print("✓ File download successful and content matches")
                            else:
                                print("✗ File download content mismatch")
                        else:
                            print(f"✗ File download failed: {download_response.status_code}")

                        # Test delete
                        file_id = uploaded_file['id']
                        response = requests.delete(f"{base_url}/api/projects/{project_id}/files/{file_id}")
                        if response.status_code == 204:
                            print("✓ File deletion successful")
                        else:
                            print(f"✗ File deletion failed: {response.status_code}")
                    else:
                        print(f"✗ Upload failed: {response.status_code}")
                        print(f"Response: {response.text}")
                else:
                    print(f"✗ List files failed: {response.status_code}")
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