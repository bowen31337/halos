"""Background Tasks API endpoints.

This module provides endpoints for tracking and managing long-running background tasks.
"""

import asyncio
import json
from typing import Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from src.core.database import get_db
from src.models.background_task import BackgroundTask, TaskStatus
from sse_starlette.sse import EventSourceResponse

router = APIRouter()

# In-memory task store for simulating task execution
# In production, this would use a proper task queue like Celery or Redis
active_tasks: dict[str, asyncio.Task] = {}


class TaskCreateRequest:
    """Request model for creating a background task."""
    pass


@router.get("")
async def list_tasks(
    db: AsyncSession = Depends(get_db),
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
) -> dict:
    """List background tasks.

    Query parameters:
    - status: Filter by status (pending, running, completed, failed, cancelled)
    - limit: Maximum number of tasks to return (default: 50)
    - offset: Number of tasks to skip (default: 0)

    Returns:
        List of background tasks
    """
    query = select(BackgroundTask).order_by(desc(BackgroundTask.created_at))

    if status:
        try:
            task_status = TaskStatus(status)
            query = query.where(BackgroundTask.status == task_status)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")

    query = query.limit(limit).offset(offset)
    result = await db.execute(query)
    tasks = result.scalars().all()

    return {
        "tasks": [task.to_dict() for task in tasks],
        "total": len(tasks),
        "limit": limit,
        "offset": offset,
    }


@router.post("")
async def create_task(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Create a new background task.

    This endpoint simulates triggering a long-running operation.
    In production, this would integrate with a proper task queue.

    Body:
        - task_type: Type of task (e.g., "agent_invocation", "export", "file_processing")
        - conversation_id: Optional conversation ID associated with the task
        - subagent_name: Optional sub-agent name if this is a delegated task

    Returns:
        Created task details
    """
    data = await request.json()
    task_type = data.get("task_type", "generic")
    conversation_id = data.get("conversation_id")
    subagent_name = data.get("subagent_name")

    # Create task record
    task = BackgroundTask(
        user_id="default",  # In production, get from auth
        conversation_id=UUID(conversation_id) if conversation_id else None,
        task_type=task_type,
        subagent_name=subagent_name,
        status=TaskStatus.PENDING,
        progress=0,
    )

    db.add(task)
    await db.commit()
    await db.refresh(task)

    # Start simulated task execution
    asyncio.create_task(simulate_task_execution(task.id, db))

    return task.to_dict()


@router.get("/{task_id}")
async def get_task(
    task_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Get a specific background task by ID.

    Returns:
        Task details
    """
    result = await db.execute(
        select(BackgroundTask).where(BackgroundTask.id == task_id)
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return task.to_dict()


@router.put("/{task_id}/cancel")
async def cancel_task(
    task_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Cancel a running or pending task.

    Returns:
        Updated task details
    """
    result = await db.execute(
        select(BackgroundTask).where(BackgroundTask.id == task_id)
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
        raise HTTPException(status_code=400, detail="Task cannot be cancelled in its current state")

    # Cancel the asyncio task if it exists
    if str(task_id) in active_tasks:
        active_tasks[str(task_id)].cancel()
        del active_tasks[str(task_id)]

    # Update task status
    task.mark_cancelled()
    await db.commit()
    await db.refresh(task)

    return task.to_dict()


@router.get("/{task_id}/stream")
async def stream_task_updates(
    task_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> EventSourceResponse:
    """Stream task progress updates via Server-Sent Events.

    Returns:
        SSE stream of task updates
    """
    async def event_generator():
        last_status = None
        last_progress = -1

        while True:
            # Fetch current task state from database
            result = await db.execute(
                select(BackgroundTask).where(BackgroundTask.id == task_id)
            )
            task = result.scalar_one_or_none()

            if not task:
                yield {
                    "event": "error",
                    "data": json.dumps({"error": "Task not found"})
                }
                break

            # Only emit if status or progress changed
            if task.status != last_status or task.progress != last_progress:
                last_status = task.status
                last_progress = task.progress

                yield {
                    "event": "update",
                    "data": json.dumps(task.to_dict())
                }

                # End stream if task is complete
                if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
                    yield {
                        "event": "done",
                        "data": json.dumps(task.to_dict())
                    }
                    break

            # Check every 0.5 seconds
            await asyncio.sleep(0.5)

    return EventSourceResponse(event_generator())


@router.post("/{task_id}/retry")
async def retry_task(
    task_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Retry a failed task.

    Creates a new task with the same parameters, incrementing the retry count.
    Implements exponential backoff for retry delays.

    Returns:
        New task details
    """
    # Get original task
    result = await db.execute(
        select(BackgroundTask).where(BackgroundTask.id == task_id)
    )
    original_task = result.scalar_one_or_none()

    if not original_task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Check if task can be retried
    if not original_task.can_retry():
        raise HTTPException(
            status_code=400,
            detail=f"Task cannot be retried. Status: {original_task.status.value}, Retries: {original_task.retry_count}/{original_task.max_retries}"
        )

    # Create retry task
    retry_task = original_task.create_retry_task()
    db.add(retry_task)
    await db.commit()
    await db.refresh(retry_task)

    # Calculate delay with exponential backoff
    delay = original_task.retry_delay_seconds * (2 ** original_task.retry_count)

    # Start task execution after delay
    async def delayed_execution():
        await asyncio.sleep(delay)
        asyncio.create_task(simulate_task_execution(retry_task.id, db))

    asyncio.create_task(delayed_execution())

    return {
        "original_task_id": str(original_task.id),
        "retry_task_id": str(retry_task.id),
        "retry_attempt": retry_task.retry_count,
        "max_retries": retry_task.max_retries,
        "delay_seconds": delay,
        "task": retry_task.to_dict()
    }


async def simulate_task_execution(task_id: UUID, db: AsyncSession):
    """Simulate a long-running task with progress updates.

    This function simulates work being done over time, updating the task's
    progress and status in the database.
    """
    try:
        # Get task from database
        result = await db.execute(
            select(BackgroundTask).where(BackgroundTask.id == task_id)
        )
        task = result.scalar_one_or_none()

        if not task:
            return

        # Mark as running
        task.mark_running()
        await db.commit()

        # Store task in active tasks
        active_tasks[str(task_id)] = asyncio.current_task()

        # Simulate progress updates
        for progress in [10, 25, 50, 75, 90]:
            await asyncio.sleep(0.5)  # Simulate work

            # Check if task was cancelled
            result = await db.execute(
                select(BackgroundTask).where(BackgroundTask.id == task_id)
            )
            task = result.scalar_one_or_none()
            if not task or task.status == TaskStatus.CANCELLED:
                return

            task.update_progress(progress, TaskStatus.RUNNING)
            await db.commit()

        # Complete the task
        await asyncio.sleep(0.3)
        task.mark_completed({
            "message": "Task completed successfully",
            "output": "Simulated task output"
        })
        await db.commit()

    except asyncio.CancelledError:
        # Task was cancelled
        result = await db.execute(
            select(BackgroundTask).where(BackgroundTask.id == task_id)
        )
        task = result.scalar_one_or_none()
        if task:
            task.mark_cancelled()
            await db.commit()
    except Exception as e:
        # Mark as failed
        result = await db.execute(
            select(BackgroundTask).where(BackgroundTask.id == task_id)
        )
        task = result.scalar_one_or_none()
        if task:
            task.mark_failed(str(e))
            await db.commit()
    finally:
        # Clean up
        if str(task_id) in active_tasks:
            del active_tasks[str(task_id)]
