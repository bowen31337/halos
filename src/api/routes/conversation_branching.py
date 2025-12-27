"""Conversation branching API endpoints."""

from typing import List

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from datetime import datetime

from src.core.database import get_db
from src.models.conversation import Conversation
from src.models.message import Message
from src.utils import generate_thread_id

router = APIRouter(prefix="/api/conversations", tags=["conversation-branching"])


@router.post("/{conversation_id}/branch")
async def create_conversation_branch(
    conversation_id: str,
    branch_point_message_id: str,
    branch_name: str = None,
    branch_color: str = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new conversation branch from a specific message.

    Args:
        conversation_id: ID of the parent conversation
        branch_point_message_id: ID of the message to branch from
        branch_name: Optional name for the branch
        branch_color: Optional color for the branch
        db: Database session

    Returns:
        New conversation with branch information
    """
    # Get the parent conversation
    parent_conversation = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    parent_conversation = parent_conversation.scalar_one_or_none()

    if not parent_conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parent conversation not found"
        )

    # Get the branch point message
    branch_point_message = await db.execute(
        select(Message).where(
            Message.id == branch_point_message_id,
            Message.conversation_id == conversation_id
        )
    )
    branch_point_message = branch_point_message.scalar_one_or_none()

    if not branch_point_message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Branch point message not found"
        )

    # Generate branch name if not provided
    if not branch_name:
        branch_name = f"Branch from {branch_point_message.content[:30]}..."

    # Generate branch color if not provided
    if not branch_color:
        branch_color = "#ff6b6b"  # Default red color

    # Create new conversation for the branch
    new_conversation = Conversation(
        user_id=parent_conversation.user_id,
        title=f"{parent_conversation.title} - {branch_name}",
        model=parent_conversation.model,
        project_id=parent_conversation.project_id,
        parent_conversation_id=conversation_id,
        branch_point_message_id=branch_point_message_id,
        branch_name=branch_name,
        branch_color=branch_color,
        thread_id=generate_thread_id(),
        extended_thinking_enabled=parent_conversation.extended_thinking_enabled
    )

    db.add(new_conversation)
    await db.commit()
    await db.refresh(new_conversation)

    # Copy messages up to the branch point
    messages_query = await db.execute(
        select(Message).where(
            Message.conversation_id == conversation_id,
            Message.created_at <= branch_point_message.created_at
        ).order_by(Message.created_at)
    )
    messages_to_copy = messages_query.scalars().all()

    for message in messages_to_copy:
        new_message = Message(
            conversation_id=new_conversation.id,
            role=message.role,
            content=message.content,
            input_tokens=message.input_tokens,
            output_tokens=message.output_tokens,
            cache_read_tokens=message.cache_read_tokens,
            cache_write_tokens=message.cache_write_tokens,
            attachments=message.attachments,
            tool_calls=message.tool_calls,
            tool_results=message.tool_results,
            thinking_content=message.thinking_content,
            parent_message_id=message.id,
            is_branch_point=message.id == branch_point_message_id
        )
        db.add(new_message)

    await db.commit()

    return {
        "message": "Conversation branch created successfully",
        "conversation": {
            "id": new_conversation.id,
            "title": new_conversation.title,
            "branch_name": new_conversation.branch_name,
            "branch_color": new_conversation.branch_color,
            "parent_conversation_id": new_conversation.parent_conversation_id,
            "branch_point_message_id": new_conversation.branch_point_message_id,
            "created_at": new_conversation.created_at.isoformat() if new_conversation.created_at else None,
        },
        "branch_point_message_id": branch_point_message_id
    }


@router.get("/{conversation_id}/branches")
async def get_conversation_branches(
    conversation_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get all branches for a conversation.

    Args:
        conversation_id: ID of the parent conversation
        db: Database session

    Returns:
        List of branch conversations
    """
    branches_query = await db.execute(
        select(Conversation).where(
            Conversation.parent_conversation_id == conversation_id
        ).order_by(Conversation.created_at)
    )
    branches = branches_query.scalars().all()

    return {
        "parent_conversation_id": conversation_id,
        "branches": branches,
        "count": len(branches)
    }


@router.get("/{conversation_id}/branch-history")
async def get_conversation_branch_history(
    conversation_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get the complete branch history for a conversation.

    Args:
        conversation_id: ID of the conversation
        db: Database session

    Returns:
        Complete branch history
    """
    # Get the conversation
    conversation = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conversation = conversation.scalar_one_or_none()

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )

    # Build branch history
    branch_history = []
    current = conversation

    while current:
        branch_history.append({
            "id": current.id,
            "title": current.title,
            "branch_name": current.branch_name,
            "branch_color": current.branch_color,
            "parent_conversation_id": current.parent_conversation_id,
            "branch_point_message_id": current.branch_point_message_id,
            "created_at": current.created_at,
            "is_current": current.id == conversation_id
        })
        if current.parent_conversation_id:
            current = await db.execute(
                select(Conversation).where(
                    Conversation.id == current.parent_conversation_id
                )
            )
            current = current.scalar_one_or_none()
        else:
            current = None

    # Reverse to show from root to current
    branch_history.reverse()

    return {
        "branch_history": branch_history,
        "current_branch_depth": len(branch_history)
    }


@router.get("/{conversation_id}/branch-path")
async def get_conversation_branch_path(
    conversation_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get the path from root conversation to current branch.

    Args:
        conversation_id: ID of the conversation
        db: Database session

    Returns:
        Path from root to current conversation
    """
    # Get the conversation
    conversation = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conversation = conversation.scalar_one_or_none()

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )

    # Build path
    path = []
    current = conversation

    while current:
        path.append({
            "id": current.id,
            "title": current.title,
            "branch_name": current.branch_name,
            "branch_color": current.branch_color,
            "model": current.model,
            "created_at": current.created_at
        })
        if current.parent_conversation_id:
            current = await db.execute(
                select(Conversation).where(
                    Conversation.id == current.parent_conversation_id
                )
            )
            current = current.scalar_one_or_none()
        else:
            current = None

    # Reverse to show from root to current
    path.reverse()

    return {
        "branch_path": path,
        "is_branch": len(path) > 1,
        "root_conversation_id": path[0]["id"] if path else None
    }


@router.put("/{conversation_id}/switch-to-branch/{target_conversation_id}")
async def switch_to_branch(
    conversation_id: str,
    target_conversation_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Switch the current conversation to a different branch.

    Args:
        conversation_id: ID of the current conversation
        target_conversation_id: ID of the target branch conversation
        db: Database session

    Returns:
        Success message with branch information
    """
    # Verify both conversations exist
    current_conversation = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    current_conversation = current_conversation.scalar_one_or_none()

    target_conversation = await db.execute(
        select(Conversation).where(Conversation.id == target_conversation_id)
    )
    target_conversation = target_conversation.scalar_one_or_none()

    if not current_conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Current conversation not found"
        )

    if not target_conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target conversation not found"
        )

    # Verify they share the same root
    current_path = await get_branch_path_for_switch(current_conversation, db)
    target_path = await get_branch_path_for_switch(target_conversation, db)

    if current_path[0]["id"] != target_path[0]["id"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot switch between conversations with different roots"
        )

    # Update the current conversation to point to the target
    await db.execute(
        update(Conversation)
        .where(Conversation.id == conversation_id)
        .values(
            parent_conversation_id=target_conversation.parent_conversation_id,
            branch_point_message_id=target_conversation.branch_point_message_id,
            branch_name=target_conversation.branch_name,
            branch_color=target_conversation.branch_color
        )
    )

    await db.commit()

    return {
        "message": "Switched to branch successfully",
        "target_conversation": {
            "id": target_conversation.id,
            "title": target_conversation.title,
            "branch_name": target_conversation.branch_name,
            "branch_color": target_conversation.branch_color,
            "parent_conversation_id": target_conversation.parent_conversation_id,
            "branch_point_message_id": target_conversation.branch_point_message_id,
        },
        "switched_from": conversation_id,
        "switched_to": target_conversation_id
    }


async def get_branch_path_for_switch(conversation: Conversation, db: AsyncSession):
    """Helper function to get branch path for switching logic."""
    path = []
    current = conversation

    while current:
        path.append({
            "id": current.id,
            "title": current.title,
            "branch_name": current.branch_name,
            "branch_color": current.branch_color,
            "model": current.model,
            "created_at": current.created_at
        })
        if current.parent_conversation_id:
            current = await db.execute(
                select(Conversation).where(
                    Conversation.id == current.parent_conversation_id
                )
            )
            current = current.scalar_one_or_none()
        else:
            current = None

    path.reverse()
    return path