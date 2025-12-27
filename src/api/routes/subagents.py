"""SubAgent management endpoints.

This module provides API endpoints for managing sub-agent configurations,
including built-in sub-agents and custom user-created sub-agents.
"""

from typing import List, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.models.subagent import SubAgent, BUILTIN_SUBAGENTS

router = APIRouter()


class SubAgentCreate(BaseModel):
    """Request model for creating a sub-agent."""
    name: str = Field(..., description="Sub-agent name (unique identifier)")
    description: Optional[str] = Field(None, description="Description of the sub-agent")
    system_prompt: str = Field(..., description="System prompt for the sub-agent")
    model: str = Field(default="claude-sonnet-4-5-20250929", description="Model to use")
    tools: List[str] = Field(default_factory=list, description="List of tool names")


class SubAgentUpdate(BaseModel):
    """Request model for updating a sub-agent."""
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    model: Optional[str] = None
    tools: Optional[List[str]] = None
    is_active: Optional[bool] = None


class SubAgentResponse(BaseModel):
    """Response model for sub-agent."""
    id: str
    user_id: str
    name: str
    description: Optional[str]
    system_prompt: str
    model: str
    tools: List[str]
    is_builtin: bool
    is_active: bool
    created_at: str
    updated_at: str


@router.get("/builtin", response_model=List[SubAgentResponse])
async def get_builtin_subagents(db: AsyncSession = Depends(get_db)) -> List[dict]:
    """Get all built-in sub-agents.

    Returns the predefined built-in sub-agents:
    - research-agent: For web research and information gathering
    - code-review-agent: For code analysis and security review
    - documentation-agent: For creating documentation
    - test-writing-agent: For writing tests
    """
    # Return built-in sub-agents (these are not stored in DB, just returned as static data)
    return [
        {
            "id": f"builtin-{agent['name']}",
            "user_id": "system",
            "name": agent["name"],
            "description": agent["description"],
            "system_prompt": agent["system_prompt"],
            "model": agent["model"],
            "tools": agent["tools"],
            "is_builtin": True,
            "is_active": True,
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
        }
        for agent in BUILTIN_SUBAGENTS
    ]


@router.get("/", response_model=List[SubAgentResponse])
async def get_subagents(
    user_id: Optional[str] = None,
    include_builtin: bool = True,
    db: AsyncSession = Depends(get_db)
) -> List[dict]:
    """Get all sub-agents for a user.

    Args:
        user_id: User ID to filter by (optional, defaults to 'default')
        include_builtin: Whether to include built-in sub-agents

    Returns:
        List of sub-agent configurations
    """
    if user_id is None:
        user_id = "default"

    # Query custom sub-agents from database
    result = await db.execute(
        select(SubAgent)
        .where(SubAgent.user_id == user_id)
        .where(SubAgent.is_deleted == False)
        .order_by(SubAgent.created_at)
    )
    custom_agents = result.scalars().all()

    response = [agent.to_dict() for agent in custom_agents]

    # Add built-in agents if requested
    if include_builtin:
        builtin_response = await get_builtin_subagents(db)
        response.extend(builtin_response)

    return response


@router.get("/{subagent_id}", response_model=SubAgentResponse)
async def get_subagent(subagent_id: str, db: AsyncSession = Depends(get_db)) -> dict:
    """Get a specific sub-agent by ID.

    Args:
        subagent_id: ID of the sub-agent

    Returns:
        Sub-agent configuration
    """
    # Check if it's a built-in sub-agent
    if subagent_id.startswith("builtin-"):
        name = subagent_id.replace("builtin-", "")
        for agent in BUILTIN_SUBAGENTS:
            if agent["name"] == name:
                return {
                    "id": f"builtin-{name}",
                    "user_id": "system",
                    "name": agent["name"],
                    "description": agent["description"],
                    "system_prompt": agent["system_prompt"],
                    "model": agent["model"],
                    "tools": agent["tools"],
                    "is_builtin": True,
                    "is_active": True,
                    "created_at": "2024-01-01T00:00:00",
                    "updated_at": "2024-01-01T00:00:00",
                }
        raise HTTPException(status_code=404, detail="Built-in sub-agent not found")

    # Query custom sub-agent from database
    result = await db.execute(
        select(SubAgent)
        .where(SubAgent.id == subagent_id)
        .where(SubAgent.is_deleted == False)
    )
    agent = result.scalar_one_or_none()

    if agent is None:
        raise HTTPException(status_code=404, detail="Sub-agent not found")

    return agent.to_dict()


