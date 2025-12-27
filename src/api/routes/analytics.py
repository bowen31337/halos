"""Analytics endpoints for project usage statistics."""

from typing import Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, case
from fastapi import APIRouter, Depends, HTTPException

from src.core.database import get_db
from src.models.usage_tracking import UsageTracking
from src.models.conversation import Conversation
from src.models.message import Message
from src.models.project import Project

router = APIRouter()


@router.get("/projects/{project_id}")
async def get_project_analytics(
    project_id: str,
    days: Optional[int] = 30,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get usage analytics for a specific project."""
    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    # Get project
    project_result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = project_result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Get usage stats
    usage_result = await db.execute(
        select(
            func.count(UsageTracking.id).label('total_requests'),
            func.sum(UsageTracking.input_tokens).label('total_input_tokens'),
            func.sum(UsageTracking.output_tokens).label('total_output_tokens'),
            func.sum(UsageTracking.input_tokens + UsageTracking.output_tokens).label('total_tokens'),
            func.avg(UsageTracking.input_tokens + UsageTracking.output_tokens).label('avg_tokens_per_request'),
        )
        .where(UsageTracking.project_id == project_id)
        .where(UsageTracking.created_at >= start_date)
    )
    usage_stats = usage_result.one()

    # Get conversation stats
    conv_result = await db.execute(
        select(
            func.count(Conversation.id).label('total_conversations'),
            func.sum(
                case(
                    (Conversation.is_pinned == True, 1),
                    else_=0
                )
            ).label('pinned_conversations'),
        )
        .where(Conversation.project_id == project_id)
        .where(Conversation.created_at >= start_date)
    )
    conv_stats = conv_result.one()

    # Get message stats
    msg_result = await db.execute(
        select(
            func.count(Message.id).label('total_messages'),
            func.sum(
                case(
                    (Message.role == 'user', 1),
                    else_=0
                )
            ).label('user_messages'),
            func.sum(
                case(
                    (Message.role == 'assistant', 1),
                    else_=0
                )
            ).label('assistant_messages'),
        )
        .select_from(Message)
        .join(Conversation, Conversation.id == Message.conversation_id)
        .where(Conversation.project_id == project_id)
        .where(Message.created_at >= start_date)
    )
    msg_stats = msg_result.one()

    # Get daily usage (for charts)
    daily_result = await db.execute(
        select(
            func.date(UsageTracking.created_at).label('date'),
            func.count(UsageTracking.id).label('requests'),
            func.sum(UsageTracking.input_tokens + UsageTracking.output_tokens).label('tokens'),
        )
        .where(UsageTracking.project_id == project_id)
        .where(UsageTracking.created_at >= start_date)
        .group_by(func.date(UsageTracking.created_at))
        .order_by(func.date(UsageTracking.created_at))
    )
    daily_usage = [
        {
            "date": str(row.date),
            "requests": row.requests,
            "tokens": row.tokens or 0,
        }
        for row in daily_result
    ]

    # Get model breakdown
    model_result = await db.execute(
        select(
            UsageTracking.model,
            func.count(UsageTracking.id).label('count'),
            func.sum(UsageTracking.input_tokens + UsageTracking.output_tokens).label('tokens'),
        )
        .where(UsageTracking.project_id == project_id)
        .where(UsageTracking.created_at >= start_date)
        .group_by(UsageTracking.model)
        .order_by(func.sum(UsageTracking.input_tokens + UsageTracking.output_tokens).desc())
    )
    model_usage = [
        {
            "model": row.model,
            "count": row.count,
            "tokens": row.tokens or 0,
        }
        for row in model_result
    ]

    return {
        "project_id": project_id,
        "project_name": project.name,
        "period": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
            "days": days,
        },
        "usage": {
            "total_requests": usage_stats.total_requests or 0,
            "total_tokens": usage_stats.total_tokens or 0,
            "total_input_tokens": usage_stats.total_input_tokens or 0,
            "total_output_tokens": usage_stats.total_output_tokens or 0,
            "avg_tokens_per_request": round(usage_stats.avg_tokens_per_request or 0, 2),
        },
        "conversations": {
            "total": conv_stats.total_conversations or 0,
            "pinned": conv_stats.pinned_conversations or 0,
        },
        "messages": {
            "total": msg_stats.total_messages or 0,
            "user": msg_stats.user_messages or 0,
            "assistant": msg_stats.assistant_messages or 0,
        },
        "daily_usage": daily_usage,
        "by_model": model_usage,
    }


@router.get("/overview")
async def get_analytics_overview(
    days: Optional[int] = 30,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get overall analytics overview across all projects."""
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    # Total usage
    usage_result = await db.execute(
        select(
            func.count(UsageTracking.id).label('total_requests'),
            func.sum(UsageTracking.input_tokens).label('total_input_tokens'),
            func.sum(UsageTracking.output_tokens).label('total_output_tokens'),
            func.sum(UsageTracking.input_tokens + UsageTracking.output_tokens).label('total_tokens'),
        )
        .where(UsageTracking.created_at >= start_date)
    )
    usage_stats = usage_result.one()

    # Active projects
    project_result = await db.execute(
        select(
            func.count(func.distinct(UsageTracking.project_id)).label('active_projects'),
        )
        .where(UsageTracking.created_at >= start_date)
    )
    active_projects = project_result.scalar() or 0

    # Total conversations
    conv_result = await db.execute(
        select(func.count(Conversation.id))
        .where(Conversation.created_at >= start_date)
    )
    total_conversations = conv_result.scalar() or 0

    # Total messages
    msg_result = await db.execute(
        select(func.count(Message.id))
        .where(Message.created_at >= start_date)
    )
    total_messages = msg_result.scalar() or 0

    # Top projects by usage
    top_projects_result = await db.execute(
        select(
            UsageTracking.project_id,
            Project.name,
            func.count(UsageTracking.id).label('requests'),
            func.sum(UsageTracking.input_tokens + UsageTracking.output_tokens).label('tokens'),
        )
        .join(Project, Project.id == UsageTracking.project_id)
        .where(UsageTracking.created_at >= start_date)
        .group_by(UsageTracking.project_id, Project.name)
        .order_by(func.sum(UsageTracking.input_tokens + UsageTracking.output_tokens).desc())
        .limit(10)
    )
    top_projects = [
        {
            "project_id": row.project_id,
            "project_name": row.name,
            "requests": row.requests,
            "tokens": row.tokens or 0,
        }
        for row in top_projects_result
    ]

    return {
        "period": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
            "days": days,
        },
        "overview": {
            "total_requests": usage_stats.total_requests or 0,
            "total_tokens": usage_stats.total_tokens or 0,
            "active_projects": active_projects,
            "total_conversations": total_conversations,
            "total_messages": total_messages,
        },
        "top_projects": top_projects,
    }


