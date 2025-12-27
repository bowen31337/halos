"""Audit logging utility functions."""

import logging
from typing import Optional, Any
from uuid import UUID

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.models.audit_log import AuditLog, AuditActionType
from src.core.database import async_session_factory

logger = logging.getLogger(__name__)


async def log_audit(
    db: AsyncSession,
    user_id: str,
    action: AuditActionType | str,
    resource_type: Optional[str] = None,
    resource_id: Optional[str | UUID] = None,
    tool_name: Optional[str] = None,
    tool_decision: Optional[str] = None,
    details: Optional[dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> AuditLog:
    """Log an audit event to the database.

    Args:
        db: Database session
        user_id: User ID performing the action
        action: Action type (AuditActionType enum or string)
        resource_type: Type of resource affected (optional)
        resource_id: ID of resource affected (optional)
        tool_name: Name of tool used (optional)
        tool_decision: Tool decision (approve/edit/reject) (optional)
        details: Additional details as JSON (optional)
        ip_address: Client IP address (optional)
        user_agent: Client user agent (optional)

    Returns:
        The created AuditLog record
    """
    # Convert string to AuditActionType if needed
    if isinstance(action, str):
        action = AuditActionType(action)

    # Convert resource_id to string if it's a UUID
    resource_id_str = str(resource_id) if resource_id else None

    audit_log = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id_str,
        tool_name=tool_name,
        tool_decision=tool_decision,
        details=details,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    db.add(audit_log)
    await db.flush()
    logger.info(
        f"Audit: {action.value} | user={user_id} | "
        f"resource={resource_type}:{resource_id_str} | "
        f"tool={tool_name} | decision={tool_decision}"
    )
    return audit_log


async def get_audit_logs(
    db: AsyncSession,
    user_id: Optional[str] = None,
    action: Optional[AuditActionType | str] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str | UUID] = None,
    tool_name: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
) -> list[AuditLog]:
    """Query audit logs with filters.

    Args:
        db: Database session
        user_id: Filter by user ID
        action: Filter by action type
        resource_type: Filter by resource type
        resource_id: Filter by resource ID
        tool_name: Filter by tool name
        limit: Maximum number of results
        offset: Number of results to skip

    Returns:
        List of matching audit logs
    """
    stmt = select(AuditLog).order_by(AuditLog.created_at.desc())

    if user_id:
        stmt = stmt.where(AuditLog.user_id == user_id)

    if action:
        action_enum = action if isinstance(action, AuditActionType) else AuditActionType(action)
        stmt = stmt.where(AuditLog.action == action_enum)

    if resource_type:
        stmt = stmt.where(AuditLog.resource_type == resource_type)

    if resource_id:
        resource_id_str = str(resource_id)
        stmt = stmt.where(AuditLog.resource_id == resource_id_str)

    if tool_name:
        stmt = stmt.where(AuditLog.tool_name == tool_name)

    stmt = stmt.limit(limit).offset(offset)

    result = await db.execute(stmt)
    return list(result.scalars().all())


async def log_tool_decision(
    db: AsyncSession,
    user_id: str,
    tool_name: str,
    decision: str,
    details: Optional[dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> AuditLog:
    """Log a HITL (Human-in-the-Loop) tool decision.

    Args:
        db: Database session
        user_id: User ID making the decision
        tool_name: Name of the tool
        decision: Decision (approve, edit, reject)
        details: Additional details about the decision
        ip_address: Client IP address
        user_agent: Client user agent

    Returns:
        The created AuditLog record
    """
    action_map = {
        "approve": AuditActionType.AGENT_INTERRUPT_APPROVE,
        "reject": AuditActionType.AGENT_INTERRUPT_REJECT,
        "edit": AuditActionType.AGENT_INTERRUPT_EDIT,
    }
    action = action_map.get(decision, AuditActionType.AGENT_INTERRUPT_EDIT)

    return await log_audit(
        db=db,
        user_id=user_id,
        action=action,
        tool_name=tool_name,
        tool_decision=decision,
        details=details,
        ip_address=ip_address,
        user_agent=user_agent,
    )


async def log_conversation_action(
    db: AsyncSession,
    user_id: str,
    action: AuditActionType,
    conversation_id: str | UUID,
    details: Optional[dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> AuditLog:
    """Log a conversation-related action.

    Args:
        db: Database session
        user_id: User ID performing the action
        action: Conversation action type
        conversation_id: ID of the conversation
        details: Additional details
        ip_address: Client IP address
        user_agent: Client user agent

    Returns:
        The created AuditLog record
    """
    return await log_audit(
        db=db,
        user_id=user_id,
        action=action,
        resource_type="conversation",
        resource_id=conversation_id,
        details=details,
        ip_address=ip_address,
        user_agent=user_agent,
    )


async def log_project_action(
    db: AsyncSession,
    user_id: str,
    action: AuditActionType,
    project_id: str | UUID,
    details: Optional[dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> AuditLog:
    """Log a project-related action.

    Args:
        db: Database session
        user_id: User ID performing the action
        action: Project action type
        project_id: ID of the project
        details: Additional details
        ip_address: Client IP address
        user_agent: Client user agent

    Returns:
        The created AuditLog record
    """
    return await log_audit(
        db=db,
        user_id=user_id,
        action=action,
        resource_type="project",
        resource_id=project_id,
        details=details,
        ip_address=ip_address,
        user_agent=user_agent,
    )


async def log_agent_invocation(
    db: AsyncSession,
    user_id: str,
    conversation_id: str | UUID,
    model: str,
    details: Optional[dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> AuditLog:
    """Log an agent invocation.

    Args:
        db: Database session
        user_id: User ID invoking the agent
        conversation_id: ID of the conversation
        model: Model used
        details: Additional details (message, settings, etc.)
        ip_address: Client IP address
        user_agent: Client user agent

    Returns:
        The created AuditLog record
    """
    full_details = {
        "model": model,
        **(details or {})
    }
    return await log_audit(
        db=db,
        user_id=user_id,
        action=AuditActionType.AGENT_INVOKE,
        resource_type="conversation",
        resource_id=conversation_id,
        details=full_details,
        ip_address=ip_address,
        user_agent=user_agent,
    )


def get_request_info(request: Request) -> tuple[Optional[str], Optional[str]]:
    """Extract IP address and user agent from request.

    Args:
        request: FastAPI request object

    Returns:
        Tuple of (ip_address, user_agent)
    """
    ip_address = None
    user_agent = None

    try:
        # Get IP address
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            ip_address = forwarded.split(",")[0].strip()
        else:
            ip_address = request.client.host if request.client else None

        # Get user agent
        user_agent = request.headers.get("User-Agent")
    except Exception:
        pass

    return ip_address, user_agent


class AuditLogger:
    """Utility class for logging user actions to the audit trail."""

    @staticmethod
    async def log(
        db: AsyncSession,
        action: AuditActionType,
        user_id: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        tool_name: Optional[str] = None,
        tool_decision: Optional[str] = None,
        details: Optional[dict] = None,
        request: Optional[Request] = None,
    ) -> AuditLog:
        """
        Log an audit event to the database.

        Args:
            db: Database session
            action: The action type being performed
            user_id: ID of the user performing the action
            resource_type: Type of resource affected (e.g., 'conversation', 'message')
            resource_id: ID of the resource affected
            tool_name: Name of tool being used (for agent/tool actions)
            tool_decision: Decision made for HITL (approve, edit, reject)
            details: Additional context as JSON
            request: FastAPI request object (for IP and user agent)

        Returns:
            The created AuditLog record
        """
        # Extract request info if provided
        ip_address = None
        user_agent = None
        if request:
            # Get real IP behind proxies
            forwarded = request.headers.get("X-Forwarded-For")
            if forwarded:
                ip_address = forwarded.split(",")[0].strip()
            else:
                ip_address = request.client.host if request.client else None
            user_agent = request.headers.get("User-Agent")

        # Create audit log record
        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            tool_name=tool_name,
            tool_decision=tool_decision,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        db.add(audit_log)
        await db.commit()
        await db.refresh(audit_log)

        # Log to application logs as well
        logger.info(
            f"AUDIT: {action.value} | user={user_id} | "
            f"resource={resource_type}:{resource_id} | "
            f"tool={tool_name} | decision={tool_decision}"
        )

        return audit_log

    @staticmethod
    async def log_conversation_create(
        db: AsyncSession,
        user_id: str,
        conversation_id: UUID,
        details: Optional[dict] = None,
        request: Optional[Request] = None,
    ) -> AuditLog:
        """Log conversation creation."""
        return await AuditLogger.log(
            db=db,
            action=AuditActionType.CONVERSATION_CREATE,
            user_id=user_id,
            resource_type="conversation",
            resource_id=str(conversation_id),
            details=details,
            request=request,
        )

    @staticmethod
    async def log_conversation_delete(
        db: AsyncSession,
        user_id: str,
        conversation_id: UUID,
        details: Optional[dict] = None,
        request: Optional[Request] = None,
    ) -> AuditLog:
        """Log conversation deletion."""
        return await AuditLogger.log(
            db=db,
            action=AuditActionType.CONVERSATION_DELETE,
            user_id=user_id,
            resource_type="conversation",
            resource_id=str(conversation_id),
            details=details,
            request=request,
        )

    @staticmethod
    async def log_message_create(
        db: AsyncSession,
        user_id: str,
        message_id: UUID,
        conversation_id: UUID,
        details: Optional[dict] = None,
        request: Optional[Request] = None,
    ) -> AuditLog:
        """Log message creation."""
        return await AuditLogger.log(
            db=db,
            action=AuditActionType.MESSAGE_CREATE,
            user_id=user_id,
            resource_type="message",
            resource_id=str(message_id),
            details={"conversation_id": str(conversation_id), **(details or {})},
            request=request,
        )

    @staticmethod
    async def log_agent_invoke(
        db: AsyncSession,
        user_id: str,
        conversation_id: UUID,
        details: Optional[dict] = None,
        request: Optional[Request] = None,
    ) -> AuditLog:
        """Log agent invocation."""
        return await AuditLogger.log(
            db=db,
            action=AuditActionType.AGENT_INVOKE,
            user_id=user_id,
            resource_type="conversation",
            resource_id=str(conversation_id),
            details=details,
            request=request,
        )

    @staticmethod
    async def log_agent_interrupt(
        db: AsyncSession,
        user_id: str,
        conversation_id: UUID,
        decision: str,
        tool_name: str,
        details: Optional[dict] = None,
        request: Optional[Request] = None,
    ) -> AuditLog:
        """Log agent interrupt HITL decision."""
        action_map = {
            "approve": AuditActionType.AGENT_INTERRUPT_APPROVE,
            "reject": AuditActionType.AGENT_INTERRUPT_REJECT,
            "edit": AuditActionType.AGENT_INTERRUPT_EDIT,
        }
        action = action_map.get(decision, AuditActionType.AGENT_INTERRUPT_EDIT)

        return await AuditLogger.log(
            db=db,
            action=action,
            user_id=user_id,
            resource_type="conversation",
            resource_id=str(conversation_id),
            tool_name=tool_name,
            tool_decision=decision,
            details=details,
            request=request,
        )

    @staticmethod
    async def log_tool_execution(
        db: AsyncSession,
        user_id: str,
        tool_name: str,
        details: Optional[dict] = None,
        request: Optional[Request] = None,
    ) -> AuditLog:
        """Log tool execution."""
        return await AuditLogger.log(
            db=db,
            action=AuditActionType.TOOL_EXECUTION,
            user_id=user_id,
            tool_name=tool_name,
            details=details,
            request=request,
        )

    @staticmethod
    async def log_project_create(
        db: AsyncSession,
        user_id: str,
        project_id: UUID,
        details: Optional[dict] = None,
        request: Optional[Request] = None,
    ) -> AuditLog:
        """Log project creation."""
        return await AuditLogger.log(
            db=db,
            action=AuditActionType.PROJECT_CREATE,
            user_id=user_id,
            resource_type="project",
            resource_id=str(project_id),
            details=details,
            request=request,
        )

    @staticmethod
    async def log_project_delete(
        db: AsyncSession,
        user_id: str,
        project_id: UUID,
        details: Optional[dict] = None,
        request: Optional[Request] = None,
    ) -> AuditLog:
        """Log project deletion."""
        return await AuditLogger.log(
            db=db,
            action=AuditActionType.PROJECT_DELETE,
            user_id=user_id,
            resource_type="project",
            resource_id=str(project_id),
            details=details,
            request=request,
        )

    @staticmethod
    async def log_artifact_create(
        db: AsyncSession,
        user_id: str,
        artifact_id: UUID,
        details: Optional[dict] = None,
        request: Optional[Request] = None,
    ) -> AuditLog:
        """Log artifact creation."""
        return await AuditLogger.log(
            db=db,
            action=AuditActionType.ARTIFACT_CREATE,
            user_id=user_id,
            resource_type="artifact",
            resource_id=str(artifact_id),
            details=details,
            request=request,
        )

    @staticmethod
    async def log_artifact_execute(
        db: AsyncSession,
        user_id: str,
        artifact_id: UUID,
        details: Optional[dict] = None,
        request: Optional[Request] = None,
    ) -> AuditLog:
        """Log artifact execution."""
        return await AuditLogger.log(
            db=db,
            action=AuditActionType.ARTIFACT_EXECUTE,
            user_id=user_id,
            resource_type="artifact",
            resource_id=str(artifact_id),
            details=details,
            request=request,
        )

    @staticmethod
    async def log_checkpoint_restore(
        db: AsyncSession,
        user_id: str,
        checkpoint_id: UUID,
        conversation_id: UUID,
        details: Optional[dict] = None,
        request: Optional[Request] = None,
    ) -> AuditLog:
        """Log checkpoint restoration."""
        return await AuditLogger.log(
            db=db,
            action=AuditActionType.CHECKPOINT_RESTORE,
            user_id=user_id,
            resource_type="checkpoint",
            resource_id=str(checkpoint_id),
            details={"conversation_id": str(conversation_id), **(details or {})},
            request=request,
        )

    @staticmethod
    async def log_memory_create(
        db: AsyncSession,
        user_id: str,
        memory_id: UUID,
        details: Optional[dict] = None,
        request: Optional[Request] = None,
    ) -> AuditLog:
        """Log memory creation."""
        return await AuditLogger.log(
            db=db,
            action=AuditActionType.MEMORY_CREATE,
            user_id=user_id,
            resource_type="memory",
            resource_id=str(memory_id),
            details=details,
            request=request,
        )

    @staticmethod
    async def log_subagent_delegation(
        db: AsyncSession,
        user_id: str,
        subagent_id: UUID,
        parent_agent: str,
        details: Optional[dict] = None,
        request: Optional[Request] = None,
    ) -> AuditLog:
        """Log subagent delegation."""
        return await AuditLogger.log(
            db=db,
            action=AuditActionType.SUBAGENT_DELEGATION,
            user_id=user_id,
            resource_type="subagent",
            resource_id=str(subagent_id),
            details={"parent_agent": parent_agent, **(details or {})},
            request=request,
        )

    @staticmethod
    async def log_settings_update(
        db: AsyncSession,
        user_id: str,
        setting_type: str,
        details: Optional[dict] = None,
        request: Optional[Request] = None,
    ) -> AuditLog:
        """Log settings update."""
        action_map = {
            "custom_instructions": AuditActionType.SETTINGS_CUSTOM_INSTRUCTIONS,
            "permission_mode": AuditActionType.SETTINGS_PERMISSION_MODE,
            "api_key": AuditActionType.SETTINGS_API_KEY,
        }
        action = action_map.get(setting_type, AuditActionType.SETTINGS_UPDATE)

        return await AuditLogger.log(
            db=db,
            action=action,
            user_id=user_id,
            resource_type="settings",
            details={"setting_type": setting_type, **(details or {})},
            request=request,
        )

    @staticmethod
    async def log_mcp_tool_use(
        db: AsyncSession,
        user_id: str,
        tool_name: str,
        server_name: str,
        details: Optional[dict] = None,
        request: Optional[Request] = None,
    ) -> AuditLog:
        """Log MCP tool usage."""
        return await AuditLogger.log(
            db=db,
            action=AuditActionType.MCP_TOOL_USE,
            user_id=user_id,
            tool_name=tool_name,
            details={"server_name": server_name, **(details or {})},
            request=request,
        )

    @staticmethod
    async def log_conversation_share(
        db: AsyncSession,
        user_id: str,
        conversation_id: UUID,
        details: Optional[dict] = None,
        request: Optional[Request] = None,
    ) -> AuditLog:
        """Log conversation sharing."""
        return await AuditLogger.log(
            db=db,
            action=AuditActionType.CONVERSATION_SHARE,
            user_id=user_id,
            resource_type="conversation",
            resource_id=str(conversation_id),
            details=details,
            request=request,
        )

    @staticmethod
    async def log_prompt_use(
        db: AsyncSession,
        user_id: str,
        prompt_id: UUID,
        details: Optional[dict] = None,
        request: Optional[Request] = None,
    ) -> AuditLog:
        """Log prompt library usage."""
        return await AuditLogger.log(
            db=db,
            action=AuditActionType.PROMPT_USE,
            user_id=user_id,
            resource_type="prompt",
            resource_id=str(prompt_id),
            details=details,
            request=request,
        )


# Re-export AuditAction for backward compatibility
from src.models.audit_log import AuditAction