@router.post("/", response_model=SubAgentResponse, status_code=status.HTTP_201_CREATED)
async def create_subagent(
    subagent_data: SubAgentCreate,
    user_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Create a new custom sub-agent.

    Args:
        subagent_data: Sub-agent configuration
        user_id: User ID (defaults to 'default')

    Returns:
        Created sub-agent configuration
    """
    if user_id is None:
        user_id = "default"

    # Check if name already exists for this user
    result = await db.execute(
        select(SubAgent)
        .where(SubAgent.user_id == user_id)
        .where(SubAgent.name == subagent_data.name)
        .where(SubAgent.is_deleted == False)
    )
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Sub-agent with name '{subagent_data.name}' already exists"
        )

    # Create new sub-agent
    agent = SubAgent(
        user_id=user_id,
        name=subagent_data.name,
        description=subagent_data.description,
        system_prompt=subagent_data.system_prompt,
        model=subagent_data.model,
        tools=subagent_data.tools,
        is_builtin=False,
    )

    db.add(agent)
    await db.commit()
    await db.refresh(agent)

    return agent.to_dict()


@router.put("/{subagent_id}", response_model=SubAgentResponse)
async def update_subagent(
    subagent_id: str,
    update_data: SubAgentUpdate,
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Update a custom sub-agent.

    Args:
        subagent_id: ID of the sub-agent to update
        update_data: Fields to update

    Returns:
        Updated sub-agent configuration
    """
    # Cannot update built-in sub-agents
    if subagent_id.startswith("builtin-"):
        raise HTTPException(
            status_code=400,
            detail="Cannot modify built-in sub-agents"
        )

    # Get the sub-agent
    result = await db.execute(
        select(SubAgent)
        .where(SubAgent.id == subagent_id)
        .where(SubAgent.is_deleted == False)
    )
    agent = result.scalar_one_or_none()

    if agent is None:
        raise HTTPException(status_code=404, detail="Sub-agent not found")

    # Update fields
    if update_data.description is not None:
        agent.description = update_data.description
    if update_data.system_prompt is not None:
        agent.system_prompt = update_data.system_prompt
    if update_data.model is not None:
        agent.model = update_data.model
    if update_data.tools is not None:
        agent.tools = update_data.tools
    if update_data.is_active is not None:
        agent.is_active = update_data.is_active

    await db.commit()
    await db.refresh(agent)

    return agent.to_dict()


@router.delete("/{subagent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_subagent(subagent_id: str, db: AsyncSession = Depends(get_db)) -> None:
    """Delete a custom sub-agent (soft delete).

    Args:
        subagent_id: ID of the sub-agent to delete
    """
    # Cannot delete built-in sub-agents
    if subagent_id.startswith("builtin-"):
        raise HTTPException(
            status_code=400,
            detail="Cannot delete built-in sub-agents"
        )

    # Get the sub-agent
    result = await db.execute(
        select(SubAgent)
        .where(SubAgent.id == subagent_id)
        .where(SubAgent.is_deleted == False)
    )
    agent = result.scalar_one_or_none()

    if agent is None:
        raise HTTPException(status_code=404, detail="Sub-agent not found")

    # Soft delete
    agent.is_deleted = True
    await db.commit()


@router.get("/{subagent_id}/tools", response_model=List[str])
async def get_subagent_tools(subagent_id: str, db: AsyncSession = Depends(get_db)) -> List[str]:
    """Get the tools available to a sub-agent.

    Args:
        subagent_id: ID of the sub-agent

    Returns:
        List of tool names
    """
    # Check if it's a built-in sub-agent
    if subagent_id.startswith("builtin-"):
        name = subagent_id.replace("builtin-", "")
        for agent in BUILTIN_SUBAGENTS:
            if agent["name"] == name:
                return agent["tools"]
        raise HTTPException(status_code=404, detail="Built-in sub-agent not found")

    # Query custom sub-agent from database
    result = await db.execute(
        select(SubAgent)
        .where(SubAgent.id == subagent_id)
        .where(SubAgent.is_deleted == False)
    )
    agent = result.scalar_one_or_none()

    if agent is None:
        raise HTTPException(status_code=404, detail="Sub-agent not found")

    return agent.tools
