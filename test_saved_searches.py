#!/usr/bin/env python3
"""Test script for saved searches API endpoints."""

import asyncio
import json
from sqlalchemy import select

from src.core.database import get_db
from src.models.saved_search import SavedSearch


async def test_saved_searches():
    """Test saved searches CRUD operations."""

    # Get database session
    async for db in get_db():
        try:
            print("=== Testing Saved Searches Backend ===\n")

            # Test 1: Create a saved search
            print("1. Creating saved search...")
            new_search = SavedSearch(
                user_id="test-user",
                name="Python Tutorials",
                query="python tutorial",
                filters=json.dumps({"category": "coding", "date_range": "30d"}),
                search_type="conversations",
                description="Search for Python tutorial conversations"
            )

            db.add(new_search)
            await db.commit()
            await db.refresh(new_search)

            print(f"   ✓ Created search: {new_search.name} (ID: {new_search.id})\n")

            # Test 2: List saved searches
            print("2. Listing saved searches...")
            result = await db.execute(
                select(SavedSearch).where(SavedSearch.user_id == "test-user")
            )
            searches = result.scalars().all()
            print(f"   ✓ Found {len(searches)} saved search(es)")
            for search in searches:
                print(f"     - {search.name}: {search.query}")
            print()

            # Test 3: Get specific search
            print("3. Getting specific search...")
            result = await db.execute(
                select(SavedSearch).where(SavedSearch.id == new_search.id)
            )
            found_search = result.scalar_one_or_none()
            if found_search:
                print(f"   ✓ Found search: {found_search.name}")
                print(f"     Filters: {found_search.filters}\n")
            else:
                print("   ✗ Search not found\n")

            # Test 4: Update search
            print("4. Updating search...")
            found_search.name = "Python Advanced Tutorials"
            found_search.description = "Advanced Python tutorials and examples"
            await db.commit()
            await db.refresh(found_search)
            print(f"   ✓ Updated search name to: {found_search.name}\n")

            # Test 5: Increment usage
            print("5. Incrementing usage count...")
            found_search.increment_usage()
            await db.commit()
            print(f"   ✓ Usage count: {found_search.usage_count}\n")

            # Test 6: Create multiple searches for ordering
            print("6. Creating multiple searches...")
            for i in range(3):
                search = SavedSearch(
                    user_id="test-user",
                    name=f"Test Search {i+1}",
                    query=f"test query {i+1}",
                    search_type="global",
                    display_order=i,
                )
                db.add(search)
            await db.commit()
            print("   ✓ Created 3 additional searches\n")

            # Test 7: List all searches ordered
            print("7. Listing searches with ordering...")
            result = await db.execute(
                select(SavedSearch)
                .where(SavedSearch.user_id == "test-user", SavedSearch.is_active == True)
                .order_by(SavedSearch.display_order)
            )
            searches = result.scalars().all()
            print(f"   ✓ Found {len(searches)} searches (ordered):")
            for search in searches:
                print(f"     [{search.display_order}] {search.name}")
            print()

            # Test 8: Test to_dict method
            print("8. Testing to_dict method...")
            search_dict = found_search.to_dict()
            print(f"   ✓ Dictionary representation:")
            print(f"     - ID: {search_dict['id']}")
            print(f"     - Name: {search_dict['name']}")
            print(f"     - Query: {search_dict['query']}")
            print(f"     - Filters: {search_dict['filters']}")
            print(f"     - Usage count: {search_dict['usage_count']}")
            print()

            # Test 9: Soft delete
            print("9. Testing soft delete...")
            found_search.is_active = False
            await db.commit()
            result = await db.execute(
                select(SavedSearch).where(
                    SavedSearch.user_id == "test-user",
                    SavedSearch.is_active == True
                )
            )
            active_count = len(result.scalars().all())
            print(f"   ✓ Soft deleted. Active searches remaining: {active_count}\n")

            print("=== All Backend Tests Passed! ===")

        except Exception as e:
            print(f"✗ Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            break  # Exit after first iteration of async for


if __name__ == "__main__":
    asyncio.run(test_saved_searches())
