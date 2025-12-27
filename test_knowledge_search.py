"""Test knowledge base search feature."""

import asyncio
from sqlalchemy import select, or_
from src.core.database import async_session_factory
from src.models.project_file import ProjectFile


async def test_knowledge_search():
    """Test knowledge base search functionality."""
    async with async_session_factory() as session:
        # Check if we have any project files
        result = await session.execute(select(ProjectFile).limit(5))
        files = result.scalars().all()
        
        print(f"Found {len(files)} project files in database")
        
        for file in files:
            print(f"\nFile: {file.filename}")
            print(f"  Size: {file.file_size} bytes")
            print(f"  Type: {file.content_type}")
            print(f"  Has content: {bool(file.content)}")
            if file.content:
                print(f"  Preview: {file.content[:100]}...")
        
        # Test search query
        if files:
            search_term = "test"
            result = await session.execute(
                select(ProjectFile)
                .where(
                    or_(
                        ProjectFile.filename.ilike(f"%{search_term}%"),
                        ProjectFile.content.ilike(f"%{search_term}%"),
                    )
                )
                .limit(5)
            )
            search_results = result.scalars().all()
            print(f"\n\nSearch for '{search_term}' found {len(search_results)} results")


if __name__ == "__main__":
    asyncio.run(test_knowledge_search())
