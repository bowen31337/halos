"""Agent interaction endpoints with DeepAgents integration."""

import json
from typing import Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from src.core.config import settings

router = APIRouter()


class AgentRequest(BaseModel):
    """Request model for agent invocation."""

    message: str
    conversation_id: Optional[UUID] = None
    thread_id: Optional[str] = None
    model: str = "claude-sonnet-4-5-20250929"
    permission_mode: str = "default"
    extended_thinking: bool = False


class InterruptDecision(BaseModel):
    """Request model for HITL interrupt decisions."""

    thread_id: str
    decision: str  # approve, edit, reject
    edited_input: Optional[dict] = None


# Thread state storage
thread_states: dict[str, dict] = {}
pending_approvals: dict[str, dict] = {}


@router.post("/invoke")
async def invoke_agent(data: AgentRequest) -> dict:
    """Synchronously invoke the agent and return complete response."""
    # TODO: Implement full DeepAgents integration
    thread_id = data.thread_id or str(uuid4())

    return {
        "thread_id": thread_id,
        "response": f"Agent response to: {data.message}",
        "model": data.model,
        "status": "completed",
    }


@router.post("/stream")
async def stream_agent(request: Request) -> EventSourceResponse:
    """Stream agent responses via Server-Sent Events."""
    data = await request.json()
    message = data.get("message", "")
    thread_id = data.get("thread_id") or str(uuid4())
    model = data.get("model", "claude-sonnet-4-5-20250929")
    permission_mode = data.get("permission_mode", "default")

    async def event_generator():
        """Generate SSE events for agent response."""
        try:
            # Start event
            yield {
                "event": "start",
                "data": json.dumps({"thread_id": thread_id, "model": model}),
            }

            # TODO: Integrate with DeepAgents
            # For now, return a mock response
            response_text = f"This is a streaming response to: {message}"

            # Stream response word by word
            words = response_text.split()
            for i, word in enumerate(words):
                yield {
                    "event": "message",
                    "data": json.dumps({"content": word + " "}),
                }

            # Done event
            yield {
                "event": "done",
                "data": json.dumps({"thread_id": thread_id}),
            }

        except Exception as e:
            yield {
                "event": "error",
                "data": json.dumps({"error": str(e)}),
            }

    return EventSourceResponse(event_generator())


@router.post("/interrupt")
async def handle_interrupt(data: InterruptDecision) -> dict:
    """Handle human-in-the-loop interrupt decisions."""
    thread_id = data.thread_id

    if thread_id not in pending_approvals:
        raise HTTPException(status_code=404, detail="No pending approval for this thread")

    approval = pending_approvals[thread_id]
    decision = data.decision

    if decision not in ["approve", "edit", "reject"]:
        raise HTTPException(status_code=400, detail="Invalid decision. Must be approve, edit, or reject")

    # Process the decision
    result = {
        "thread_id": thread_id,
        "decision": decision,
        "tool": approval.get("tool"),
        "status": "resumed" if decision in ["approve", "edit"] else "rejected",
    }

    if decision == "edit" and data.edited_input:
        result["edited_input"] = data.edited_input

    # Clear pending approval
    del pending_approvals[thread_id]

    return result


@router.get("/state/{thread_id}")
async def get_agent_state(thread_id: str) -> dict:
    """Get the current state of an agent thread."""
    if thread_id not in thread_states:
        return {"thread_id": thread_id, "state": None, "message": "Thread not found"}

    return {
        "thread_id": thread_id,
        "state": thread_states[thread_id],
    }


@router.get("/todos/{thread_id}")
async def get_todos(thread_id: str) -> dict:
    """Get the todo list for an agent thread."""
    state = thread_states.get(thread_id, {})
    todos = state.get("todos", [])

    return {
        "thread_id": thread_id,
        "todos": todos,
    }


@router.get("/files/{thread_id}")
async def get_workspace_files(thread_id: str) -> dict:
    """Get the workspace files for an agent thread."""
    state = thread_states.get(thread_id, {})
    files = state.get("files", [])

    return {
        "thread_id": thread_id,
        "files": files,
    }
