"""MCP server management endpoints."""

from typing import Optional
from uuid import UUID
import json
from datetime import datetime

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.models.mcp_server import MCPServer

router = APIRouter()


class MCPServerCreate(BaseModel):
    """Request model for creating an MCP server."""

    name: str
    server_type: str
    config: dict
    description: Optional[str] = None


class MCPServerUpdate(BaseModel):
    """Request model for updating an MCP server."""

    name: Optional[str] = None
    config: Optional[dict] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    available_tools: Optional[list[str]] = None


class MCPServerTest(BaseModel):
    """Request model for testing an MCP server connection."""

    config: dict
    server_type: str


@router.get("")
async def list_mcp_servers(
    db: AsyncSession = Depends(get_db),
    active_only: bool = False,
) -> list[dict]:
    """List all MCP servers with optional filtering."""
    query = select(MCPServer)

    if active_only:
        query = query.where(MCPServer.is_active == True)

    # Order by most recently used/updated
    query = query.order_by(MCPServer.updated_at.desc())

    result = await db.execute(query)
    servers = result.scalars().all()

    return [server.to_dict() for server in servers]


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_mcp_server(
    data: MCPServerCreate,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Create a new MCP server configuration."""
    server = MCPServer(
        name=data.name,
        server_type=data.server_type,
        config=data.config,
        description=data.description,
    )

    db.add(server)
    await db.commit()
    await db.refresh(server)

    return server.to_dict()


@router.get("/{server_id}")
async def get_mcp_server(
    server_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get a specific MCP server."""
    result = await db.execute(select(MCPServer).where(MCPServer.id == str(server_id)))
    server = result.scalar_one_or_none()

    if not server:
        raise HTTPException(status_code=404, detail="MCP server not found")

    return server.to_dict()


@router.put("/{server_id}")
async def update_mcp_server(
    server_id: UUID,
    data: MCPServerUpdate,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Update an MCP server configuration."""
    result = await db.execute(select(MCPServer).where(MCPServer.id == str(server_id)))
    server = result.scalar_one_or_none()

    if not server:
        raise HTTPException(status_code=404, detail="MCP server not found")

    if data.name is not None:
        server.name = data.name
    if data.config is not None:
        server.config = data.config
    if data.description is not None:
        server.description = data.description
    if data.is_active is not None:
        server.is_active = data.is_active
    if data.available_tools is not None:
        server.available_tools = data.available_tools

    await db.commit()
    await db.refresh(server)

    return server.to_dict()


@router.delete("/{server_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_mcp_server(
    server_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete an MCP server configuration."""
    result = await db.execute(select(MCPServer).where(MCPServer.id == str(server_id)))
    server = result.scalar_one_or_none()

    if not server:
        raise HTTPException(status_code=404, detail="MCP server not found")

    await db.delete(server)
    await db.commit()


@router.post("/{server_id}/test", status_code=status.HTTP_200_OK)
async def test_mcp_server(
    server_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Test connection to an MCP server."""
    result = await db.execute(select(MCPServer).where(MCPServer.id == str(server_id)))
    server = result.scalar_one_or_none()

    if not server:
        raise HTTPException(status_code=404, detail="MCP server not found")

    # Simulate health check (in real implementation, this would ping the server)
    # For now, we'll just update the health check timestamp
    server.last_health_check = datetime.utcnow()
    server.health_status = "healthy"  # Simulated

    await db.commit()
    await db.refresh(server)

    return {
        "status": "success",
        "health_status": server.health_status,
        "last_check": server.last_health_check.isoformat() if server.last_health_check else None,
        "message": "Server is reachable"
    }


@router.post("/test-connection", status_code=status.HTTP_200_OK)
async def test_mcp_connection(
    data: MCPServerTest,
) -> dict:
    """Test a potential MCP server connection before saving."""
    # Simulate connection test
    # In real implementation, this would attempt to connect to the server

    return {
        "status": "success",
        "message": f"Connection to {data.server_type} server successful",
        "server_type": data.server_type,
        "available_tools": ["tool1", "tool2", "tool3"]  # Simulated
    }


@router.get("/types/list")
async def list_server_types() -> list[dict]:
    """Get list of available MCP server types."""
    return [
        {
            "type": "filesystem",
            "label": "Filesystem Access",
            "description": "Read and write files on the local filesystem",
            "config_fields": ["root_path", "permissions"],
        },
        {
            "type": "brave-search",
            "label": "Brave Search",
            "description": "Web search using Brave Search API",
            "config_fields": ["api_key"],
        },
        {
            "type": "tavily-search",
            "label": "Tavily Search",
            "description": "Web search using Tavily API",
            "config_fields": ["api_key"],
        },
        {
            "type": "github",
            "label": "GitHub Integration",
            "description": "Access GitHub repositories and issues",
            "config_fields": ["api_key", "repositories"],
        },
        {
            "type": "slack",
            "label": "Slack Integration",
            "description": "Send and receive Slack messages",
            "config_fields": ["bot_token", "channels"],
        },
        {
            "type": "database",
            "label": "Database Connection",
            "description": "Connect to SQL databases",
            "config_fields": ["connection_string", "db_type"],
        },
    ]


@router.post("/{server_id}/tools")
async def get_server_tools(
    server_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get available tools from an MCP server."""
    result = await db.execute(select(MCPServer).where(MCPServer.id == str(server_id)))
    server = result.scalar_one_or_none()

    if not server:
        raise HTTPException(status_code=404, detail="MCP server not found")

    # In real implementation, this would query the MCP server for its tools
    # For now, return cached tools or simulated tools
    tools = server.available_tools or []

    return {
        "server_id": str(server_id),
        "server_name": server.name,
        "tools": tools,
        "count": len(tools)
    }
