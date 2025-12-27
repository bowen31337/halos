"""Audit logging endpoints."""

from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta

from src.core.database import get_db
from src.models.audit_log import AuditLog, AuditActionType
from src.utils.audit import get_audit_logs

router = APIRouter()


@router.get("")
async def list_audit_logs(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    action: Optional[str] = Query(None, description="Filter by action type"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    resource_id: Optional[str] = Query(None, description="Filter by resource ID"),
    tool_name: Optional[str] = Query(None, description="Filter by tool name"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """List audit logs with filtering and pagination.

    Returns audit trail of user actions for security and compliance monitoring.
    """
    # Convert action string to enum if provided
    action_enum = None
    if action:
        try:
            action_enum = AuditActionType(action)
        except ValueError:
            return {"logs": [], "count": 0, "limit": limit, "offset": offset}

    logs = await get_audit_logs(
        db=db,
        user_id=user_id,
        action=action_enum,
        resource_type=resource_type,
        resource_id=resource_id,
        tool_name=tool_name,
        limit=limit,
        offset=offset,
    )

    return {
        "logs": [log.to_dict() for log in logs],
        "count": len(logs),
        "limit": limit,
        "offset": offset,
    }


@router.get("/stats")
async def get_audit_stats(
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get audit statistics.

    Returns counts of actions by type and over time.
    """
    # Count by action
    action_counts = await db.execute(
        select(AuditLog.action, func.count(AuditLog.id))
        .group_by(AuditLog.action)
        .order_by(func.count(AuditLog.id).desc())
    )
    action_stats = [{"action": row[0], "count": row[1]} for row in action_counts.all()]

    # Count by resource type
    resource_counts = await db.execute(
        select(AuditLog.resource_type, func.count(AuditLog.id))
        .where(AuditLog.resource_type.isnot(None))
        .group_by(AuditLog.resource_type)
        .order_by(func.count(AuditLog.id).desc())
    )
    resource_stats = [{"resource_type": row[0], "count": row[1]} for row in resource_counts.all()]

    # Total count
    total_count = await db.execute(select(func.count(AuditLog.id)))
    total = total_count.scalar() or 0

    # Recent activity (last 24 hours)
    yesterday = datetime.utcnow() - timedelta(hours=24)
    recent_count = await db.execute(
        select(func.count(AuditLog.id))
        .where(AuditLog.created_at >= yesterday)
    )
    recent = recent_count.scalar() or 0

    return {
        "total": total,
        "recent_24h": recent,
        "by_action": action_stats,
        "by_resource": resource_stats,
    }


@router.get("/actions")
async def list_audit_actions() -> dict:
    """List all available audit action types.

    Returns the complete list of action types that can be audited.
    """
    return {
        "actions": [action.value for action in AuditActionType]
    }


@router.get("/user/{user_id}")
async def get_user_audit_logs(
    user_id: str,
    action: Optional[str] = Query(None, description="Filter by action type"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get audit logs for a specific user.

    Useful for user activity monitoring and security reviews.
    """
    action_enum = None
    if action:
        try:
            action_enum = AuditActionType(action)
        except ValueError:
            return {"user_id": user_id, "logs": [], "count": 0}

    logs = await get_audit_logs(
        db=db,
        user_id=user_id,
        action=action_enum,
        resource_type=resource_type,
        limit=limit,
        offset=offset,
    )

    return {
        "user_id": user_id,
        "logs": [log.to_dict() for log in logs],
        "count": len(logs),
    }


@router.get("/resource/{resource_type}/{resource_id}")
async def get_resource_audit_logs(
    resource_type: str,
    resource_id: str,
    action: Optional[str] = Query(None, description="Filter by action type"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get audit logs for a specific resource.

    Useful for tracking the history of a conversation, project, or other resource.
    """
    action_enum = None
    if action:
        try:
            action_enum = AuditActionType(action)
        except ValueError:
            return {"resource_type": resource_type, "resource_id": resource_id, "logs": [], "count": 0}

    logs = await get_audit_logs(
        db=db,
        action=action_enum,
        resource_type=resource_type,
        resource_id=resource_id,
        limit=limit,
        offset=offset,
    )

    return {
        "resource_type": resource_type,
        "resource_id": resource_id,
        "logs": [log.to_dict() for log in logs],
        "count": len(logs),
    }
