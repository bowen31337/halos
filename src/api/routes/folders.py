"""Folder management endpoints for organizing conversations hierarchically."""

from typing import Optional
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.models import Folder as FolderModel, FolderItem as FolderItemModel, Conversation as ConversationModel

router = APIRouter()


class FolderCreate(BaseModel):
    """Request model for creating a folder."""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=500)
    parent_folder_id: Optional[UUID] = None


class FolderUpdate(BaseModel):
    """Request model for updating a folder."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=500)
    parent_folder_id: Optional[UUID] = None
    position: Optional[int] = None
    is_archived: Optional[bool] = None


class AddConversationToFolderRequest(BaseModel):
    """Request model for adding a conversation to a folder."""

    conversation_id: UUID
    position: Optional[int] = None


class FolderResponse(BaseModel):
    """Response model for a folder."""

    id: str
    name: str
    description: Optional[str]
    parent_folder_id: Optional[str]
    position: int
    is_archived: bool
    created_at: str
    updated_at: str


@router.get("")
async def list_folders(
    parent_folder_id: Optional[UUID] = None,
    archived: bool = False,
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """List all folders."""
    query = select(FolderModel).where(FolderModel.is_deleted == False)

    if archived:
        query = query.where(FolderModel.is_archived == True)
    else:
        query = query.where(FolderModel.is_archived == False)

    if parent_folder_id:
        query = query.where(FolderModel.parent_folder_id == str(parent_folder_id))
    else:
        # Only get root folders (no parent)
        query = query.where(FolderModel.parent_folder_id == None)

    query = query.order_by(FolderModel.position, FolderModel.created_at)

    result = await db.execute(query)
    folders = result.scalars().all()

    return [
        {
            "id": folder.id,
            "name": folder.name,
            "description": folder.description,
            "parent_folder_id": folder.parent_folder_id,
            "position": folder.position,
            "is_archived": folder.is_archived,
            "created_at": folder.created_at.isoformat(),
            "updated_at": folder.updated_at.isoformat(),
        }
        for folder in folders
    ]


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_folder(
    data: FolderCreate,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Create a new folder."""
    # Get position for new folder
    if data.parent_folder_id:
        result = await db.execute(
            select(FolderModel)
            .where(FolderModel.parent_folder_id == str(data.parent_folder_id))
            .where(FolderModel.is_deleted == False)
            .order_by(FolderModel.position.desc())
            .limit(1)
        )
    else:
        result = await db.execute(
            select(FolderModel)
            .where(FolderModel.parent_folder_id == None)
            .where(FolderModel.is_deleted == False)
            .order_by(FolderModel.position.desc())
            .limit(1)
        )

    last_folder = result.scalar_one_or_none()
    position = (last_folder.position + 1) if last_folder else 0

    folder = FolderModel(
        name=data.name,
        description=data.description,
        parent_folder_id=str(data.parent_folder_id) if data.parent_folder_id else None,
        position=position,
    )

    db.add(folder)
    await db.commit()
    await db.refresh(folder)

    return {
        "id": folder.id,
        "name": folder.name,
        "description": folder.description,
        "parent_folder_id": folder.parent_folder_id,
        "position": folder.position,
        "is_archived": folder.is_archived,
        "created_at": folder.created_at.isoformat(),
        "updated_at": folder.updated_at.isoformat(),
    }


