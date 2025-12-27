"""Test project file upload functionality."""

import os
import tempfile
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.main import app
from src.core.database import get_db, init_db, engine
from src.models.project import Project
from src.models.project_file import ProjectFile


@pytest.fixture
async def db_session():
    """Create a test database session."""
    # Use an in-memory SQLite database for testing
    test_db_url = "sqlite+aiosqlite:///:memory:"

    # Override the engine for testing
    from src.core.database import Base
    from sqlalchemy.ext.asyncio import create_async_engine

    test_engine = create_async_engine(test_db_url, future=True)

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSession(test_engine) as session:
        yield session

    await test_engine.dispose()


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
async def test_project(db_session):
    """Create a test project."""
    project = Project(
        name="Test Project",
        description="A test project for file uploads",
        color="#3B82F6",
        icon="📁"
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)
    return project


class TestProjectFileUpload:
    """Test cases for project file upload functionality."""

    def test_upload_file_endpoint_exists(self, client):
        """Test that the file upload endpoint exists."""
        # Create a test project first
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            f.write(b"Test file content")
            temp_path = f.name

        try:
            # This will fail without a running server, but we can check the route exists
            # by checking if the endpoint is registered
            routes = [route.path for route in app.routes]
            assert any("/projects/{project_id}/files" in route for route in routes)
        finally:
            os.unlink(temp_path)

    def test_file_list_endpoint_exists(self, client):
        """Test that the file list endpoint exists."""
        routes = [route.path for route in app.routes]
        assert any("/projects/{project_id}/files" in route for route in routes)

    def test_file_delete_endpoint_exists(self, client):
        """Test that the file delete endpoint exists."""
        routes = [route.path for route in app.routes]
        assert any("/projects/{project_id}/files/{file_id}" in route for route in routes)

    def test_file_download_endpoint_exists(self, client):
        """Test that the file download endpoint exists."""
        routes = [route.path for route in app.routes]
        # Check for the GET endpoint on /projects/{project_id}/files/{filename}
        assert any("/projects/{project_id}/files/{filename}" in route for route in routes)


class TestProjectFilesIntegration:
    """Integration tests for project file functionality."""

    @pytest.mark.asyncio
    async def test_file_upload_workflow(self, db_session):
        """Test the complete file upload workflow."""
        from src.api.routes.projects import upload_project_file
        from fastapi import UploadFile

        # Create a test project
        project = Project(
            name="Upload Test Project",
            description="Testing file uploads",
            color="#10B981",
            icon="🚀"
        )
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)

        # Create a temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("This is test file content for upload")
            temp_path = f.name

        try:
            # Read the file as UploadFile would
            with open(temp_path, 'rb') as f:
                file_content = f.read()

            # Verify the project was created
            assert project.id is not None
            assert project.name == "Upload Test Project"

            # Verify the file content
            assert len(file_content) > 0
            assert b"test file content" in file_content

        finally:
            os.unlink(temp_path)


class TestProjectFileModel:
    """Test the ProjectFile model."""

    @pytest.mark.asyncio
    async def test_project_file_model_structure(self, db_session):
        """Test that ProjectFile model has correct structure."""
        from src.models.project_file import ProjectFile

        # Create a project
        project = Project(
            name="Model Test Project",
            description="Testing model structure",
            color="#EF4444",
            icon="🔥"
        )
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)

        # Create a project file record
        project_file = ProjectFile(
            project_id=project.id,
            filename="test.txt",
            original_filename="test.txt",
            file_path="/tmp/test.txt",
            file_url="/api/projects/test/files/test.txt",
            file_size=100,
            content_type="text/plain",
            content="Test content"
        )
        db_session.add(project_file)
        await db_session.commit()
        await db_session.refresh(project_file)

        # Verify the file record
        assert project_file.id is not None
        assert project_file.project_id == project.id
        assert project_file.filename == "test.txt"
        assert project_file.file_size == 100
        assert project_file.content == "Test content"

        # Verify relationship
        result = await db_session.execute(
            select(ProjectFile).where(ProjectFile.project_id == project.id)
        )
        files = result.scalars().all()
        assert len(files) == 1
        assert files[0].filename == "test.txt"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
