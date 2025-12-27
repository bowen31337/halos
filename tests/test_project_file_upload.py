#!/usr/bin/env python3
"""Test project file upload feature (Feature #38).

This test verifies that users can upload files to a project's knowledge base
and that the files are properly stored and accessible.
"""

import io
import json
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import Base, get_db
from src.main import app
from src.models.project import Project
from src.models.project_file import ProjectFile
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select


# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_project_files.db"


@pytest_asyncio.fixture(scope="function")
async def test_db_and_engine():
    """Create a fresh database for each test."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        yield session, engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def client(test_db_and_engine):
    """Create an async HTTP client for testing."""
    test_db, engine = test_db_and_engine

    async def override_get_db():
        yield test_db

    app.dependency_overrides[get_db] = override_get_db

    from httpx import ASGITransport
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def test_project(client: AsyncClient):
    """Create a test project for file upload tests."""
    project_data = {
        "name": "Test Project for Files",
        "description": "Testing file upload functionality",
        "color": "#10B981",
        "icon": "📁",
        "custom_instructions": "Be helpful"
    }

    response = await client.post("/api/projects", json=project_data)
    assert response.status_code == 201
    return response.json()


@pytest.mark.asyncio
async def test_upload_file_to_project(client: AsyncClient, test_project):
    """Test uploading a file to a project's knowledge base."""
    print("\n" + "=" * 60)
    print("TEST: Upload file to project knowledge base")
    print("=" * 60)

    project_id = test_project["id"]

    # Step 1: Verify project exists
    print("\n1. Verifying project exists...")
    response = await client.get(f"/api/projects/{project_id}")
    assert response.status_code == 200
    print(f"   ✓ Project found: {test_project['name']}")

    # Step 2: Upload a test file
    print("\n2. Uploading test file...")
    test_content = b"This is a test document. It contains important information about the project."
    files = {
        "file": ("test_document.txt", io.BytesIO(test_content), "text/plain")
    }

    response = await client.post(
        f"/api/projects/{project_id}/files",
        files=files
    )
    assert response.status_code == 201
    uploaded_file = response.json()
    print(f"   ✓ File uploaded successfully")
    print(f"     - ID: {uploaded_file['id']}")
    print(f"     - Filename: {uploaded_file['filename']}")
    print(f"     - Original: {uploaded_file['original_filename']}")
    print(f"     - Size: {uploaded_file['file_size']} bytes")
    print(f"     - URL: {uploaded_file['file_url']}")

    # Step 3: List project files
    print("\n3. Listing project files...")
    response = await client.get(f"/api/projects/{project_id}/files")
    assert response.status_code == 200
    files_list = response.json()
    assert len(files_list) == 1
    print(f"   ✓ Found {len(files_list)} file(s) in project")

    # Step 4: Download the file
    print("\n4. Downloading file...")
    response = await client.get(f"/api/projects/{project_id}/files/{uploaded_file['filename']}")
    assert response.status_code == 200
    downloaded_content = response.content
    assert downloaded_content == test_content
    print(f"   ✓ File downloaded correctly")

    # Step 5: Check file content in list response
    print("\n5. Checking file content in list...")
    response = await client.get(f"/api/projects/{project_id}/files")
    files_list = response.json()
    assert files_list[0]['content'] == test_content.decode('utf-8')
    print(f"   ✓ Content available in file list")

    print("\n" + "=" * 60)
    print("✓ ALL FILE UPLOAD TESTS PASSED")
    print("=" * 60)


@pytest.mark.asyncio
async def test_upload_multiple_files(client: AsyncClient, test_project):
    """Test uploading multiple files to a project."""
    print("\n" + "=" * 60)
    print("TEST: Upload multiple files")
    print("=" * 60)

    project_id = test_project["id"]

    # Upload multiple files
    test_files = [
        ("doc1.txt", b"First document content", "text/plain"),
        ("doc2.txt", b"Second document content", "text/plain"),
        ("doc3.txt", b"Third document content", "text/plain"),
    ]

    print("\n1. Uploading 3 files...")
    for filename, content, mime_type in test_files:
        files = {"file": (filename, io.BytesIO(content), mime_type)}
        response = await client.post(f"/api/projects/{project_id}/files", files=files)
        assert response.status_code == 201
        print(f"   ✓ Uploaded: {filename}")

    # Verify all files are listed
    print("\n2. Verifying all files are listed...")
    response = await client.get(f"/api/projects/{project_id}/files")
    assert response.status_code == 200
    files_list = response.json()
    assert len(files_list) == 3
    print(f"   ✓ Found {len(files_list)} files")

    print("\n" + "=" * 60)
    print("✓ MULTIPLE FILE UPLOAD TEST PASSED")
    print("=" * 60)


@pytest.mark.asyncio
async def test_upload_file_to_nonexistent_project(client: AsyncClient):
    """Test uploading file to a project that doesn't exist."""
    print("\n" + "=" * 60)
    print("TEST: Upload to nonexistent project")
    print("=" * 60)

    print("\n1. Attempting upload to nonexistent project...")
    files = {"file": ("test.txt", io.BytesIO(b"content"), "text/plain")}
    response = await client.post("/api/projects/nonexistent-id/files", files=files)

    assert response.status_code == 404
    print(f"   ✓ Correctly returned 404: {response.json()['detail']}")

    print("\n" + "=" * 60)
    print("✓ NONEXISTENT PROJECT TEST PASSED")
    print("=" * 60)


