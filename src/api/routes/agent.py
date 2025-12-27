"""Agent interaction endpoints with DeepAgents integration."""

import json
from typing import Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, Request
from langchain_core.messages import HumanMessage
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from src.core.config import settings
from src.services.agent_service import agent_service

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
    thread_id = data.thread_id or str(uuid4())

    try:
        # Get or create agent
        agent = agent_service.get_or_create_agent(
            user_id="default",
            permission_mode=data.permission_mode,
            model=data.model,
        )

        if agent is None:
            # Fallback mock response if agent creation failed
            return {
                "thread_id": thread_id,
                "response": f"Agent unavailable. Mock response to: {data.message}",
                "model": data.model,
                "status": "error",
                "error": "Agent creation failed - check API key configuration",
            }

        # Invoke agent with message
        config = {"configurable": {"thread_id": thread_id}}
        result = agent.invoke({"messages": [HumanMessage(content=data.message)]}, config=config)

        # Extract response from result
        response_message = result.get("messages", [])[-1] if result.get("messages") else AIMessage(content="No response")
        response_content = response_message.content if hasattr(response_message, 'content') else str(response_message)

        return {
            "thread_id": thread_id,
            "response": response_content,
            "model": data.model,
            "status": "completed",
        }

    except Exception as e:
        return {
            "thread_id": thread_id,
            "response": f"Error invoking agent: {str(e)}",
            "model": data.model,
            "status": "error",
            "error": str(e),
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

            # Get or create agent
            agent = agent_service.get_or_create_agent(
                user_id="default",
                permission_mode=permission_mode,
                model=model,
            )

            if agent is None:
                # Agent creation failed, return mock response
                response_text = f"Agent unavailable. This is a mock response to: {message}"
                for word in response_text.split():
                    yield {
                        "event": "message",
                        "data": json.dumps({"content": word + " "}),
                    }
                yield {
                    "event": "done",
                    "data": json.dumps({"thread_id": thread_id, "error": "Agent creation failed"}),
                }
                return

            # Stream agent response
            config = {"configurable": {"thread_id": thread_id}}

            async for event in agent.astream_events(
                {"messages": [HumanMessage(content=message)]},
                config=config,
                version="v2",
            ):
                event_kind = event.get("event", "")

                # Stream message content
                if event_kind == "on_chat_model_stream":
                    chunk = event.get("data", {}).get("chunk", {})
                    content = chunk.content if hasattr(chunk, 'content') else ""
                    if content:
                        yield {
                            "event": "message",
                            "data": json.dumps({"content": content}),
                        }

                # Tool start event
                elif event_kind == "on_tool_start":
                    tool_name = event.get("name", "")
                    tool_input = event.get("data", {}).get("input", {})
                    yield {
                        "event": "tool_start",
                        "data": json.dumps({
                            "tool": tool_name,
                            "input": tool_input,
                        }),
                    }

                # Tool end event
                elif event_kind == "on_tool_end":
                    tool_output = event.get("data", {}).get("output", "")
                    yield {
                        "event": "tool_end",
                        "data": json.dumps({"output": str(tool_output)[:500]}),  # Limit output size
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
