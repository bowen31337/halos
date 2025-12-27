"""E2E Test for Knowledge Base Search Feature (Feature #164)

This test verifies that users can search through their project knowledge base
(files, documents, and extracted content) to find relevant information.
"""

import pytest
import asyncio
from sqlalchemy import select, or_, func
from httpx import AsyncClient

from src.core.database import async_session_factory, Base, engine
from src.models.project_file import ProjectFile
from src.models.project import Project
from src.main import app


@pytest.fixture(scope="module")
async def setup_test_data():
    """Create test project and files for knowledge base search."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_factory() as session:
        # Create test project
        project = Project(
            id="test-kb-search-project",
            user_id="test-user",
            name="Knowledge Base Test Project",
            description="Test project for knowledge base search",
        )
        session.add(project)

        # Create test files with searchable content
        test_files = [
            ProjectFile(
                id="file-1",
                user_id="test-user",
                project_id="test-kb-search-project",
                filename="api-documentation.pdf",
                original_filename="api-documentation.pdf",
                file_path="/test/api-documentation.pdf",
                file_url="/files/api-documentation.pdf",
                file_size=1024000,
                content_type="application/pdf",
                content="API Documentation: This document describes the REST API endpoints for authentication, user management, and data operations. The API supports JSON responses and implements rate limiting.",
            ),
            ProjectFile(
                id="file-2",
                user_id="test-user",
                project_id="test-kb-search-project",
                filename="user-guide.txt",
                original_filename="user-guide.txt",
                file_path="/test/user-guide.txt",
                file_url="/files/user-guide.txt",
                file_size=5120,
                content_type="text/plain",
                content="User Guide: This guide explains how to use the application. Topics include creating conversations, managing projects, and configuring settings. The interface supports dark mode and multiple languages.",
            ),
            ProjectFile(
                id="file-3",
                user_id="test-user",
                project_id="test-kb-search-project",
                filename="architecture-diagram.png",
                original_filename="architecture-diagram.png",
                file_path="/test/architecture-diagram.png",
                file_url="/files/architecture-diagram.png",
                file_size=2048000,
                content_type="image/png",
                content=None,  # Images don't have extracted text content
            ),
            ProjectFile(
                id="file-4",
                user_id="test-user",
                project_id="test-kb-search-project",
                filename="database-schema.sql",
                original_filename="database-schema.sql",
                file_path="/test/database-schema.sql",
                file_url="/files/database-schema.sql",
                file_size=8192,
                content_type="text/plain",
                content="Database Schema: CREATE TABLE users (id UUID PRIMARY KEY, email VARCHAR(255)); CREATE TABLE conversations (id UUID PRIMARY KEY, title VARCHAR(500));",
            ),
        ]

        for file in test_files:
            session.add(file)

        await session.commit()
        await session.refresh(project)

    yield

    # Cleanup
    async with async_session_factory() as session:
        await session.execute(
            select(ProjectFile).where(
                ProjectFile.project_id == "test-kb-search-project"
            )
        )
        for file in test_files:
            await session.delete(file)
        await session.delete(project)
        await session.commit()


@pytest.mark.asyncio
async def test_knowledge_search_by_filename(setup_test_data):
    """Test searching for files by filename."""
    async with async_session_factory() as session:
        # Search for "API" in filename
        query = select(ProjectFile).where(
            or_(
                ProjectFile.filename.ilike("%API%"),
                ProjectFile.content.ilike("%API%"),
            )
        )

        result = await session.execute(query)
        files = result.scalars().all()

        # Should find the API documentation file
        assert len(files) >= 1
        api_files = [f for f in files if "api" in f.filename.lower()]
        assert len(api_files) >= 1


@pytest.mark.asyncio
async def test_knowledge_search_by_content(setup_test_data):
    """Test searching for files by extracted content."""
    async with async_session_factory() as session:
        # Search for "authentication" in content
        query = select(ProjectFile).where(
            ProjectFile.content.ilike("%authentication%")
        )

        result = await session.execute(query)
        files = result.scalars().all()

        # Should find the API documentation file that mentions authentication
        assert len(files) >= 1
        assert any(
            "authentication" in (f.content or "").lower()
            for f in files
        )


@pytest.mark.asyncio
async def test_knowledge_search_api_endpoint(setup_test_data):
    """Test the /api/search/knowledge endpoint."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Search for "database"
        response = await client.get(
            "/api/search/knowledge",
            params={"q": "database"}
        )

        assert response.status_code == 200
        data = response.json()

        assert "files" in data
        assert "total" in data
        assert isinstance(data["files"], list)
        assert data["total"] >= 0

        # If results exist, verify structure
        if data["total"] > 0:
            file = data["files"][0]
            assert "id" in file
            assert "filename" in file
            assert "content_preview" in file


@pytest.mark.asyncio
async def test_knowledge_search_with_filters(setup_test_data):
    """Test knowledge base search with project filter."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Search within specific project
        response = await client.get(
            "/api/search/knowledge",
            params={
                "q": "guide",
                "project_id": "test-kb-search-project"
            }
        )

        assert response.status_code == 200
        data = response.json()

        # Should find the user guide
        assert data["total"] >= 1
        guide_files = [
            f for f in data["files"]
            if "guide" in f["filename"].lower()
        ]
        assert len(guide_files) >= 1


@pytest.mark.asyncio
async def test_knowledge_search_empty_query(setup_test_data):
    """Test that empty queries return empty results."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Empty search should return no results
        response = await client.get(
            "/api/search/knowledge",
            params={"q": ""}
        )

        assert response.status_code == 200
        data = response.json()

        assert data["files"] == []
        assert data["total"] == 0


@pytest.mark.asyncio
async def test_knowledge_search_content_preview(setup_test_data):
    """Test that search results include content previews."""
    async with async_session_factory() as session:
        # Search for content that exists
        query = select(ProjectFile).where(
            ProjectFile.content.ilike("%REST API%")
        )

        result = await session.execute(query)
        files = result.scalars().all()

        # Find the API documentation file
        api_file = next(
            (f for f in files if "api" in f.filename.lower()),
            None
        )
        assert api_file is not None
        assert api_file.content is not None
        assert "REST API" in api_file.content or "API" in api_file.content


@pytest.mark.asyncio
async def test_global_search_includes_knowledge(setup_test_data):
    """Test that global search includes knowledge base files."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            "/api/search/global",
            params={"q": "schema"}
        )

        assert response.status_code == 200
        data = response.json()

        # Should have files section
        assert "files" in data
        assert isinstance(data["files"], list)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
