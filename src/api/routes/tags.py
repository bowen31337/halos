"""Conversation tags management endpoints."""

import uuid
from typing import Optional
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, HTTPException, status, Depends, Request
from pydantic import BaseModel, Field
from sqlalchemy import select, delete, func, distinct
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.models import Tag, Conversation, conversation_tags
from src.utils.audit import log_audit, get_request_info
from src.models.audit_log import AuditActionType as AuditAction

router = APIRouter()


class TagCreate(BaseModel):
    """Request model for creating a tag."""

    name: str = Field(..., min_length=1, max_length=50)
    color: Optional[str] = Field("#3b82f6", max_length=7)  # Hex color code


class TagUpdate(BaseModel):
    """Request model for updating a tag."""

    name: Optional[str] = Field(None, min_length=1, max_length=50)
    color: Optional[str] = Field(None, max_length=7)


class ConversationTagUpdate(BaseModel):
    """Request model for updating conversation tags."""

    tag_ids: list[str]


@router.get("")
async def list_tags(
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """List all available tags."""
    result = await db.execute(select(Tag).where(Tag.is_deleted == False))
    tags = result.scalars().all()

    return [
        {
            "id": tag.id,
            "name": tag.name,
            "color": tag.color,
            "created_at": tag.created_at.isoformat(),
        }
        for tag in tags
    ]


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_tag(
    data: TagCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Create a new tag."""
    # Check if tag already exists
    result = await db.execute(select(Tag).where(Tag.name == data.name))
    existing_tag = result.scalar_one_or_none()

    if existing_tag:
        raise HTTPException(status_code=400, detail="Tag with this name already exists")

    tag = Tag(
        name=data.name,
        color=data.color or "#3b82f6",
    )

    db.add(tag)
    await db.commit()
    await db.refresh(tag)

    # Audit log
    ip_address, user_agent = get_request_info(request)
    await log_audit(
        db=db,
        user_id="default-user",
        action=AuditAction.TAG_CREATE,
        resource_type="tag",
        resource_id=tag.id,
        details={"name": tag.name, "color": tag.color},
        ip_address=ip_address,
        user_agent=user_agent,
    )

    return {
        "id": tag.id,
        "name": tag.name,
        "color": tag.color,
        "created_at": tag.created_at.isoformat(),
    }


@router.get("/{tag_id}")
async def get_tag(
    tag_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get a specific tag."""
    result = await db.execute(
        select(Tag)
        .where(Tag.id == tag_id)
        .where(Tag.is_deleted == False)
    )
    tag = result.scalar_one_or_none()

    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")

    return {
        "id": tag.id,
        "name": tag.name,
        "color": tag.color,
        "created_at": tag.created_at.isoformat(),
    }


@router.put("/{tag_id}")
async def update_tag(
    tag_id: str,
    data: TagUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Update a tag."""
    result = await db.execute(
        select(Tag)
        .where(Tag.id == tag_id)
        .where(Tag.is_deleted == False)
    )
    tag = result.scalar_one_or_none()

    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")

    changes = {}
    if data.name is not None and data.name != tag.name:
        # Check if new name already exists
        result = await db.execute(select(Tag).where(Tag.name == data.name))
        existing_tag = result.scalar_one_or_none()
        if existing_tag and existing_tag.id != tag.id:
            raise HTTPException(status_code=400, detail="Tag with this name already exists")
        changes["name"] = {"from": tag.name, "to": data.name}
        tag.name = data.name
    if data.color is not None and data.color != tag.color:
        changes["color"] = {"from": tag.color, "to": data.color}
        tag.color = data.color

    tag.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(tag)

    # Audit log
    if changes:
        ip_address, user_agent = get_request_info(request)
        await log_audit(
            db=db,
            user_id="default-user",
            action=AuditAction.TAG_UPDATE,
            resource_type="tag",
            resource_id=tag.id,
            details={"changes": changes},
            ip_address=ip_address,
            user_agent=user_agent,
        )

    return {
        "id": tag.id,
        "name": tag.name,
        "color": tag.color,
        "created_at": tag.created_at.isoformat(),
        "updated_at": tag.updated_at.isoformat(),
    }


@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tag(
    tag_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a tag."""
    result = await db.execute(
        select(Tag)
        .where(Tag.id == tag_id)
        .where(Tag.is_deleted == False)
    )
    tag = result.scalar_one_or_none()

    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")

    # Remove tag from all conversations first
    await db.execute(
        delete(conversation_tags)
        .where(conversation_tags.c.tag_id == tag_id)
    )

    # Mark tag as deleted
    tag.is_deleted = True
    await db.commit()

    # Audit log
    ip_address, user_agent = get_request_info(request)
    await log_audit(
        db=db,
        user_id="default-user",
        action=AuditAction.TAG_DELETE,
        resource_type="tag",
        resource_id=tag.id,
        details={"name": tag.name},
        ip_address=ip_address,
        user_agent=user_agent,
    )


@router.post("/conversations/{conversation_id}/tags")
async def update_conversation_tags(
    conversation_id: str,
    data: ConversationTagUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Update tags for a conversation."""
    # Verify conversation exists
    result = await db.execute(
        select(Conversation)
        .where(Conversation.id == conversation_id)
        .where(Conversation.is_deleted == False)
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Verify all tags exist and are not deleted
    if data.tag_ids:
        result = await db.execute(
            select(Tag)
            .where(Tag.id.in_(data.tag_ids))
            .where(Tag.is_deleted == False)
        )
        existing_tags = result.scalars().all()
        existing_tag_ids = {tag.id for tag in existing_tags}

        # Check for non-existent tags
        for tag_id in data.tag_ids:
            if tag_id not in existing_tag_ids:
                raise HTTPException(status_code=404, detail=f"Tag {tag_id} not found")

        # Replace conversation tags
        conversation.tags = existing_tags
    else:
        # Remove all tags
        conversation.tags = []

    await db.commit()
    await db.refresh(conversation)

    # Audit log
    ip_address, user_agent = get_request_info(request)
    await log_audit(
        db=db,
        user_id="default-user",
        action=AuditAction.CONVERSATION_UPDATE,
        resource_type="conversation",
        resource_id=conversation.id,
        details={"tag_ids": data.tag_ids},
        ip_address=ip_address,
        user_agent=user_agent,
    )

    return {
        "conversation_id": conversation.id,
        "tag_ids": data.tag_ids,
        "tags": [{"id": tag.id, "name": tag.name, "color": tag.color} for tag in conversation.tags],
    }


@router.get("/conversations/filter/by-tags")
async def filter_conversations_by_tags(
    tag_ids: str,  # Comma-separated tag IDs
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """Filter conversations by tags."""
    if not tag_ids:
        return []

    tag_id_list = [tag_id.strip() for tag_id in tag_ids.split(",") if tag_id.strip()]

    if not tag_id_list:
        return []

    # Query conversations that have all the specified tags
    query = (
        select(Conversation)
        .join(conversation_tags)
        .join(Tag)
        .where(conversation_tags.c.tag_id.in_(tag_id_list))
        .where(Conversation.is_deleted == False)
        .group_by(Conversation.id)
        .having(func.count(distinct(conversation_tags.c.tag_id)) == len(tag_id_list))
    )

    result = await db.execute(query)
    conversations = result.scalars().all()

    return [
        {
            "id": conv.id,
            "title": conv.title,
            "model": conv.model,
            "project_id": conv.project_id,
            "is_archived": conv.is_archived,
            "is_pinned": conv.is_pinned,
            "message_count": conv.message_count,
            "unread_count": conv.unread_count,
            "tags": [{"id": tag.id, "name": tag.name, "color": tag.color} for tag in conv.tags],
            "created_at": conv.created_at.isoformat(),
            "updated_at": conv.updated_at.isoformat(),
        }
        for conv in conversations
    ]