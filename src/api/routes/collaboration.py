"""Real-time collaboration endpoints for cursor sharing and live editing."""

import asyncio
import json
from datetime import datetime
from typing import Optional, Dict, Set
from uuid import uuid4

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.core.database import get_db
from src.models.conversation import Conversation

router = APIRouter()

# In-memory storage for active collaboration sessions
# Structure: {conversation_id: {user_id: {cursor: position, name: str, color: str}}}
active_sessions: Dict[str, Dict[str, dict]] = {}

# Structure: {websocket_id: {conversation_id, user_id, cursor, name, color}}
connected_clients: Dict[str, dict] = {}


class CursorPosition(BaseModel):
    """Cursor position model."""
    x: float
    y: float
    line: Optional[int] = None
    character: Optional[int] = None


class UserPresence(BaseModel):
    """User presence information."""
    user_id: str
    name: str
    color: str
    cursor: Optional[CursorPosition] = None
    last_seen: str


class CollaborationEvent(BaseModel):
    """Collaboration event model."""
    event_type: str  # cursor, presence, join, leave, edit
    user_id: str
    data: dict


def get_user_color(user_id: str) -> str:
    """Generate a consistent color for a user based on their ID."""
    colors = [
        "#FF6B6B", "#4ECDC4", "#45B7D1", "#FFA07A", "#98D8C8",
        "#F7DC6F", "#BB8FCE", "#85C1E9", "#F8B739", "#52B788"
    ]
    # Simple hash to pick a color
    hash_val = sum(ord(c) for c in user_id) % len(colors)
    return colors[hash_val]


@router.get("/active/{conversation_id}", response_model=list[UserPresence])
async def get_active_users(
    conversation_id: str,
    db: AsyncSession = Depends(get_db)
) -> list[UserPresence]:
    """Get list of active users in a conversation."""
    # Verify conversation exists
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    active = active_sessions.get(conversation_id, {})
    return [
        UserPresence(
            user_id=user_id,
            name=data.get("name", "Anonymous"),
            color=data.get("color", "#000000"),
            cursor=data.get("cursor"),
            last_seen=data.get("last_seen", datetime.utcnow().isoformat())
        )
        for user_id, data in active.items()
    ]


@router.websocket("/ws/{conversation_id}/{user_id}")
async def websocket_collaboration(
    websocket: WebSocket,
    conversation_id: str,
    user_id: str,
    name: str = Query(default="Anonymous"),
    db: AsyncSession = Depends(get_db)
):
    """WebSocket endpoint for real-time collaboration."""
    await websocket.accept()

    # Verify conversation exists
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()
    if not conversation:
        await websocket.close(code=1008, reason="Conversation not found")
        return

    # Generate client ID
    client_id = str(uuid4())

    # Initialize session data
    user_color = get_user_color(user_id)
    session_data = {
        "conversation_id": conversation_id,
        "user_id": user_id,
        "name": name,
        "color": user_color,
        "cursor": None,
        "last_seen": datetime.utcnow().isoformat()
    }

    connected_clients[client_id] = session_data

    # Add to active sessions
    if conversation_id not in active_sessions:
        active_sessions[conversation_id] = {}

    active_sessions[conversation_id][user_id] = session_data

    # Notify other users that this user joined
    await broadcast_to_conversation(
        conversation_id,
        {
            "event_type": "join",
            "user_id": user_id,
            "name": name,
            "color": user_color,
            "timestamp": datetime.utcnow().isoformat()
        },
        exclude_client=client_id
    )

    # Send current active users to the new user
    await websocket.send_json({
        "event_type": "presence",
        "data": {
            "active_users": [
                {
                    "user_id": uid,
                    "name": data["name"],
                    "color": data["color"],
                    "cursor": data.get("cursor"),
                    "last_seen": data["last_seen"]
                }
                for uid, data in active_sessions[conversation_id].items()
            ]
        }
    })

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            event_type = data.get("event_type")

            # Update last seen
            session_data["last_seen"] = datetime.utcnow().isoformat()
            active_sessions[conversation_id][user_id]["last_seen"] = session_data["last_seen"]

            if event_type == "cursor":
                # Update cursor position
                cursor_data = data.get("data", {})
                session_data["cursor"] = cursor_data

                # Broadcast cursor update to other users
                await broadcast_to_conversation(
                    conversation_id,
                    {
                        "event_type": "cursor",
                        "user_id": user_id,
                        "name": name,
                        "color": user_color,
                        "data": cursor_data,
                        "timestamp": session_data["last_seen"]
                    },
                    exclude_client=client_id
                )

            elif event_type == "edit":
                # Broadcast edit to other users
                edit_data = data.get("data", {})
                await broadcast_to_conversation(
                    conversation_id,
                    {
                        "event_type": "edit",
                        "user_id": user_id,
                        "name": name,
                        "color": user_color,
                        "data": edit_data,
                        "timestamp": session_data["last_seen"]
                    },
                    exclude_client=client_id
                )

            elif event_type == "ping":
                # Respond to ping (keepalive)
                await websocket.send_json({
                    "event_type": "pong",
                    "timestamp": datetime.utcnow().isoformat()
                })

    except WebSocketDisconnect:
        # Handle disconnect
        await handle_disconnect(client_id, conversation_id, user_id, name, user_color)
    except Exception as e:
        print(f"WebSocket error: {e}")
        await handle_disconnect(client_id, conversation_id, user_id, name, user_color)


