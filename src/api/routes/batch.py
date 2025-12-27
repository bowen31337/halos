"""Batch operations endpoints for handling multiple requests at once."""

import json
from typing import List, Optional, Literal, Any
from uuid import UUID
from datetime import datetime
from pathlib import Path
import asyncio
from zipfile import ZipFile
import io

from fastapi import APIRouter, HTTPException, status, Depends, BackgroundTasks
from fastapi.responses import Response, FileResponse
from pydantic import BaseModel, Field
from sqlalchemy import select, func, distinct
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.models import Conversation as ConversationModel, Message as MessageModel, Tag, conversation_tags
from src.utils.audit import log_audit, get_request_info
from src.models.audit_log import AuditActionType as AuditAction

router = APIRouter()


class BatchOperationRequest(BaseModel):
    """Request model for batch operations."""

    conversation_ids: List[UUID] = Field(..., description="List of conversation IDs to process")
    operation: Literal["export", "delete", "archive", "unarchive", "pin", "unpin", "move"] = Field(
        ..., description="Operation to perform on all conversations"
    )
    # Optional parameters for specific operations
    project_id: Optional[UUID] = Field(None, description="Target project ID for move operations")
    export_format: Literal["json", "markdown", "csv"] = Field(
        "json", description="Format for export operations"
    )


class BatchOperationResponse(BaseModel):
    """Response model for batch operations."""

    success: bool
    operation: str
    total_requested: int
    total_processed: int
    successful: List[UUID]
    failed: List[tuple[UUID, str]]  # (conversation_id, error_message)
    started_at: datetime
    completed_at: datetime
    processing_time_seconds: float


class BatchExportResult(BaseModel):
    """Result of a batch export operation."""

    success: bool
    operation: str
    total_requested: int
    total_exported: int
    export_format: str
    file_url: Optional[str] = None
    file_data: Optional[str] = None  # Base64 encoded for small exports
    successful: List[UUID]
    failed: List[tuple[UUID, str]]
    started_at: datetime
    completed_at: datetime
    processing_time_seconds: float


