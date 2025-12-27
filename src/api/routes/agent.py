"""Agent interaction endpoints with DeepAgents integration."""

import json
from typing import Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, Request, Depends
from langchain_core.messages import HumanMessage
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.database import get_db
from src.services.agent_service import agent_service

router = APIRouter()


async def get_effective_custom_instructions(
    conversation_id: Optional[str],
    db: AsyncSession
) -> tuple[str, str]:
    """
    Get effective custom instructions for a conversation.

    Returns a tuple of (project_instructions, global_instructions).
    Project instructions take precedence over global instructions.
    """
    from src.api.routes.settings import user_settings
    from sqlalchemy import select
    from src.models.conversation import Conversation
    from src.models.project import Project

    global_instructions = user_settings.get("custom_instructions", "")
    project_instructions = ""

    if conversation_id:
        # Get conversation to find its project
        result = await db.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        conversation = result.scalar_one_or_none()

        if conversation and conversation.project_id:
            # Get project custom instructions
            result = await db.execute(
                select(Project).where(Project.id == conversation.project_id)
            )
            project = result.scalar_one_or_none()

            if project and project.custom_instructions:
                project_instructions = project.custom_instructions

    return project_instructions, global_instructions


class AgentRequest(BaseModel):
    """Request model for agent invocation."""

    message: str
    conversation_id: Optional[UUID] = None
    thread_id: Optional[str] = None
    model: str = "claude-sonnet-4-5-20250929"
    permission_mode: str = "default"
    extended_thinking: bool = False
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 4096
    custom_instructions: Optional[str] = None
    system_prompt_override: Optional[str] = None


class InterruptDecision(BaseModel):
    """Request model for HITL interrupt decisions."""

    thread_id: str
    decision: str  # approve, edit, reject
    edited_input: Optional[dict] = None


# Thread state storage
thread_states: dict[str, dict] = {}
pending_approvals: dict[str, dict] = {}


@router.post("/invoke")
async def invoke_agent(
    data: AgentRequest,
    db: AsyncSession = Depends(get_db)
) -> dict:
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

        # Get effective custom instructions (project overrides global)
        project_instructions, global_instructions = await get_effective_custom_instructions(
            str(data.conversation_id) if data.conversation_id else None,
            db
        )

        # Use explicitly provided instructions, or fall back to effective instructions
        effective_instructions = data.custom_instructions
        if not effective_instructions or not effective_instructions.strip():
            # Use project instructions if available, otherwise global
            effective_instructions = project_instructions if project_instructions else global_instructions

        # Prepare message with custom instructions if provided
        message_content = data.message
        if effective_instructions and effective_instructions.strip():
            message_content = f"[System Instructions: {effective_instructions}]\n\n{data.message}"

        # Invoke agent with message and parameters
        config = {
            "configurable": {
                "thread_id": thread_id,
                "temperature": data.temperature,
                "max_tokens": data.max_tokens,
                "custom_instructions": effective_instructions,
                "system_prompt_override": data.system_prompt_override,
            }
        }
        result = agent.invoke({"messages": [HumanMessage(content=message_content)]}, config=config)

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
async def stream_agent(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> EventSourceResponse:
    """Stream agent responses via Server-Sent Events."""
    data = await request.json()
    message = data.get("message", "")
    thread_id = data.get("thread_id") or str(uuid4())
    model = data.get("model", "claude-sonnet-4-5-20250929")
    permission_mode = data.get("permission_mode", "default")
    extended_thinking = data.get("extended_thinking", False)
    temperature = data.get("temperature", 0.7)
    max_tokens = data.get("max_tokens", 4096)
    custom_instructions = data.get("custom_instructions", "")
    conversation_id = data.get("conversation_id")

    async def event_generator():
        """Generate SSE events for agent response."""
        try:
            # Start event
            yield {
                "event": "start",
                "data": json.dumps({"thread_id": thread_id, "model": model, "temperature": temperature, "max_tokens": max_tokens}),
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

            # Get effective custom instructions (project overrides global)
            project_instructions, global_instructions = await get_effective_custom_instructions(
                str(conversation_id) if conversation_id else None,
                db
            )

            # Use explicitly provided instructions, or fall back to effective instructions
            effective_instructions = custom_instructions
            if not effective_instructions or not effective_instructions.strip():
                # Use project instructions if available, otherwise global
                effective_instructions = project_instructions if project_instructions else global_instructions

            # Stream agent response with extended thinking support
            # Pass temperature, max_tokens, custom_instructions, and system_prompt_override in config for mock agent to use

            # Prepare message with custom instructions if provided (same as invoke endpoint)
            message_content = message
            if effective_instructions and effective_instructions.strip():
                message_content = f"[System Instructions: {effective_instructions}]\n\n{message}"

            config = {
                "configurable": {
                    "thread_id": thread_id,
                    "extended_thinking": extended_thinking,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "custom_instructions": effective_instructions,
                }
            }

            # Track thinking content when extended thinking is enabled
            thinking_content = ""

            # Send thinking status indicator first
            if extended_thinking:
                yield {
                    "event": "thinking",
                    "data": json.dumps({"status": "thinking"}),
                }

            async for event in agent.astream_events(
                {"messages": [HumanMessage(content=message_content)]},
                config=config,
                version="v2",
            ):
                event_kind = event.get("event", "")

                # Handle thinking events from mock agent
                if extended_thinking and event_kind == "on_chain_stream" and event.get("name") == "think_step":
                    chunk = event.get("data", {}).get("chunk", {})
                    content = chunk.content if hasattr(chunk, 'content') else ""
                    if content:
                        thinking_content += content
                        yield {
                            "event": "thinking",
                            "data": json.dumps({"content": content}),
                        }
                    continue

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

            # Done event with thinking content if extended thinking was enabled
            done_data = {"thread_id": thread_id}
            if extended_thinking and thinking_content:
                done_data["thinking_content"] = thinking_content
            yield {
                "event": "done",
                "data": json.dumps(done_data),
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