@router.get("/{folder_id}")
async def get_folder(
    folder_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get a specific folder."""
    result = await db.execute(
        select(FolderModel)
        .where(FolderModel.id == folder_id)
        .where(FolderModel.is_deleted == False)
    )
    folder = result.scalar_one_or_none()

    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")

    return {
        "id": folder.id,
        "name": folder.name,
        "description": folder.description,
        "parent_folder_id": folder.parent_folder_id,
        "position": folder.position,
        "is_archived": folder.is_archived,
        "created_at": folder.created_at.isoformat(),
        "updated_at": folder.updated_at.isoformat(),
    }


@router.put("/{folder_id}")
async def update_folder(
    folder_id: str,
    data: FolderUpdate,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Update a folder."""
    result = await db.execute(
        select(FolderModel)
        .where(FolderModel.id == folder_id)
        .where(FolderModel.is_deleted == False)
    )
    folder = result.scalar_one_or_none()

    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")

    if data.name is not None:
        folder.name = data.name
    if data.description is not None:
        folder.description = data.description
    if data.parent_folder_id is not None:
        folder.parent_folder_id = str(data.parent_folder_id)
    if data.position is not None:
        folder.position = data.position
    if data.is_archived is not None:
        folder.is_archived = data.is_archived

    folder.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(folder)

    return {
        "id": folder.id,
        "name": folder.name,
        "description": folder.description,
        "parent_folder_id": folder.parent_folder_id,
        "position": folder.position,
        "is_archived": folder.is_archived,
        "created_at": folder.created_at.isoformat(),
        "updated_at": folder.updated_at.isoformat(),
    }


@router.delete("/{folder_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_folder(
    folder_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a folder (soft delete)."""
    result = await db.execute(
        select(FolderModel)
        .where(FolderModel.id == folder_id)
        .where(FolderModel.is_deleted == False)
    )
    folder = result.scalar_one_or_none()

    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")

    folder.is_deleted = True
    await db.commit()


@router.post("/{folder_id}/items")
async def add_conversation_to_folder(
    folder_id: str,
    data: AddConversationToFolderRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Add a conversation to a folder."""
    # Verify folder exists
    folder_result = await db.execute(
        select(FolderModel)
        .where(FolderModel.id == folder_id)
        .where(FolderModel.is_deleted == False)
    )
    folder = folder_result.scalar_one_or_none()

    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")

    # Verify conversation exists
    conversation_result = await db.execute(
        select(ConversationModel)
        .where(ConversationModel.id == str(data.conversation_id))
        .where(ConversationModel.is_deleted == False)
    )
    conversation = conversation_result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Check if conversation is already in a folder
    existing_item_result = await db.execute(
        select(FolderItemModel)
        .where(FolderItemModel.conversation_id == str(data.conversation_id))
    )
    existing_item = existing_item_result.scalar_one_or_none()

    if existing_item:
        raise HTTPException(
            status_code=400,
            detail="Conversation is already in a folder. Remove it first."
        )

    # Get position for new item
    position_result = await db.execute(
        select(FolderItemModel)
        .where(FolderItemModel.folder_id == folder_id)
        .order_by(FolderItemModel.position.desc())
        .limit(1)
    )
    last_item = position_result.scalar_one_or_none()
    position = (last_item.position + 1) if last_item else (data.position if data.position is not None else 0)

    folder_item = FolderItemModel(
        folder_id=folder_id,
        conversation_id=str(data.conversation_id),
        position=position,
    )

    db.add(folder_item)
    await db.commit()
    await db.refresh(folder_item)

    return {
        "id": folder_item.id,
        "folder_id": folder_item.folder_id,
        "conversation_id": folder_item.conversation_id,
        "position": folder_item.position,
        "created_at": folder_item.created_at.isoformat(),
    }


@router.get("/{folder_id}/items")
async def list_folder_items(
    folder_id: str,
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """List all conversations in a folder."""
    # Verify folder exists
    folder_result = await db.execute(
        select(FolderModel)
        .where(FolderModel.id == folder_id)
        .where(FolderModel.is_deleted == False)
    )
    folder = folder_result.scalar_one_or_none()

    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")

    # Get folder items with conversation details
    result = await db.execute(
        select(FolderItemModel, ConversationModel)
        .join(ConversationModel, FolderItemModel.conversation_id == ConversationModel.id)
        .where(FolderItemModel.folder_id == folder_id)
        .where(ConversationModel.is_deleted == False)
        .order_by(FolderItemModel.position)
    )

    items = result.all()

    return [
        {
            "id": item[0].id,
            "folder_id": item[0].folder_id,
            "conversation_id": item[0].conversation_id,
            "position": item[0].position,
            "created_at": item[0].created_at.isoformat(),
            "conversation": {
                "id": item[1].id,
                "title": item[1].title,
                "model": item[1].model,
                "message_count": item[1].message_count,
            }
        }
        for item in items
    ]


@router.delete("/{folder_id}/items/{conversation_id}")
async def remove_conversation_from_folder(
    folder_id: str,
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Remove a conversation from a folder."""
    result = await db.execute(
        select(FolderItemModel)
        .where(FolderItemModel.folder_id == folder_id)
        .where(FolderItemModel.conversation_id == conversation_id)
    )
    folder_item = result.scalar_one_or_none()

    if not folder_item:
        raise HTTPException(status_code=404, detail="Conversation not found in folder")

    await db.delete(folder_item)
    await db.commit()
