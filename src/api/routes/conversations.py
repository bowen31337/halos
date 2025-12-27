"""Conversation management endpoints."""

import json
from typing import Optional
from uuid import UUID
from datetime import datetime
from pathlib import Path
import os

from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from src.core.database import get_db
from src.models import Conversation as ConversationModel, Message as MessageModel

router = APIRouter()


class ConversationCreate(BaseModel):
    """Request model for creating a conversation."""

    title: Optional[str] = None
    project_id: Optional[UUID] = None
    model: str = "claude-sonnet-4-5-20250929"


class ConversationUpdate(BaseModel):
    """Request model for updating a conversation."""

    title: Optional[str] = None
    is_archived: Optional[bool] = None
    is_pinned: Optional[bool] = None


class MoveConversationRequest(BaseModel):
    """Request model for moving a conversation to a project."""

    project_id: Optional[str] = None


class BranchConversationRequest(BaseModel):
    """Request model for creating a branch from a conversation."""

    branch_name: str = Field(..., min_length=1, max_length=100)
    branch_color: Optional[str] = Field(None, max_length=20)
    message_id: str = Field(..., description="The message ID to branch from")


class ConversationResponse(BaseModel):
    """Response model for a conversation."""

    id: str
    title: str
    model: str
    project_id: Optional[str] = None
    is_archived: bool = False
    is_pinned: bool = False
    message_count: int = 0
    created_at: str
    updated_at: str