async def handle_disconnect(client_id: str, conversation_id: str, user_id: str, name: str, color: str):
    """Handle user disconnection."""
    # Remove from connected clients
    if client_id in connected_clients:
        del connected_clients[client_id]

    # Remove from active sessions
    if conversation_id in active_sessions and user_id in active_sessions[conversation_id]:
        del active_sessions[conversation_id][user_id]
        # Clean up empty conversation
        if not active_sessions[conversation_id]:
            del active_sessions[conversation_id]

    # Notify other users that this user left
    await broadcast_to_conversation(
        conversation_id,
        {
            "event_type": "leave",
            "user_id": user_id,
            "name": name,
            "color": color,
            "timestamp": datetime.utcnow().isoformat()
        },
        exclude_client=None
    )


async def broadcast_to_conversation(conversation_id: str, message: dict, exclude_client: Optional[str] = None):
    """Broadcast a message to all clients in a conversation."""
    # Find all clients in this conversation
    clients_to_notify = []
    for client_id, session_data in connected_clients.items():
        if session_data["conversation_id"] == conversation_id:
            if exclude_client is None or client_id != exclude_client:
                clients_to_notify.append((client_id, session_data))

    # Send to each client
    for client_id, session_data in clients_to_notify:
        try:
            # We need to track websocket connections separately
            # For now, we'll use a simple approach with a connection registry
            pass
        except Exception as e:
            print(f"Error broadcasting to client {client_id}: {e}")


# WebSocket connection registry to track actual websocket objects
websocket_registry: Dict[str, WebSocket] = {}