@router.post("/api/batch/conversations", response_model=BatchOperationResponse)
@router.post("/conversations/batch/delete", response_model=BatchOperationResponse)  # Frontend compatibility
@router.post("/conversations/batch/archive", response_model=BatchOperationResponse)  # Frontend compatibility
async def batch_conversation_operations(
    request: BatchOperationRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Perform batch operations on multiple conversations.

    Supported operations:
    - export: Export multiple conversations (returns bundled data)
    - delete: Delete multiple conversations with confirmation
    - archive: Archive multiple conversations
    - unarchive: Unarchive multiple conversations
    - pin: Pin multiple conversations
    - unpin: Unpin multiple conversations
    - move: Move multiple conversations to a project

    Returns a summary of the operation including success/failure counts.
    """
    started_at = datetime.now()
    successful = []
    failed = []

    if not request.conversation_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one conversation ID is required"
        )

    # Verify all conversations exist
    conversations_query = select(ConversationModel).where(
        ConversationModel.id.in_(request.conversation_ids)
    )
    result = await db.execute(conversations_query)
    conversations = result.scalars().all()
    conversation_map = {conv.id: conv for conv in conversations}

    # Find missing conversations
    missing_ids = set(request.conversation_ids) - set(conversation_map.keys())
    for missing_id in missing_ids:
        failed.append((missing_id, "Conversation not found"))

    # Process each conversation based on operation
    for conv_id in request.conversation_ids:
        if conv_id not in conversation_map:
            continue  # Already marked as failed

        conversation = conversation_map[conv_id]

        try:
            if request.operation == "delete":
                conversation.is_deleted = True
                conversation.deleted_at = datetime.now()
                successful.append(conv_id)

            elif request.operation == "archive":
                conversation.is_archived = True
                successful.append(conv_id)

            elif request.operation == "unarchive":
                conversation.is_archived = False
                successful.append(conv_id)

            elif request.operation == "pin":
                conversation.is_pinned = True
                successful.append(conv_id)

            elif request.operation == "unpin":
                conversation.is_pinned = False
                successful.append(conv_id)

            elif request.operation == "move":
                if request.project_id:
                    conversation.project_id = str(request.project_id)
                    successful.append(conv_id)
                else:
                    failed.append((conv_id, "Project ID required for move operation"))

        except Exception as e:
            failed.append((conv_id, str(e)))

    # Commit all changes
    if successful:
        await db.commit()

    completed_at = datetime.now()
    processing_time = (completed_at - started_at).total_seconds()

    # Log the batch operation
    await log_audit(
        db=db,
        action=AuditAction.BATCH_OPERATION,
        resource_type="conversations",
        details={
            "operation": request.operation,
            "total_requested": len(request.conversation_ids),
            "successful": len(successful),
            "failed": len(failed)
        }
    )

    return BatchOperationResponse(
        success=len(failed) == 0,
        operation=request.operation,
        total_requested=len(request.conversation_ids),
        total_processed=len(successful) + len(failed),
        successful=successful,
        failed=failed,
        started_at=started_at,
        completed_at=completed_at,
        processing_time_seconds=processing_time
    )


@router.post("/api/batch/conversations/export", response_model=BatchExportResult)
@router.post("/conversations/batch/export")  # Frontend compatibility
async def batch_export_conversations(
    request: dict,
    export_format: Literal["json", "markdown", "csv"] = "json",
    db: AsyncSession = Depends(get_db),
):
    """
    Export multiple conversations in the specified format.

    Frontend-compatible endpoint that returns blob data.
    """
    # Extract conversation_ids from request body
    conversation_ids = request.get("conversation_ids", [])
    if not conversation_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one conversation ID is required"
        )

    # Convert string IDs to UUID
    try:
        conversation_ids = [UUID(cid) if isinstance(cid, str) else cid for cid in conversation_ids]
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid conversation ID format"
        )

    started_at = datetime.now()
    successful = []
    failed = []
    export_data = []

    # Fetch all conversations with their messages
    conversations_query = (
        select(ConversationModel)
        .options(selectinload(ConversationModel.messages))
        .where(ConversationModel.id.in_(conversation_ids))
    )
    result = await db.execute(conversations_query)
    conversations = result.scalars().all()
    conversation_map = {conv.id: conv for conv in conversations}

    # Find missing conversations
    missing_ids = set(conversation_ids) - set(conversation_map.keys())
    for missing_id in missing_ids:
        failed.append((missing_id, "Conversation not found"))

    # Export each conversation
    for conv_id in conversation_ids:
        if conv_id not in conversation_map:
            continue

        conversation = conversation_map[conv_id]

        try:
            if export_format == "json":
                # Export as JSON
                conv_data = {
                    "id": str(conversation.id),
                    "title": conversation.title,
                    "model": conversation.model,
                    "created_at": conversation.created_at.isoformat(),
                    "updated_at": conversation.updated_at.isoformat(),
                    "messages": [
                        {
                            "id": str(msg.id),
                            "role": msg.role,
                            "content": msg.content,
                            "created_at": msg.created_at.isoformat(),
                            "input_tokens": msg.input_tokens,
                            "output_tokens": msg.output_tokens
                        }
                        for msg in conversation.messages
                    ]
                }
                export_data.append(conv_data)
                successful.append(conv_id)

            elif export_format == "markdown":
                # Export as Markdown
                md_content = f"# {conversation.title}\n\n"
                md_content += f"**Model:** {conversation.model}\n"
                md_content += f"**Created:** {conversation.created_at.isoformat()}\n\n"
                md_content += "---\n\n"

                for msg in conversation.messages:
                    role = msg.role.capitalize()
                    md_content += f"## {role}\n\n{msg.content}\n\n"

                export_data.append({
                    "id": str(conversation.id),
                    "title": conversation.title,
                    "content": md_content
                })
                successful.append(conv_id)

            elif export_format == "csv":
                # Export as CSV (messages format)
                for msg in conversation.messages:
                    export_data.append({
                        "conversation_id": str(conversation.id),
                        "conversation_title": conversation.title,
                        "message_id": str(msg.id),
                        "role": msg.role,
                        "content": msg.content[:1000],  # Truncate long content
                        "created_at": msg.created_at.isoformat()
                    })
                successful.append(conv_id)

        except Exception as e:
            failed.append((conv_id, str(e)))

    completed_at = datetime.now()
    processing_time = (completed_at - started_at).total_seconds()

    # Determine if data should be included directly or via file
    data_size = len(json.dumps(export_data))
    include_data = data_size < 10 * 1024 * 1024  # 10MB threshold

    # Create export file if needed
    file_url = None
    file_data = None

    if include_data:
        # Include data in response (base64 encoded for safety)
        import base64
        if export_format == "json":
            json_str = json.dumps(export_data, indent=2)
            file_data = base64.b64encode(json_str.encode()).decode()
    else:
        # Save to file and return URL
        export_dir = Path("data/exports")
        export_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"batch_export_{timestamp}.{export_format}"
        filepath = export_dir / filename

        if export_format == "json":
            with open(filepath, 'w') as f:
                json.dump(export_data, f, indent=2)
        elif export_format == "markdown":
            with open(filepath, 'w') as f:
                for item in export_data:
                    f.write(item['content'])
                    f.write("\n\n---\n\n")
        elif export_format == "csv":
            import csv
            with open(filepath, 'w', newline='') as f:
                if export_data:
                    writer = csv.DictWriter(f, fieldnames=export_data[0].keys())
                    writer.writeheader()
                    writer.writerows(export_data)

        file_url = f"/api/batch/exports/{filename}"

    # Log the export
    await log_audit(
        db=db,
        action=AuditAction.BATCH_EXPORT,
        resource_type="conversations",
        details={
            "export_format": export_format,
            "total_requested": len(conversation_ids),
            "successful": len(successful),
            "failed": len(failed),
            "file_url": file_url
        }
    )

    return BatchExportResult(
        success=len(successful) > 0,
        operation="batch_export",
        total_requested=len(conversation_ids),
        total_exported=len(successful),
        export_format=export_format,
        file_url=file_url,
        file_data=file_data,
        successful=successful,
        failed=failed,
        started_at=started_at,
        completed_at=completed_at,
        processing_time_seconds=processing_time
    )


@router.get("/api/batch/exports/{filename}")
async def download_export_file(filename: str):
    """Download a previously generated export file."""
    export_path = Path("data/exports") / filename

    if not export_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Export file not found"
        )

    return FileResponse(
        path=export_path,
        filename=filename,
        media_type="application/octet-stream"
    )


@router.get("/api/batch/operations/{task_id}")
async def get_batch_operation_status(task_id: str):
    """
    Get the status of a batch operation (for long-running operations).

    This is useful for operations that run in the background.
    """
    # This would integrate with a background task system
    # For now, return a placeholder
    return {
        "task_id": task_id,
        "status": "not_implemented",
        "message": "Background task tracking not yet implemented"
    }