@router.get("")
async def list_conversations(
    project_id: Optional[UUID] = None,
    archived: bool = False,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """List all conversations."""
    query = select(ConversationModel).where(ConversationModel.is_deleted == False)

    if archived:
        query = query.where(ConversationModel.is_archived == True)
    else:
        query = query.where(ConversationModel.is_archived == False)

    if project_id:
        query = query.where(ConversationModel.project_id == str(project_id))

    query = query.order_by(ConversationModel.updated_at.desc()).offset(offset).limit(limit)

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
            "created_at": conv.created_at.isoformat(),
            "updated_at": conv.updated_at.isoformat(),
        }
        for conv in conversations
    ]


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_conversation(
    data: ConversationCreate,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Create a new conversation."""
    conversation = ConversationModel(
        title=data.title or "New Conversation",
        model=data.model,
        project_id=str(data.project_id) if data.project_id else None,
    )

    db.add(conversation)
    await db.commit()
    await db.refresh(conversation)

    return {
        "id": conversation.id,
        "title": conversation.title,
        "model": conversation.model,
        "project_id": conversation.project_id,
        "is_archived": conversation.is_archived,
        "is_pinned": conversation.is_pinned,
        "message_count": conversation.message_count,
        "created_at": conversation.created_at.isoformat(),
        "updated_at": conversation.updated_at.isoformat(),
    }


@router.get("/{conversation_id}")
async def get_conversation(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get a specific conversation."""
    result = await db.execute(select(ConversationModel).where(ConversationModel.id == conversation_id))
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return {
        "id": conversation.id,
        "title": conversation.title,
        "model": conversation.model,
        "project_id": conversation.project_id,
        "is_archived": conversation.is_archived,
        "is_pinned": conversation.is_pinned,
        "message_count": conversation.message_count,
        "created_at": conversation.created_at.isoformat(),
        "updated_at": conversation.updated_at.isoformat(),
    }


@router.put("/{conversation_id}")
async def update_conversation(
    conversation_id: str,
    data: ConversationUpdate,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Update a conversation."""
    result = await db.execute(select(ConversationModel).where(ConversationModel.id == conversation_id))
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    if data.title is not None:
        conversation.title = data.title
    if data.is_archived is not None:
        conversation.is_archived = data.is_archived
    if data.is_pinned is not None:
        conversation.is_pinned = data.is_pinned

    conversation.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(conversation)

    return {
        "id": conversation.id,
        "title": conversation.title,
        "model": conversation.model,
        "project_id": conversation.project_id,
        "is_archived": conversation.is_archived,
        "is_pinned": conversation.is_pinned,
        "message_count": conversation.message_count,
        "created_at": conversation.created_at.isoformat(),
        "updated_at": conversation.updated_at.isoformat(),
    }


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a conversation (soft delete)."""
    result = await db.execute(select(ConversationModel).where(ConversationModel.id == conversation_id))
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    conversation.is_deleted = True
    await db.commit()


@router.post("/{conversation_id}/duplicate")
async def duplicate_conversation(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Duplicate a conversation."""
    result = await db.execute(select(ConversationModel).where(ConversationModel.id == conversation_id))
    original = result.scalar_one_or_none()

    if not original:
        raise HTTPException(status_code=404, detail="Conversation not found")

    now = datetime.utcnow()

    duplicate = ConversationModel(
        title=f"{original.title} (Copy)",
        model=original.model,
        project_id=original.project_id,
        created_at=now,
        updated_at=now,
        last_message_at=now,
    )

    db.add(duplicate)
    await db.commit()
    await db.refresh(duplicate)

    return {
        "id": duplicate.id,
        "title": duplicate.title,
        "model": duplicate.model,
        "project_id": duplicate.project_id,
        "is_archived": duplicate.is_archived,
        "is_pinned": duplicate.is_pinned,
        "message_count": duplicate.message_count,
        "created_at": duplicate.created_at.isoformat(),
        "updated_at": duplicate.updated_at.isoformat(),
    }


@router.post("/{conversation_id}/move")
async def move_conversation(
    conversation_id: str,
    data: MoveConversationRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Move a conversation to a different project (or remove from project)."""
    result = await db.execute(
        select(ConversationModel).where(ConversationModel.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Update project_id (can be None to remove from project)
    conversation.project_id = data.project_id
    conversation.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(conversation)

    return {
        "id": conversation.id,
        "title": conversation.title,
        "model": conversation.model,
        "project_id": conversation.project_id,
        "is_archived": conversation.is_archived,
        "is_pinned": conversation.is_pinned,
        "message_count": conversation.message_count,
        "created_at": conversation.created_at.isoformat(),
        "updated_at": conversation.updated_at.isoformat(),
    }


@router.post("/{conversation_id}/export")
async def export_conversation(
    conversation_id: str,
    format: str = "json",
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Export a conversation in JSON or Markdown format."""
    # Get conversation
    result = await db.execute(
        select(ConversationModel).where(ConversationModel.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Get messages
    messages_result = await db.execute(
        select(MessageModel)
        .where(MessageModel.conversation_id == conversation_id)
        .order_by(MessageModel.created_at)
    )
    messages = messages_result.scalars().all()

    if format.lower() == "json":
        # Export as JSON
        export_data = {
            "id": conversation.id,
            "title": conversation.title,
            "model": conversation.model,
            "created_at": conversation.created_at.isoformat(),
            "updated_at": conversation.updated_at.isoformat(),
            "messages": [
                {
                    "id": msg.id,
                    "role": msg.role,
                    "content": msg.content,
                    "created_at": msg.created_at.isoformat(),
                    "edited_at": msg.edited_at.isoformat() if msg.edited_at else None,
                    "tool_calls": msg.tool_calls,
                    "tool_results": msg.tool_results,
                    "thinking_content": msg.thinking_content,
                    "attachments": msg.attachments,
                    "input_tokens": msg.input_tokens,
                    "output_tokens": msg.output_tokens,
                    "cache_read_tokens": msg.cache_read_tokens,
                    "cache_write_tokens": msg.cache_write_tokens,
                }
                for msg in messages
            ],
            "metadata": {
                "message_count": len(messages),
                "token_count": conversation.token_count,
                "is_archived": conversation.is_archived,
                "is_pinned": conversation.is_pinned,
            }
        }

        json_str = json.dumps(export_data, indent=2, ensure_ascii=False)
        filename = f"{conversation.title.replace(' ', '_').replace('/', '_')}_export.json"

        return Response(
            content=json_str,
            media_type="application/json",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )

    elif format.lower() == "markdown":
        # Export as Markdown
        md_lines = [
            f"# {conversation.title}",
            "",
            f"**Model:** {conversation.model}",
            f"**Created:** {conversation.created_at.strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Updated:** {conversation.updated_at.strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Message Count:** {len(messages)}",
            "",
            "---",
            "",
        ]

        for msg in messages:
            if msg.role == "user":
                md_lines.append("## 👤 User")
            elif msg.role == "assistant":
                md_lines.append("## 🤖 Assistant")
            elif msg.role == "system":
                md_lines.append("## ⚙️ System")
            elif msg.role == "tool":
                tool_name = "unknown"
                if msg.tool_calls and "name" in msg.tool_calls:
                    tool_name = msg.tool_calls["name"]
                md_lines.append(f"## 🔧 Tool: {tool_name}")

            md_lines.append("")
            md_lines.append(msg.content)
            md_lines.append("")

            # Add thinking content if present
            if msg.thinking_content:
                md_lines.append("<details>")
                md_lines.append("<summary>Thinking Process</summary>")
                md_lines.append("")
                md_lines.append(msg.thinking_content)
                md_lines.append("")
                md_lines.append("</details>")
                md_lines.append("")

            # Add tool results if present
            if msg.tool_results:
                md_lines.append("**Tool Results:**")
                md_lines.append("```json")
                md_lines.append(json.dumps(msg.tool_results, indent=2))
                md_lines.append("```")
                md_lines.append("")

            # Add tool calls if present
            if msg.tool_calls:
                md_lines.append("**Tool Call:**")
                md_lines.append("```json")
                md_lines.append(json.dumps(msg.tool_calls, indent=2))
                md_lines.append("```")
                md_lines.append("")

            # Add token info
            if msg.input_tokens or msg.output_tokens:
                total = msg.input_tokens + msg.output_tokens
                md_lines.append(f"*Tokens: {msg.input_tokens} in, {msg.output_tokens} out, {total} total*")
                md_lines.append("")

            md_lines.append("---")
            md_lines.append("")

        md_content = "\n".join(md_lines)
        filename = f"{conversation.title.replace(' ', '_').replace('/', '_')}_export.md"

        return Response(
            content=md_content,
            media_type="text/markdown",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )

    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format: {format}. Supported formats: json, markdown"
        )


@router.post("/{conversation_id}/branch")
async def create_branch(
    conversation_id: str,
    data: BranchConversationRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Create a new branch from a conversation at a specific message."""
    from uuid import uuid4
    from datetime import datetime

    # Check if parent conversation exists
    result = await db.execute(
        select(ConversationModel).where(ConversationModel.id == conversation_id)
    )
    parent_conversation = result.scalar_one_or_none()

    if not parent_conversation:
        raise HTTPException(status_code=404, detail="Parent conversation not found")

    # Check if the branch point message exists
    result = await db.execute(
        select(MessageModel).where(MessageModel.id == data.message_id)
    )
    branch_point_message = result.scalar_one_or_none()

    if not branch_point_message:
        raise HTTPException(status_code=404, detail="Branch point message not found")

    # Validate that the message belongs to this conversation
    if branch_point_message.conversation_id != conversation_id:
        raise HTTPException(status_code=400, detail="Branch point message does not belong to this conversation")

    # Create branch conversation
    now = datetime.utcnow()
    branch_name = data.branch_name or f"Branch from {parent_conversation.title}"

    branch_conversation = ConversationModel(
        title=f"{parent_conversation.title} - {branch_name}",
        model=parent_conversation.model,
        project_id=parent_conversation.project_id,
        parent_conversation_id=parent_conversation.id,
        branch_point_message_id=data.message_id,
        branch_name=branch_name,
        branch_color=data.branch_color,
        created_at=now,
        updated_at=now,
        last_message_at=now,
    )

    db.add(branch_conversation)
    await db.commit()
    await db.refresh(branch_conversation)

    # Copy messages up to and including the branch point
    result = await db.execute(
        select(MessageModel)
        .where(MessageModel.conversation_id == conversation_id)
        .where(MessageModel.created_at <= branch_point_message.created_at)
        .order_by(MessageModel.created_at)
    )
    messages_to_copy = result.scalars().all()

    for msg in messages_to_copy:
        new_message = MessageModel(
            conversation_id=branch_conversation.id,
            role=msg.role,
            content=msg.content,
            attachments=msg.attachments,
            tool_calls=msg.tool_calls,
            tool_results=msg.tool_results,
            thinking_content=msg.thinking_content,
            input_tokens=msg.input_tokens,
            output_tokens=msg.output_tokens,
            cache_read_tokens=msg.cache_read_tokens,
            cache_write_tokens=msg.cache_write_tokens,
            created_at=msg.created_at,
            edited_at=msg.edited_at,
        )
        db.add(new_message)

    # Mark the branch point message as a branch point in the original conversation
    branch_point_message.is_branch_point = True
    branch_conversation.message_count = len(messages_to_copy)
    branch_conversation.token_count = sum(msg.input_tokens + msg.output_tokens for msg in messages_to_copy)

    await db.commit()
    await db.refresh(branch_conversation)

    return {
        "id": branch_conversation.id,
        "title": branch_conversation.title,
        "model": branch_conversation.model,
        "project_id": branch_conversation.project_id,
        "parent_conversation_id": branch_conversation.parent_conversation_id,
        "branch_point_message_id": branch_conversation.branch_point_message_id,
        "branch_name": branch_conversation.branch_name,
        "branch_color": branch_conversation.branch_color,
        "is_archived": branch_conversation.is_archived,
        "is_pinned": branch_conversation.is_pinned,
        "message_count": branch_conversation.message_count,
        "token_count": branch_conversation.token_count,
        "created_at": branch_conversation.created_at.isoformat(),
        "updated_at": branch_conversation.updated_at.isoformat(),
    }


@router.get("/{conversation_id}/branches")
async def list_branches(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """List all branches for a conversation."""
    result = await db.execute(
        select(ConversationModel)
        .where(ConversationModel.parent_conversation_id == conversation_id)
        .order_by(ConversationModel.created_at)
    )
    branches = result.scalars().all()

    return [
        {
            "id": branch.id,
            "title": branch.title,
            "model": branch.model,
            "project_id": branch.project_id,
            "parent_conversation_id": branch.parent_conversation_id,
            "branch_point_message_id": branch.branch_point_message_id,
            "branch_name": branch.branch_name,
            "branch_color": branch.branch_color,
            "is_archived": branch.is_archived,
            "is_pinned": branch.is_pinned,
            "message_count": branch.message_count,
            "token_count": branch.token_count,
            "created_at": branch.created_at.isoformat(),
            "updated_at": branch.updated_at.isoformat(),
        }
        for branch in branches
    ]


@router.get("/{conversation_id}/branch-tree")
async def get_branch_tree(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get the branch tree structure for a conversation."""
    # Get the conversation
    result = await db.execute(
        select(ConversationModel).where(ConversationModel.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Get all related conversations (parent and children)
    conversations_to_check = [conversation]
    current = conversation

    # Find root conversation
    while current.parent_conversation_id:
        result = await db.execute(
            select(ConversationModel).where(ConversationModel.id == current.parent_conversation_id)
        )
        parent = result.scalar_one_or_none()
        if parent:
            conversations_to_check.append(parent)
            current = parent
        else:
            break

    # Get all branches from all conversations in the tree
    all_conversations = []
    for conv in conversations_to_check:
        # Get branches for this conversation
        result = await db.execute(
            select(ConversationModel)
            .where(ConversationModel.parent_conversation_id == conv.id)
            .order_by(ConversationModel.created_at)
        )
        branches = result.scalars().all()
        all_conversations.extend(branches)

    # Build tree structure
    tree = {
        "root": {
            "id": current.id,
            "title": current.title,
            "model": current.model,
            "is_archived": current.is_archived,
            "is_pinned": current.is_pinned,
            "created_at": current.created_at.isoformat(),
        },
        "branches": [
            {
                "id": branch.id,
                "title": branch.title,
                "model": branch.model,
                "parent_conversation_id": branch.parent_conversation_id,
                "branch_point_message_id": branch.branch_point_message_id,
                "branch_name": branch.branch_name,
                "branch_color": branch.branch_color,
                "is_archived": branch.is_archived,
                "is_pinned": branch.is_pinned,
                "created_at": branch.created_at.isoformat(),
                "message_count": branch.message_count,
                "token_count": branch.token_count,
            }
            for branch in all_conversations
        ],
        "current_conversation": {
            "id": conversation.id,
            "title": conversation.title,
            "model": conversation.model,
            "is_archived": conversation.is_archived,
            "is_pinned": conversation.is_pinned,
            "created_at": conversation.created_at.isoformat(),
        }
    }

    return tree


@router.post("/upload-image")
async def upload_image(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Upload an image file and return a URL."""
    # Validate file type
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail="File must be an image"
        )

    # Create uploads directory if it doesn't exist
    uploads_dir = Path("static/uploads")
    uploads_dir.mkdir(parents=True, exist_ok=True)

    # Generate unique filename
    import uuid
    file_extension = Path(file.filename).suffix if file.filename else ".jpg"
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = uploads_dir / unique_filename

    # Save the file
    try:
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save file: {str(e)}"
        )

    # Return the URL
    file_url = f"/static/uploads/{unique_filename}"

    return {
        "filename": unique_filename,
        "url": file_url,
        "size": len(content),
        "content_type": file.content_type
    }