@router.get("/usage/daily")
async def get_daily_usage(
    project_id: Optional[str] = None,
    days: Optional[int] = 30,
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """Get daily usage statistics."""
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    query = select(
        func.date(UsageTracking.created_at).label('date'),
        func.count(UsageTracking.id).label('requests'),
        func.sum(UsageTracking.input_tokens).label('input_tokens'),
        func.sum(UsageTracking.output_tokens).label('output_tokens'),
        func.sum(UsageTracking.input_tokens + UsageTracking.output_tokens).label('total_tokens'),
        func.count(func.distinct(UsageTracking.conversation_id)).label('conversations'),
    )

    if project_id:
        query = query.where(UsageTracking.project_id == project_id)

    query = query.where(UsageTracking.created_at >= start_date)
    query = query.group_by(func.date(UsageTracking.created_at))
    query = query.order_by(func.date(UsageTracking.created_at))

    result = await db.execute(query)

    return [
        {
            "date": str(row.date),
            "requests": row.requests,
            "input_tokens": row.input_tokens or 0,
            "output_tokens": row.output_tokens or 0,
            "total_tokens": row.total_tokens or 0,
            "conversations": row.conversations,
        }
        for row in result
    ]


@router.get("/models")
async def get_model_usage(
    project_id: Optional[str] = None,
    days: Optional[int] = 30,
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """Get usage breakdown by model."""
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    query = select(
        UsageTracking.model,
        func.count(UsageTracking.id).label('requests'),
        func.sum(UsageTracking.input_tokens).label('input_tokens'),
        func.sum(UsageTracking.output_tokens).label('output_tokens'),
        func.sum(UsageTracking.input_tokens + UsageTracking.output_tokens).label('total_tokens'),
        func.avg(UsageTracking.input_tokens + UsageTracking.output_tokens).label('avg_tokens'),
    )

    if project_id:
        query = query.where(UsageTracking.project_id == project_id)

    query = query.where(UsageTracking.created_at >= start_date)
    query = query.group_by(UsageTracking.model)
    query = query.order_by(func.sum(UsageTracking.input_tokens + UsageTracking.output_tokens).desc())

    result = await db.execute(query)

    return [
        {
            "model": row.model,
            "requests": row.requests,
            "input_tokens": row.input_tokens or 0,
            "output_tokens": row.output_tokens or 0,
            "total_tokens": row.total_tokens or 0,
            "avg_tokens": round(row.avg_tokens or 0, 2),
        }
        for row in result
    ]