@pytest.mark.asyncio
async def test_delete_project_file(client: AsyncClient, test_project):
    """Test deleting a file from a project."""
    print("\n" + "=" * 60)
    print("TEST: Delete project file")
    print("=" * 60)

    project_id = test_project["id"]

    # Upload a file first
    print("\n1. Uploading file to delete...")
    files = {"file": ("delete_me.txt", io.BytesIO(b"Delete this"), "text/plain")}
    response = await client.post(f"/api/projects/{project_id}/files", files=files)
    assert response.status_code == 201
    file_id = response.json()["id"]
    print(f"   ✓ File uploaded: {file_id}")

    # Delete the file
    print("\n2. Deleting file...")
    response = await client.delete(f"/api/projects/{project_id}/files/{file_id}")
    assert response.status_code == 204
    print(f"   ✓ File deleted")

    # Verify file is no longer in list
    print("\n3. Verifying file is removed from list...")
    response = await client.get(f"/api/projects/{project_id}/files")
    assert response.status_code == 200
    files_list = response.json()
    assert len(files_list) == 0
    print(f"   ✓ File list is empty")

    print("\n" + "=" * 60)
    print("✓ DELETE FILE TEST PASSED")
    print("=" * 60)


@pytest.mark.asyncio
async def test_upload_pdf_file(client: AsyncClient, test_project):
    """Test uploading a PDF file (with content extraction if available)."""
    print("\n" + "=" * 60)
    print("TEST: Upload PDF file")
    print("=" * 60)

    project_id = test_project["id"]

    # Create a minimal PDF (just header, no actual content for simplicity)
    # In real scenario, pdftotext would extract text if installed
    pdf_header = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n/Contents 4 0 R\n>>\nendobj\n4 0 obj\n<<\n/Length 44\n>>\nstream\nBT\n/F1 12 Tf\n100 700 Td\n(Test PDF) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000204 00000 n \ntrailer\n<<\n/Size 5\n/Root 1 0 R\n>>\nstartxref\n306\n%%EOF"

    print("\n1. Uploading PDF file...")
    files = {"file": ("test.pdf", io.BytesIO(pdf_header), "application/pdf")}
    response = await client.post(f"/api/projects/{project_id}/files", files=files)
    assert response.status_code == 201
    uploaded_file = response.json()
    print(f"   ✓ PDF uploaded: {uploaded_file['original_filename']}")
    print(f"     - Content type: {uploaded_file['content_type']}")

    print("\n" + "=" * 60)
    print("✓ PDF UPLOAD TEST PASSED")
    print("=" * 60)


@pytest.mark.asyncio
async def test_project_files_isolation(client: AsyncClient):
    """Test that files are isolated between different projects."""
    print("\n" + "=" * 60)
    print("TEST: Project file isolation")
    print("=" * 60)

    # Create two projects
    print("\n1. Creating two projects...")
    project1 = (await client.post("/api/projects", json={
        "name": "Project A",
        "description": "First project"
    })).json()

    project2 = (await client.post("/api/projects", json={
        "name": "Project B",
        "description": "Second project"
    })).json()
    print(f"   ✓ Created: {project1['name']} and {project2['name']}")

    # Upload files to each project
    print("\n2. Uploading files to each project...")
    files1 = {"file": ("file1.txt", io.BytesIO(b"Project A content"), "text/plain")}
    files2 = {"file": ("file2.txt", io.BytesIO(b"Project B content"), "text/plain")}

    await client.post(f"/api/projects/{project1['id']}/files", files=files1)
    await client.post(f"/api/projects/{project2['id']}/files", files=files2)
    print(f"   ✓ Files uploaded to respective projects")

    # Verify isolation
    print("\n3. Verifying file isolation...")
    response1 = await client.get(f"/api/projects/{project1['id']}/files")
    response2 = await client.get(f"/api/projects/{project2['id']}/files")

    files1_list = response1.json()
    files2_list = response2.json()

    assert len(files1_list) == 1
    assert len(files2_list) == 1
    assert files1_list[0]["original_filename"] == "file1.txt"
    assert files2_list[0]["original_filename"] == "file2.txt"
    print(f"   ✓ Each project has only its own files")

    print("\n" + "=" * 60)
    print("✓ PROJECT ISOLATION TEST PASSED")
    print("=" * 60)


if __name__ == "__main__":
    import asyncio

    async def run_all_tests():
        """Run all tests sequentially."""
        print("\n" + "=" * 70)
        print("  FEATURE #38: Upload files to project knowledge base")
        print("=" * 70)

        # Setup
        from httpx import ASGITransport

        engine = create_async_engine(TEST_DATABASE_URL, echo=False)
        async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        async with async_session() as session:
            # Override get_db
            async def override_get_db():
                yield session

            app.dependency_overrides[get_db] = override_get_db

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                # Create test project
                project_data = {
                    "name": "Test Project",
                    "description": "For file upload tests",
                    "color": "#10B981",
                    "icon": "📁"
                }
                response = await client.post("/api/projects", json=project_data)
                test_project = response.json()

                # Run tests
                await test_upload_file_to_project(client, test_project)
                await test_upload_multiple_files(client, test_project)
                await test_upload_file_to_nonexistent_project(client)
                await test_delete_project_file(client, test_project)
                await test_upload_pdf_file(client, test_project)
                await test_project_files_isolation(client)

            app.dependency_overrides.clear()

        # Cleanup
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await engine.dispose()

        print("\n" + "=" * 70)
        print("  ALL TESTS COMPLETED SUCCESSFULLY!")
        print("=" * 70 + "\n")

    asyncio.run(run_all_tests())