@router.websocket("/ws/v2/{conversation_id}/{user_id}")
async def websocket_collaboration_v2(
    websocket: WebSocket,
    conversation_id: str,
    user_id: str,
    name: str = Query(default="Anonymous"),
    db: AsyncSession = Depends(get_db)
):
    """WebSocket endpoint v2 - improved with proper connection tracking."""
    await websocket.accept()

    # Verify conversation exists
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()
    if not conversation:
        await websocket.close(code=1008, reason="Conversation not found")
        return

    # Generate client ID
    client_id = str(uuid4())

    # Store websocket
    websocket_registry[client_id] = websocket

    # Initialize session data
    user_color = get_user_color(user_id)
    session_data = {
        "conversation_id": conversation_id,
        "user_id": user_id,
        "name": name,
        "color": user_color,
        "cursor": None,
        "last_seen": datetime.utcnow().isoformat(),
        "websocket": websocket
    }

    connected_clients[client_id] = session_data

    # Add to active sessions
    if conversation_id not in active_sessions:
        active_sessions[conversation_id] = {}

    active_sessions[conversation_id][user_id] = {
        "name": name,
        "color": user_color,
        "cursor": None,
        "last_seen": datetime.utcnow().isoformat(),
        "client_id": client_id
    }

    # Notify other users that this user joined
    await broadcast_v2(
        conversation_id,
        {
            "event_type": "join",
            "user_id": user_id,
            "name": name,
            "color": user_color,
            "timestamp": datetime.utcnow().isoformat()
        },
        exclude_client=client_id
    )

    # Send current active users to the new user
    active_users = []
    for uid, data in active_sessions[conversation_id].items():
        active_users.append({
            "user_id": uid,
            "name": data["name"],
            "color": data["color"],
            "cursor": data.get("cursor"),
            "last_seen": data["last_seen"]
        })

    await websocket.send_json({
        "event_type": "presence",
        "data": {"active_users": active_users}
    })

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            event_type = data.get("event_type")

            # Update last seen
            now = datetime.utcnow().isoformat()
            if conversation_id in active_sessions and user_id in active_sessions[conversation_id]:
                active_sessions[conversation_id][user_id]["last_seen"] = now

            if event_type == "cursor":
                # Update cursor position
                cursor_data = data.get("data", {})

                if conversation_id in active_sessions and user_id in active_sessions[conversation_id]:
                    active_sessions[conversation_id][user_id]["cursor"] = cursor_data

                # Broadcast cursor update to other users
                await broadcast_v2(
                    conversation_id,
                    {
                        "event_type": "cursor",
                        "user_id": user_id,
                        "name": name,
                        "color": user_color,
                        "data": cursor_data,
                        "timestamp": now
                    },
                    exclude_client=client_id
                )

            elif event_type == "edit":
                # Broadcast edit to other users
                edit_data = data.get("data", {})
                await broadcast_v2(
                    conversation_id,
                    {
                        "event_type": "edit",
                        "user_id": user_id,
                        "name": name,
                        "color": user_color,
                        "data": edit_data,
                        "timestamp": now
                    },
                    exclude_client=client_id
                )

            elif event_type == "ping":
                # Respond to ping (keepalive)
                await websocket.send_json({
                    "event_type": "pong",
                    "timestamp": now
                })

    except (WebSocketDisconnect, Exception) as e:
        # Handle disconnect
        await handle_disconnect_v2(client_id, conversation_id, user_id, name, user_color)


async def broadcast_v2(conversation_id: str, message: dict, exclude_client: Optional[str] = None):
    """Broadcast a message to all clients in a conversation."""
    # Find all clients in this conversation
    for client_id, session_data in connected_clients.items():
        if session_data["conversation_id"] == conversation_id:
            if exclude_client is None or client_id != exclude_client:
                try:
                    websocket = session_data.get("websocket")
                    if websocket:
                        await websocket.send_json(message)
                except Exception:
                    # Client may have disconnected, clean up
                    if client_id in connected_clients:
                        del connected_clients[client_id]


async def handle_disconnect_v2(client_id: str, conversation_id: str, user_id: str, name: str, color: str):
    """Handle user disconnection."""
    # Remove from connected clients
    if client_id in connected_clients:
        del connected_clients[client_id]

    # Remove from websocket registry
    if client_id in websocket_registry:
        del websocket_registry[client_id]

    # Remove from active sessions
    if conversation_id in active_sessions and user_id in active_sessions[conversation_id]:
        # Only remove if this is the same client
        session = active_sessions[conversation_id][user_id]
        if session.get("client_id") == client_id:
            del active_sessions[conversation_id][user_id]
            # Clean up empty conversation
            if not active_sessions[conversation_id]:
                del active_sessions[conversation_id]

    # Notify other users that this user left
    await broadcast_v2(
        conversation_id,
        {
            "event_type": "leave",
            "user_id": user_id,
            "name": name,
            "color": color,
            "timestamp": datetime.utcnow().isoformat()
        },
        exclude_client=None
    )
