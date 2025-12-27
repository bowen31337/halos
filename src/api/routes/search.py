"""Search endpoints."""

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func
from fastapi import APIRouter, Depends

from src.core.database import get_db
from src.models.project_file import ProjectFile
from src.models.conversation import Conversation
from src.models.message import Message
from src.models.memory import Memory

router = APIRouter()


@router.get("/conversations")
async def search_conversations(
    q: str,
    project_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """Search conversations by title and content."""
    if not q or len(q.strip()) < 2:
        return []

    query = (
        select(Conversation)
        .where(
            or_(
                Conversation.title.ilike(f"%{q}%"),
                Conversation.id.in_(
                    select(Message.conversation_id)
                    .where(Message.content.ilike(f"%{q}%"))
                )
            )
        )
        .where(Conversation.is_deleted == False)
        .order_by(Conversation.updated_at.desc())
        .limit(20)
    )

    if project_id:
        query = query.where(Conversation.project_id == project_id)

    result = await db.execute(query)
    conversations = result.scalars().all()

    return [
        {
            "id": conv.id,
            "title": conv.title,
            "project_id": conv.project_id,
            "updated_at": conv.updated_at.isoformat() if conv.updated_at else None,
        }
        for conv in conversations
    ]


@router.get("/messages")
async def search_messages(
    q: str,
    conversation_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """Search messages by content."""
    if not q or len(q.strip()) < 2:
        return []

    query = (
        select(Message)
        .where(Message.content.ilike(f"%{q}%"))
        .order_by(Message.created_at.desc())
        .limit(50)
    )

    if conversation_id:
        query = query.where(Message.conversation_id == conversation_id)

    result = await db.execute(query)
    messages = result.scalars().all()

    return [
        {
            "id": msg.id,
            "conversation_id": msg.conversation_id,
            "content": msg.content[:200] + "..." if msg.content and len(msg.content) > 200 else msg.content,
            "role": msg.role,
            "created_at": msg.created_at.isoformat() if msg.created_at else None,
        }
        for msg in messages
    ]


@router.get("/files")
async def search_files(
    q: str,
    project_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """Search files in project knowledge base."""
    if not q or len(q.strip()) < 2:
        return []

    # Search in filename and extracted content
    query = (
        select(ProjectFile)
        .where(
            or_(
                ProjectFile.filename.ilike(f"%{q}%"),
                ProjectFile.content.ilike(f"%{q}%"),
            )
        )
        .where(ProjectFile.is_deleted == False)
        .order_by(ProjectFile.updated_at.desc())
        .limit(20)
    )

    if project_id:
        query = query.where(ProjectFile.project_id == project_id)

    result = await db.execute(query)
    files = result.scalars().all()

    return [
        {
            "id": f.id,
            "filename": f.filename,
            "project_id": f.project_id,
            "file_size": f.file_size,
            "content_type": f.content_type,
            "content_preview": f.content[:200] + "..." if f.content and len(f.content) > 200 else f.content,
            "created_at": f.created_at.isoformat() if f.created_at else None,
        }
        for f in files
    ]


@router.get("/knowledge")
async def search_knowledge_base(
    q: str,
    project_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Search project knowledge base (files, documents, and extracted content)."""
    if not q or len(q.strip()) < 2:
        return {"files": [], "total": 0}

    # Search in project files
    files_query = (
        select(ProjectFile)
        .where(
            or_(
                ProjectFile.filename.ilike(f"%{q}%"),
                ProjectFile.content.ilike(f"%{q}%"),
            )
        )
        .where(ProjectFile.is_deleted == False)
    )

    if project_id:
        files_query = files_query.where(ProjectFile.project_id == project_id)

    # Get total count
    count_query = select(func.count()).select_from(files_query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Get paginated results
    files_query = files_query.order_by(ProjectFile.updated_at.desc()).limit(20)
    files_result = await db.execute(files_query)
    files = files_result.scalars().all()

    return {
        "files": [
            {
                "id": f.id,
                "filename": f.filename,
                "project_id": f.project_id,
                "file_size": f.file_size,
                "content_type": f.content_type,
                "content_preview": f.content[:300] + "..." if f.content and len(f.content) > 300 else f.content,
                "created_at": f.created_at.isoformat() if f.created_at else None,
                "updated_at": f.updated_at.isoformat() if f.updated_at else None,
            }
            for f in files
        ],
        "total": total,
        "query": q,
    }


@router.get("/global")
async def global_search(
    q: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Search across all content types."""
    if not q or len(q.strip()) < 2:
        return {
            "conversations": [],
            "messages": [],
            "files": [],
            "memories": [],
        }

    # Search conversations
    conv_result = await db.execute(
        select(Conversation)
        .where(Conversation.title.ilike(f"%{q}%"))
        .where(Conversation.is_deleted == False)
        .limit(10)
    )
    conversations = conv_result.scalars().all()

    # Search messages
    msg_result = await db.execute(
        select(Message)
        .where(Message.content.ilike(f"%{q}%"))
        .order_by(Message.created_at.desc())
        .limit(10)
    )
    messages = msg_result.scalars().all()

    # Search files
    file_result = await db.execute(
        select(ProjectFile)
        .where(
            or_(
                ProjectFile.filename.ilike(f"%{q}%"),
                ProjectFile.content.ilike(f"%{q}%"),
            )
        )
        .where(ProjectFile.is_deleted == False)
        .limit(10)
    )
    files = file_result.scalars().all()

    # Search memories
    mem_result = await db.execute(
        select(Memory)
        .where(Memory.content.ilike(f"%{q}%"))
        .where(Memory.is_active == True)
        .limit(10)
    )
    memories = mem_result.scalars().all()

    return {
        "conversations": [
            {
                "id": c.id,
                "title": c.title,
                "project_id": c.project_id,
                "updated_at": c.updated_at.isoformat() if c.updated_at else None,
            }
            for c in conversations
        ],
        "messages": [
            {
                "id": m.id,
                "conversation_id": m.conversation_id,
                "content": m.content[:200] + "..." if m.content and len(m.content) > 200 else m.content,
                "role": m.role,
                "created_at": m.created_at.isoformat() if m.created_at else None,
            }
            for m in messages
        ],
        "files": [
            {
                "id": f.id,
                "filename": f.filename,
                "project_id": f.project_id,
                "content_preview": f.content[:200] + "..." if f.content and len(f.content) > 200 else f.content,
            }
            for f in files
        ],
        "memories": [
            {
                "id": m.id,
                "content": m.content[:200] + "..." if m.content and len(m.content) > 200 else m.content,
                "category": m.category,
            }
            for m in memories
        ],
    }
