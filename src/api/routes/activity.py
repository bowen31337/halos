"""Activity feed API endpoints for tracking and displaying user actions."""

from datetime import datetime, timedelta
from typing import Optional, List

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, desc, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.models.activity import ActivityLog

router = APIRouter()


# ==================== Request/Response Models ====================


class ActivityLogRequest(BaseModel):
    """Request model for logging an activity."""
    action_type: str = Field(..., description="Type of action performed")
    resource_type: Optional[str] = Field(None, description="Type of resource affected")
    resource_id: Optional[str] = Field(None, description="ID of resource affected")
    resource_name: Optional[str] = Field(None, description="Name of resource")
    details: Optional[dict] = Field(None, description="Additional context")
    ip_address: Optional[str] = Field(None, description="User IP address")
    user_agent: Optional[str] = Field(None, description="User agent string")


class ActivityLogResponse(BaseModel):
    """Response model for an activity log."""
    id: str
    user_id: str
    user_name: Optional[str]
    action_type: str
    resource_type: Optional[str]
    resource_id: Optional[str]
    resource_name: Optional[str]
    details: Optional[dict]
    created_at: str


class ActivityFeedResponse(BaseModel):
    """Response model for activity feed."""
    activities: List[ActivityLogResponse]
    total: int
    has_more: bool


# ==================== API Endpoints ====================


@router.post("", response_model=ActivityLogResponse, status_code=201)
async def log_activity(
    activity: ActivityLogRequest,
    user_id: str = Query(default="default-user", description="User ID making the request"),
    user_name: str = Query(default="Anonymous", description="User name for display"),
    db: AsyncSession = Depends(get_db),
) -> ActivityLogResponse:
    """Log a user activity."""
    log_entry = ActivityLog(
        user_id=user_id,
        user_name=user_name,
        action_type=activity.action_type,
        resource_type=activity.resource_type,
        resource_id=activity.resource_id,
        resource_name=activity.resource_name,
        details=activity.details,
        ip_address=activity.ip_address,
        user_agent=activity.user_agent,
    )

    db.add(log_entry)
    await db.commit()
    await db.refresh(log_entry)

    return log_entry.to_dict()


@router.get("", response_model=ActivityFeedResponse)
async def get_activity_feed(
    user_id: str = Query(default=None, description="Filter by user ID"),
    action_type: Optional[str] = Query(None, description="Filter by action type"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    time_range: str = Query("7d", description="Time range: 1d, 7d, 30d, all"),
    limit: int = Query(50, ge=1, le=100, description="Number of activities to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: AsyncSession = Depends(get_db),
) -> ActivityFeedResponse:
    """Get activity feed with optional filters."""
    # Calculate time range
    now = datetime.utcnow()
    time_filters = []

    if time_range == "1d":
        time_filters.append(ActivityLog.created_at >= now - timedelta(days=1))
    elif time_range == "7d":
        time_filters.append(ActivityLog.created_at >= now - timedelta(days=7))
    elif time_range == "30d":
        time_filters.append(ActivityLog.created_at >= now - timedelta(days=30))
    # "all" means no time filter

    # Build query
    query = select(ActivityLog).where(
        ActivityLog.is_deleted == False,
        *time_filters
    )

    # Apply filters
    if user_id:
        query = query.where(ActivityLog.user_id == user_id)
    if action_type:
        query = query.where(ActivityLog.action_type == action_type)
    if resource_type:
        query = query.where(ActivityLog.resource_type == resource_type)

    # Order by newest first
    query = query.order_by(desc(ActivityLog.created_at))

    # Apply pagination
    query = query.limit(limit + 1).offset(offset)

    result = await db.execute(query)
    activities = result.scalars().all()

    has_more = len(activities) > limit
    if has_more:
        activities = activities[:limit]

    return ActivityFeedResponse(
        activities=[activity.to_dict() for activity in activities],
        total=len(activities),
        has_more=has_more,
    )


@router.get("/types", response_model=dict)
async def get_activity_types(db: AsyncSession = Depends(get_db)) -> dict:
    """Get available activity types and their counts."""
    from sqlalchemy import func

    # Get distinct action types with counts
    query = select(
        ActivityLog.action_type,
        func.count(ActivityLog.id).label('count')
    ).where(
        ActivityLog.is_deleted == False
    ).group_by(
        ActivityLog.action_type
    ).order_by(
        desc('count')
    )

    result = await db.execute(query)
    types = [{"type": row[0], "count": row[1]} for row in result.all()]

    # Get distinct resource types with counts
    query = select(
        ActivityLog.resource_type,
        func.count(ActivityLog.id).label('count')
    ).where(
        ActivityLog.is_deleted == False,
        ActivityLog.resource_type.isnot(None)
    ).group_by(
        ActivityLog.resource_type
    ).order_by(
        desc('count')
    )

    result = await db.execute(query)
    resources = [{"type": row[0], "count": row[1]} for row in result.all()]

    return {
        "action_types": types,
        "resource_types": resources,
    }


@router.get("/summary", response_model=dict)
async def get_activity_summary(
    days: int = Query(7, ge=1, le=365, description="Number of days to summarize"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get activity summary statistics."""
    from sqlalchemy import func

    since = datetime.utcnow() - timedelta(days=days)

    # Total activities
    total_query = select(func.count(ActivityLog.id)).where(
        ActivityLog.is_deleted == False,
        ActivityLog.created_at >= since
    )
    total_result = await db.execute(total_query)
    total = total_result.scalar()

    # Activities by user
    by_user_query = select(
        ActivityLog.user_name,
        func.count(ActivityLog.id).label('count')
    ).where(
        ActivityLog.is_deleted == False,
        ActivityLog.created_at >= since
    ).group_by(
        ActivityLog.user_name
    ).order_by(
        desc('count')
    ).limit(10)

    result = await db.execute(by_user_query)
    by_user = [{"user": row[0], "count": row[1]} for row in result.all()]

    # Activities by type
    by_type_query = select(
        ActivityLog.action_type,
        func.count(ActivityLog.id).label('count')
    ).where(
        ActivityLog.is_deleted == False,
        ActivityLog.created_at >= since
    ).group_by(
        ActivityLog.action_type
    ).order_by(
        desc('count')
    )

    result = await db.execute(by_type_query)
    by_type = [{"type": row[0], "count": row[1]} for row in result.all()]

    return {
        "total": total,
        "period_days": days,
        "by_user": by_user,
        "by_type": by_type,
    }


@router.delete("/{activity_id}", status_code=204)
async def delete_activity(
    activity_id: str,
    user_id: str = Query(default="default-user"),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Soft delete an activity log."""
    query = select(ActivityLog).where(
        ActivityLog.id == activity_id,
        ActivityLog.user_id == user_id
    )
    result = await db.execute(query)
    activity = result.scalar_one_or_none()

    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    activity.is_deleted = True
    await db.commit()


# ==================== Utility Functions ====================


async def log_user_activity(
    db: AsyncSession,
    user_id: str,
    action_type: str,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    resource_name: Optional[str] = None,
    details: Optional[dict] = None,
    user_name: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> ActivityLog:
    """Utility function to log activity from other parts of the application."""
    log_entry = ActivityLog(
        user_id=user_id,
        user_name=user_name,
        action_type=action_type,
        resource_type=resource_type,
        resource_id=resource_id,
        resource_name=resource_name,
        details=details,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    db.add(log_entry)
    await db.commit()
    await db.refresh(log_entry)

    return log_entry
