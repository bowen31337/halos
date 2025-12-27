"""Saved searches API endpoints."""

import json
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.models.saved_search import SavedSearch

router = APIRouter()


# ==================== Request/Response Models ====================


class SavedSearchCreate(BaseModel):
    """Request model for creating a saved search."""
    name: str = Field(..., min_length=1, max_length=255, description="Name of the saved search")
    query: str = Field(..., min_length=1, max_length=500, description="Search query string")
    filters: Optional[dict] = Field(None, description="Search filters as JSON")
    search_type: str = Field(default="global", description="Type of search: global, conversations, messages, files")
    description: Optional[str] = Field(None, description="Optional description")


class SavedSearchUpdate(BaseModel):
    """Request model for updating a saved search."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    query: Optional[str] = Field(None, min_length=1, max_length=500)
    filters: Optional[dict] = None
    search_type: Optional[str] = None
    description: Optional[str] = None
    display_order: Optional[int] = None


class SavedSearchResponse(BaseModel):
    """Response model for a saved search."""
    id: str
    user_id: str
    name: str
    query: str
    filters: dict
    search_type: str
    description: Optional[str]
    is_active: bool
    usage_count: int
    display_order: int
    created_at: str
    updated_at: str
    last_used_at: Optional[str]


# ==================== API Endpoints ====================


@router.get("", response_model=list[SavedSearchResponse])
async def list_saved_searches(
    user_id: str = "default-user",
    search_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
) -> list[SavedSearchResponse]:
    """List all saved searches for a user."""
    query = select(SavedSearch).where(
        SavedSearch.user_id == user_id,
        SavedSearch.is_active == True
    )

    if search_type:
        query = query.where(SavedSearch.search_type == search_type)

    query = query.order_by(SavedSearch.display_order, SavedSearch.created_at)

    result = await db.execute(query)
    saved_searches = result.scalars().all()

    return [search.to_dict() for search in saved_searches]


@router.post("", response_model=SavedSearchResponse, status_code=status.HTTP_201_CREATED)
async def create_saved_search(
    search_data: SavedSearchCreate,
    user_id: str = "default-user",
    db: AsyncSession = Depends(get_db)
) -> SavedSearchResponse:
    """Create a new saved search."""
    # Get the highest display_order for user's searches
    order_query = select(SavedSearch).where(
        SavedSearch.user_id == user_id
    ).order_by(SavedSearch.display_order.desc())
    order_result = await db.execute(order_query)
    last_search = order_result.scalar_one_or_none()
    next_order = (last_search.display_order + 1) if last_search else 0

    # Create new saved search
    saved_search = SavedSearch(
        user_id=user_id,
        name=search_data.name,
        query=search_data.query,
        filters=json.dumps(search_data.filters) if search_data.filters else None,
        search_type=search_data.search_type,
        description=search_data.description,
        display_order=next_order,
    )

    db.add(saved_search)
    await db.commit()
    await db.refresh(saved_search)

    return saved_search.to_dict()


@router.get("/{search_id}", response_model=SavedSearchResponse)
async def get_saved_search(
    search_id: str,
    user_id: str = "default-user",
    db: AsyncSession = Depends(get_db)
) -> SavedSearchResponse:
    """Get a specific saved search by ID."""
    query = select(SavedSearch).where(
        SavedSearch.id == search_id,
        SavedSearch.user_id == user_id,
        SavedSearch.is_active == True
    )

    result = await db.execute(query)
    saved_search = result.scalar_one_or_none()

    if not saved_search:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Saved search '{search_id}' not found"
        )

    return saved_search.to_dict()


@router.put("/{search_id}", response_model=SavedSearchResponse)
async def update_saved_search(
    search_id: str,
    search_data: SavedSearchUpdate,
    user_id: str = "default-user",
    db: AsyncSession = Depends(get_db)
) -> SavedSearchResponse:
    """Update a saved search."""
    query = select(SavedSearch).where(
        SavedSearch.id == search_id,
        SavedSearch.user_id == user_id,
        SavedSearch.is_active == True
    )

    result = await db.execute(query)
    saved_search = result.scalar_one_or_none()

    if not saved_search:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Saved search '{search_id}' not found"
        )

    # Update fields if provided
    if search_data.name is not None:
        saved_search.name = search_data.name
    if search_data.query is not None:
        saved_search.query = search_data.query
    if search_data.filters is not None:
        saved_search.filters = json.dumps(search_data.filters)
    if search_data.search_type is not None:
        saved_search.search_type = search_data.search_type
    if search_data.description is not None:
        saved_search.description = search_data.description
    if search_data.display_order is not None:
        saved_search.display_order = search_data.display_order

    saved_search.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(saved_search)

    return saved_search.to_dict()


@router.delete("/{search_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_saved_search(
    search_id: str,
    user_id: str = "default-user",
    db: AsyncSession = Depends(get_db)
) -> None:
    """Delete a saved search (soft delete)."""
    query = select(SavedSearch).where(
        SavedSearch.id == search_id,
        SavedSearch.user_id == user_id,
        SavedSearch.is_active == True
    )

    result = await db.execute(query)
    saved_search = result.scalar_one_or_none()

    if not saved_search:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Saved search '{search_id}' not found"
        )

    # Soft delete
    saved_search.is_active = False
    saved_search.updated_at = datetime.utcnow()

    await db.commit()


@router.post("/{search_id}/run", response_model=dict)
async def run_saved_search(
    search_id: str,
    user_id: str = "default-user",
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Run a saved search and increment usage count."""
    query = select(SavedSearch).where(
        SavedSearch.id == search_id,
        SavedSearch.user_id == user_id,
        SavedSearch.is_active == True
    )

    result = await db.execute(query)
    saved_search = result.scalar_one_or_none()

    if not saved_search:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Saved search '{search_id}' not found"
        )

    # Increment usage count and update last_used_at
    saved_search.increment_usage()
    await db.commit()

    # Return the saved search data to be used for actual searching
    return {
        "search_id": saved_search.id,
        "query": saved_search.query,
        "filters": json.loads(saved_search.filters) if saved_search.filters else {},
        "search_type": saved_search.search_type,
        "name": saved_search.name,
    }


@router.post("/{search_id}/reorder", status_code=status.HTTP_200_OK)
async def reorder_saved_searches(
    search_id: str,
    new_order: int,
    user_id: str = "default-user",
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Reorder a saved search by changing its display_order."""
    query = select(SavedSearch).where(
        SavedSearch.id == search_id,
        SavedSearch.user_id == user_id,
        SavedSearch.is_active == True
    )

    result = await db.execute(query)
    saved_search = result.scalar_one_or_none()

    if not saved_search:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Saved search '{search_id}' not found"
        )

    saved_search.display_order = new_order
    saved_search.updated_at = datetime.utcnow()

    await db.commit()

    return {"message": "Search reordered successfully", "new_order": new_order}
