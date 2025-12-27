"""Template management endpoints."""

import json
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, status, Depends, Request
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.models import Template as TemplateModel
from src.utils.audit import log_audit, get_request_info
from src.models.audit_log import AuditActionType as AuditAction

router = APIRouter()


class TemplateCreate(BaseModel):
    """Request model for creating a template."""

    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    category: str = Field(default="general", max_length=50)
    system_prompt: Optional[str] = None
    initial_message: str = Field(..., min_length=1)
    model: str = Field(default="claude-sonnet-4-5-20250929", max_length=100)
    tags: Optional[dict] = None


class TemplateUpdate(BaseModel):
    """Request model for updating a template."""

    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = Field(None, max_length=50)
    system_prompt: Optional[str] = None
    initial_message: Optional[str] = Field(None, min_length=1)
    model: Optional[str] = Field(None, max_length=100)
    tags: Optional[dict] = None
    is_active: Optional[bool] = None


class TemplateResponse(BaseModel):
    """Response model for a template."""

    id: str
    user_id: str
    title: str
    description: Optional[str]
    category: str
    system_prompt: Optional[str]
    initial_message: str
    model: str
    tags: Optional[dict]
    is_builtin: bool
    is_active: bool
    usage_count: int
    created_at: str
    updated_at: str


@router.get("", response_model=list[TemplateResponse])
async def list_templates(
    category: Optional[str] = None,
    is_active: bool = True,
    include_builtin: bool = True,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """List all templates."""
    query = select(TemplateModel)

    if is_active:
        query = query.where(TemplateModel.is_active == True)

    if not include_builtin:
        query = query.where(TemplateModel.is_builtin == False)

    if category:
        query = query.where(TemplateModel.category == category)

    query = query.order_by(TemplateModel.usage_count.desc(), TemplateModel.created_at.desc())
    query = query.offset(offset).limit(limit)

    result = await db.execute(query)
    templates = result.scalars().all()

    return [template.to_dict() for template in templates]


@router.get("/categories")
async def list_categories(
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """List all template categories."""
    query = select(TemplateModel.category, func.count(TemplateModel.id))
    query = query.where(TemplateModel.is_active == True)
    query = query.group_by(TemplateModel.category)
    query = query.order_by(TemplateModel.category)

    result = await db.execute(query)
    categories = result.all()

    return [{"category": cat, "count": count} for cat, count in categories]


@router.get("/{template_id}", response_model=TemplateResponse)
async def get_template(
    template_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get a specific template."""
    result = await db.execute(
        select(TemplateModel).where(TemplateModel.id == template_id)
    )
    template = result.scalar_one_or_none()

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    return template.to_dict()


@router.post("", status_code=status.HTTP_201_CREATED, response_model=TemplateResponse)
async def create_template(
    data: TemplateCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Create a new template."""
    template = TemplateModel(
        title=data.title,
        description=data.description,
        category=data.category,
        system_prompt=data.system_prompt,
        initial_message=data.initial_message,
        model=data.model,
        tags=data.tags,
        is_builtin=False,
        is_active=True,
        usage_count=0,
    )

    db.add(template)
    await db.commit()
    await db.refresh(template)

    # Audit log
    ip_address, user_agent = get_request_info(request)
    await log_audit(
        db=db,
        user_id="default-user",
        action=AuditAction.TEMPLATE_CREATE,
        resource_type="template",
        resource_id=template.id,
        details={"title": template.title, "category": template.category},
        ip_address=ip_address,
        user_agent=user_agent,
    )

    return template.to_dict()


@router.put("/{template_id}", response_model=TemplateResponse)
async def update_template(
    template_id: str,
    data: TemplateUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Update a template."""
    result = await db.execute(
        select(TemplateModel).where(TemplateModel.id == template_id)
    )
    template = result.scalar_one_or_none()

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    # Don't allow updating built-in templates
    if template.is_builtin:
        raise HTTPException(
            status_code=403, detail="Cannot update built-in templates"
        )

    # Update fields
    if data.title is not None:
        template.title = data.title
    if data.description is not None:
        template.description = data.description
    if data.category is not None:
        template.category = data.category
    if data.system_prompt is not None:
        template.system_prompt = data.system_prompt
    if data.initial_message is not None:
        template.initial_message = data.initial_message
    if data.model is not None:
        template.model = data.model
    if data.tags is not None:
        template.tags = data.tags
    if data.is_active is not None:
        template.is_active = data.is_active

    await db.commit()
    await db.refresh(template)

    # Audit log
    ip_address, user_agent = get_request_info(request)
    await log_audit(
        db=db,
        user_id="default-user",
        action=AuditAction.TEMPLATE_UPDATE,
        resource_type="template",
        resource_id=template.id,
        details={"title": template.title},
        ip_address=ip_address,
        user_agent=user_agent,
    )

    return template.to_dict()


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(
    template_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a template."""
    result = await db.execute(
        select(TemplateModel).where(TemplateModel.id == template_id)
    )
    template = result.scalar_one_or_none()

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    # Don't allow deleting built-in templates
    if template.is_builtin:
        raise HTTPException(
            status_code=403, detail="Cannot delete built-in templates"
        )

    await db.delete(template)
    await db.commit()

    # Audit log
    ip_address, user_agent = get_request_info(request)
    await log_audit(
        db=db,
        user_id="default-user",
        action=AuditAction.TEMPLATE_DELETE,
        resource_type="template",
        resource_id=template_id,
        details={"title": template.title},
        ip_address=ip_address,
        user_agent=user_agent,
    )


@router.post("/{template_id}/use", response_model=TemplateResponse)
async def use_template(
    template_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Increment template usage count."""
    result = await db.execute(
        select(TemplateModel).where(TemplateModel.id == template_id)
    )
    template = result.scalar_one_or_none()

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    # Increment usage count
    template.usage_count += 1
    await db.commit()
    await db.refresh(template)

    # Audit log
    ip_address, user_agent = get_request_info(request)
    await log_audit(
        db=db,
        user_id="default-user",
        action=AuditAction.TEMPLATE_USE,
        resource_type="template",
        resource_id=template.id,
        details={"title": template.title, "usage_count": template.usage_count},
        ip_address=ip_address,
        user_agent=user_agent,
    )

    return template.to_dict()


class TemplateFromConversationRequest(BaseModel):
    """Request model for creating a template from conversation."""
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    category: str = Field(default="custom", max_length=50)


@router.post("/from-conversation/{conversation_id}", status_code=status.HTTP_201_CREATED, response_model=TemplateResponse)
async def create_template_from_conversation(
    conversation_id: str,
    request_body: TemplateFromConversationRequest,
    request: Request = None,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Create a template from an existing conversation."""
    from src.models import Conversation

    # Get the conversation
    conv_result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conversation = conv_result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Get the first message as the initial message
    from src.models import Message
    msg_result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .where(Message.role == "user")
        .order_by(Message.created_at.asc())
        .limit(1)
    )
    first_message = msg_result.scalar_one_or_none()

    if not first_message:
        raise HTTPException(
            status_code=400, detail="Conversation has no user messages"
        )

    # Create template
    template = TemplateModel(
        title=request_body.title,
        description=request_body.description,
        category=request_body.category,
        system_prompt=None,  # Could extract from system messages if needed
        initial_message=first_message.content,
        model=conversation.model,
        tags=None,
        is_builtin=False,
        is_active=True,
        usage_count=0,
    )

    db.add(template)
    await db.commit()
    await db.refresh(template)

    # Audit log
    ip_address, user_agent = get_request_info(request)
    await log_audit(
        db=db,
        user_id="default-user",
        action=AuditAction.TEMPLATE_CREATE,
        resource_type="template",
        resource_id=template.id,
        details={
            "title": template.title,
            "category": template.category,
            "from_conversation": conversation_id,
        },
        ip_address=ip_address,
        user_agent=user_agent,
    )

    return template.to_dict()
