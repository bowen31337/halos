"""Agent interaction endpoints with DeepAgents integration."""

import json
import re
from typing import Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, Request, Depends
from langchain_core.messages import HumanMessage, AIMessage
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.core.config import settings
from src.core.database import get_db
from src.services.agent_service import agent_service
from src.models.artifact import Artifact
from src.models.conversation import Conversation
from src.models.memory import Memory

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


async def get_project_files_content(
    conversation_id: Optional[str],
    db: AsyncSession
) -> str:
    """
    Get the content of all files in the project associated with a conversation.

    Returns a formatted string containing file contents for the agent context.
    """
    from src.models.project_file import ProjectFile

    if not conversation_id:
        return ""

    # Get conversation to find its project
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()

    if not conversation or not conversation.project_id:
        return ""

    # Get all files in the project
    result = await db.execute(
        select(ProjectFile)
        .where(ProjectFile.project_id == conversation.project_id)
        .where(ProjectFile.is_deleted == False)
        .where(ProjectFile.content != None)
    )
    files = result.scalars().all()

    if not files:
        return ""

    # Format file contents for the agent
    file_context = "\n\n[PROJECT FILES CONTEXT]\n"
    file_context += "The following files are available in this project:\n\n"

    for file in files:
        file_context += f"--- File: {file.original_filename} ---\n"
        file_context += f"Content:\n{file.content}\n\n"

    file_context += "[END PROJECT FILES CONTEXT]\n\n"
    return file_context


async def get_memory_context(
    conversation_id: Optional[str],
    db: AsyncSession
) -> str:
    """
    Get relevant long-term memories for the agent context.

    Returns a formatted string containing memories for the agent context.
    """
    from src.api.routes.settings import user_settings

    # Check if memory is enabled
    if not user_settings.get("memory_enabled", True):
        return ""

    # Get all active memories
    result = await db.execute(
        select(Memory)
        .where(Memory.is_active == True)
        .order_by(Memory.created_at.desc())
    )
    memories = result.scalars().all()

    if not memories:
        return ""

    # Format memories for the agent
    memory_context = "\n\n[LONG-TERM MEMORY CONTEXT]\n"
    memory_context += "The following are facts and preferences stored in your long-term memory:\n\n"

    for memory in memories:
        memory_context += f"- [{memory.category.upper()}] {memory.content}\n"

    memory_context += "[END LONG-TERM MEMORY CONTEXT]\n\n"
    return memory_context


async def extract_memories_from_response(
    content: str,
    conversation_id: Optional[str],
    db: AsyncSession
) -> list[dict]:
    """
    Extract and store memories from agent response content.

    This function looks for patterns indicating the agent learned something
    about the user that should be stored in long-term memory.

    Returns list of created memories.
    """
    from src.api.routes.settings import user_settings

    # Check if memory is enabled
    if not user_settings.get("memory_enabled", True):
        return []

    # Simple pattern matching for memory extraction
    # Look for phrases like "I remember", "You mentioned", "Your preference is"
    memory_indicators = [
        "remember that",
        "your favorite",
        "you prefer",
        "you like",
        "your preference",
        "you mentioned",
        "you said",
    ]

    content_lower = content.lower()
    created_memories = []

    # Check if content contains memory indicators
    for indicator in memory_indicators:
        if indicator in content_lower:
            # Extract a simple memory - in production, this would use NLP
            # For now, store the relevant sentence or phrase
            memory_content = content[:200]  # Truncate to 200 chars
            if len(memory_content) < 10:
                continue

            # Create memory
            memory = Memory(
                content=memory_content,
                category="preference",
                source_conversation_id=conversation_id,
            )

            db.add(memory)
            await db.commit()
            await db.refresh(memory)

            created_memories.append(memory.to_dict())
            break  # Only extract one memory per response for now

    return created_memories


# Artifact detection constants
LANGUAGE_ALIASES = {
    "javascript": "js",
    "typescript": "ts",
    "python": "py",
    "java": "java",
    "cpp": "cpp",
    "c++": "cpp",
    "csharp": "cs",
    "c#": "cs",
    "go": "go",
    "rust": "rs",
    "ruby": "rb",
    "php": "php",
    "swift": "swift",
    "kotlin": "kt",
    "html": "html",
    "css": "css",
    "json": "json",
    "yaml": "yaml",
    "markdown": "md",
    "bash": "bash",
    "shell": "bash",
    "sql": "sql",
    "graphql": "graphql",
    "xml": "xml",
}

REACT_PATTERNS = [
    r"import\s+.*React",
    r"export\s+default\s+function\s+\w+\([^)]*\)\s*{[^}]*return[^}]*<",
    r"const\s+\w+\s*=\s*\([^)]*\)\s*=>\s*{[^}]*return[^}]*<",
    r"function\s+\w+\([^)]*\)\s*{[^}]*return[^}]*<",
    r"jsx",
    r"tsx",
]


def detect_language(code: str, language_hint: str = "") -> str:
    """Detect the programming language of a code block."""
    if language_hint:
        normalized = language_hint.lower().strip()
        return LANGUAGE_ALIASES.get(normalized, normalized)

    for pattern in REACT_PATTERNS:
        if re.search(pattern, code, re.IGNORECASE):
            return "React/JSX"

    if "def " in code and ":" in code and "import " not in code:
        return "python"
    if "function " in code or "=> " in code or "let " in code or "const " in code:
        return "javascript"
    if "public class " in code or "System.out.println" in code:
        return "java"
    if "#include " in code or "std::" in code:
        return "cpp"
    if "package " in code and "func " in code:
        return "go"

    return "code"


def extract_title_from_code(code: str, language: str) -> str:
    """Extract a meaningful title from code content."""
    patterns = [
        r"function\s+(\w+)",
        r"const\s+(\w+)\s*=\s*\(",
        r"export\s+default\s+function\s+(\w+)",
        r"class\s+(\w+)",
        r"def\s+(\w+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, code)
        if match:
            name = match.group(1)
            if language == "React/JSX" and name[0].islower():
                name = name[0].upper() + name[1:]
            return name

    first_line = code.strip().split('\n')[0]
    if len(first_line) < 50:
        return first_line.strip().strip('/*#').strip()

    return "Code Artifact"


def extract_code_blocks(content: str) -> list[dict]:
    """Extract code blocks from markdown content."""
    pattern = r"```(\w+)?\n(.*?)\n```"
    matches = re.findall(pattern, content, re.DOTALL)

    artifacts = []
    for language_hint, code in matches:
        if not code.strip():
            continue

        language = detect_language(code, language_hint)
        title = extract_title_from_code(code, language)

        # Auto-detect artifact type from language
        language_lower = language.lower()
        if language_lower in ["html", "htm"]:
            artifact_type = "html"
        elif language_lower in ["svg"]:
            artifact_type = "svg"
        elif language_lower in ["mermaid"]:
            artifact_type = "mermaid"
        elif language_lower in ["latex", "tex"]:
            artifact_type = "latex"
        else:
            artifact_type = "code"

        artifacts.append({
            "content": code,
            "language": language,
            "title": title,
            "artifact_type": artifact_type,
        })

    return artifacts


async def create_artifacts_from_response(
    content: str,
    conversation_id: Optional[str],
    db: AsyncSession
) -> list[dict]:
    """
    Detect code blocks in content and create artifacts in the database.
    Returns list of created artifact IDs.
    """
    if not conversation_id:
        return []

    # Extract code blocks
    artifacts_data = extract_code_blocks(content)
    if not artifacts_data:
        return []

    created_artifacts = []

    for artifact_data in artifacts_data:
        artifact = Artifact(
            conversation_id=conversation_id,
            content=artifact_data["content"],
            title=artifact_data["title"],
            language=artifact_data["language"],
            artifact_type=artifact_data["artifact_type"],
        )

        db.add(artifact)
        created_artifacts.append({
            "id": artifact.id,
            "title": artifact.title,
            "content": artifact.content,
            "language": artifact.language,
            "artifact_type": artifact.artifact_type,
            "version": artifact.version,
            "created_at": artifact.created_at.isoformat() if artifact.created_at else None,
        })

    await db.commit()
    return created_artifacts


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

        # Get project files content
        files_content = await get_project_files_content(
            str(data.conversation_id) if data.conversation_id else None,
            db
        )

        # Get long-term memory context
        memory_content = await get_memory_context(
            str(data.conversation_id) if data.conversation_id else None,
            db
        )

        # Use explicitly provided instructions, or fall back to effective instructions
        effective_instructions = data.custom_instructions
        if not effective_instructions or not effective_instructions.strip():
            # Use project instructions if available, otherwise global
            effective_instructions = project_instructions if project_instructions else global_instructions

        # Prepare message with custom instructions and files content if provided
        message_content = data.message
        if effective_instructions and effective_instructions.strip():
            message_content = f"[System Instructions: {effective_instructions}]\n\n{data.message}"

        # Add project files context if available
        if files_content:
            message_content = f"{files_content}{message_content}"

        # Add long-term memory context if available
        if memory_content:
            message_content = f"{memory_content}{message_content}"

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

        # Detect and save artifacts from response
        created_artifacts = []
        if data.conversation_id:
            created_artifacts = await create_artifacts_from_response(
                response_content,
                str(data.conversation_id),
                db
            )

        return {
            "thread_id": thread_id,
            "response": response_content,
            "model": data.model,
            "status": "completed",
            "artifacts": created_artifacts,
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

            # Get project files content
            files_content = await get_project_files_content(
                str(conversation_id) if conversation_id else None,
                db
            )

            # Get long-term memory context
            memory_content = await get_memory_context(
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

            # Prepare message with custom instructions and files content if provided (same as invoke endpoint)
            message_content = message
            if effective_instructions and effective_instructions.strip():
                message_content = f"[System Instructions: {effective_instructions}]\n\n{message}"

            # Add project files context if available
            if files_content:
                message_content = f"{files_content}{message_content}"

            # Add long-term memory context if available
            if memory_content:
                message_content = f"{memory_content}{message_content}"

            config = {
                "configurable": {
                    "thread_id": thread_id,
                    "extended_thinking": extended_thinking,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "custom_instructions": effective_instructions,
                    "permission_mode": data.get("permission_mode", "default"),
                    "memory_enabled": data.get("memory_enabled", True),
                }
            }

            # Track thinking content and full response for artifact detection
            thinking_content = ""
            full_response = ""
            last_todos = None
            last_files = None

            # Send thinking status indicator first
            if extended_thinking:
                yield {
                    "event": "thinking",
                    "data": json.dumps({"status": "thinking"}),
                }

            try:
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
                            full_response += content
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

                    # Interrupt event (HITL - Human in the Loop)
                    elif event_kind == "on_interrupt":
                        event_data = event.get("data", {})
                        tool_name = event_data.get("tool", event.get("name", ""))
                        tool_input = event_data.get("input", {})
                        reason = event_data.get("reason", "Tool execution requires approval")

                        # Store in pending approvals
                        pending_approvals[thread_id] = {
                            "tool": tool_name,
                            "input": tool_input,
                            "reason": reason,
                        }

                        # Emit interrupt event to frontend
                        yield {
                            "event": "interrupt",
                            "data": json.dumps({
                                "tool": tool_name,
                                "input": tool_input,
                                "reason": reason,
                            }),
                        }
                        # Stop streaming - will be resumed after approval
                        # Note: return removed

                    # Handle on_chain_end event (end of streaming with token info)
                    elif event_kind == "on_chain_end":
                        event_data = event.get("data", {})
                        # Extract token information if available
                        input_tokens = event_data.get("input_tokens", 0)
                        output_tokens = event_data.get("output_tokens", 0)
                        cache_read_tokens = event_data.get("cache_read_tokens", 0)
                        cache_write_tokens = event_data.get("cache_write_tokens", 0)

                        # Store token information in thread state for the done event
                        thread_states[thread_id] = thread_states.get(thread_id, {})
                        thread_states[thread_id]["tokens"] = {
                            "input_tokens": input_tokens,
                            "output_tokens": output_tokens,
                            "cache_read_tokens": cache_read_tokens,
                            "cache_write_tokens": cache_write_tokens,
                        }

                    # Handle custom events (e.g., todos from mock agent)
                    elif event_kind == "on_custom_event":
                        event_name = event.get("name", "")
                        if event_name == "todo_update":
                            event_data = event.get("data", {})
                            if "todos" in event_data:
                                todos = event_data["todos"]
                                # Store in thread state
                                thread_states[thread_id] = thread_states.get(thread_id, {})
                                thread_states[thread_id]["todos"] = todos
                                # Emit todos event
                                yield {
                                    "event": "todos",
                                    "data": json.dumps({"todos": todos}),
                                }
                        elif event_name == "subagent_start":
                            # Handle sub-agent delegation start
                            event_data = event.get("data", {})
                            subagent = event_data.get("subagent", "")
                            reason = event_data.get("reason", "")
                            yield {
                                "event": "subagent_start",
                                "data": json.dumps({
                                    "subagent": subagent,
                                    "reason": reason,
                                }),
                            }
                        elif event_name == "subagent_progress":
                            # Handle sub-agent progress update
                            event_data = event.get("data", {})
                            subagent = event_data.get("subagent", "")
                            progress = event_data.get("progress", 0)
                            yield {
                                "event": "subagent_progress",
                                "data": json.dumps({
                                    "subagent": subagent,
                                    "progress": progress,
                                }),
                            }
                        elif event_name == "subagent_end":
                            # Handle sub-agent completion
                            event_data = event.get("data", {})
                            subagent = event_data.get("subagent", "")
                            output = event_data.get("output", "")
                            yield {
                                "event": "subagent_end",
                                "data": json.dumps({
                                    "subagent": subagent,
                                    "output": output,
                                }),
                            }
                        elif event_name == "memory_save":
                            # Handle memory save - save to database
                            event_data = event.get("data", {})
                            memory_content = event_data.get("content", "")
                            category = event_data.get("category", "fact")
                            source_conversation_id = event_data.get("source_conversation_id")

                            if memory_content:
                                try:
                                    memory = Memory(
                                        content=memory_content,
                                        category=category,
                                        source_conversation_id=source_conversation_id,
                                    )
                                    db.add(memory)
                                    await db.commit()

                                    # Notify frontend of successful save
                                    yield {
                                        "event": "memory_saved",
                                        "data": json.dumps({
                                            "content": memory_content,
                                            "category": category,
                                        }),
                                    }
                                except Exception as e:
                                    # Log error but don't fail the stream
                                    print(f"Failed to save memory: {e}")
                        elif event_name == "memory_retrieve":
                            # Handle memory retrieval - search and return relevant memories
                            event_data = event.get("data", {})
                            query = event_data.get("query", "")

                            if query:
                                try:
                                    # Search memories by content
                                    result = await db.execute(
                                        select(Memory)
                                        .where(Memory.content.ilike(f"%{query}%"))
                                        .where(Memory.is_active == True)
                                        .order_by(Memory.created_at.desc())
                                        .limit(5)
                                    )
                                    memories = result.scalars().all()

                                    if memories:
                                        # Emit memories to frontend
                                        yield {
                                            "event": "memories",
                                            "data": json.dumps({
                                                "memories": [m.to_dict() for m in memories],
                                            }),
                                        }
                                except Exception as e:
                                    # Log error but don't fail the stream
                                    print(f"Failed to retrieve memories: {e}")

                # Check for todos in agent state during streaming
                if hasattr(agent, '_thread_state') and 'todos' in agent._thread_state:
                    current_todos = agent._thread_state["todos"]
                    if current_todos != last_todos:
                        last_todos = current_todos
                        yield {
                            "event": "todos",
                            "data": json.dumps({"todos": current_todos}),
                        }

                # Check for files in agent state during streaming
                if hasattr(agent, '_thread_state') and 'files' in agent._thread_state:
                    current_files = agent._thread_state["files"]
                    if current_files != last_files:
                        last_files = current_files
                        yield {
                            "event": "files",
                            "data": json.dumps({"files": current_files}),
                        }

            except Exception as e:
                # Catch any errors during streaming and yield error event
                import traceback
                traceback.print_exc()
                yield {
                    "event": "error",
                    "data": json.dumps({"error": str(e), "type": "streaming_error"}),
                }
                return

            # Detect and create artifacts from the full response
            artifacts = []
            if full_response and conversation_id:
                try:
                    artifacts = await create_artifacts_from_response(
                        full_response,
                        str(conversation_id),
                        db
                    )
                except Exception as e:
                    # Don't fail the response if artifact creation fails
                    print(f"Artifact creation error: {e}")

            # Extract and store memories from the response
            extracted_memories = []
            if full_response and conversation_id:
                try:
                    extracted_memories = await extract_memories_from_response(
                        full_response,
                        str(conversation_id),
                        db
                    )
                except Exception as e:
                    # Don't fail the response if memory extraction fails
                    print(f"Memory extraction error: {e}")

            # Update thread state with todos if agent provided them
            if hasattr(agent, '_thread_state') and 'todos' in agent._thread_state:
                thread_states[thread_id] = thread_states.get(thread_id, {})
                thread_states[thread_id]["todos"] = agent._thread_state["todos"]
                # Emit final todos update
                yield {
                    "event": "todos",
                    "data": json.dumps({"todos": agent._thread_state["todos"]}),
                }

            # Update thread state with files if agent provided them
            if hasattr(agent, '_thread_state') and 'files' in agent._thread_state:
                thread_states[thread_id] = thread_states.get(thread_id, {})
                thread_states[thread_id]["files"] = agent._thread_state["files"]
                # Emit final files update
                yield {
                    "event": "files",
                    "data": json.dumps({"files": agent._thread_state["files"]}),
                }

            # Done event with thinking content and artifacts if available
            done_data = {"thread_id": thread_id}
            if extended_thinking and thinking_content:
                done_data["thinking_content"] = thinking_content
            if artifacts:
                done_data["artifacts"] = artifacts
            if extracted_memories:
                done_data["extracted_memories"] = extracted_memories
            # Include files in done event for immediate UI update
            if hasattr(agent, '_thread_state') and 'files' in agent._thread_state:
                done_data["files"] = agent._thread_state["files"]
            # Include tokens from thread state if available
            if thread_id in thread_states and "tokens" in thread_states[thread_id]:
                done_data.update(thread_states[thread_id]["tokens"])
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


@router.get("/pending-approval/{thread_id}")
async def get_pending_approval(thread_id: str) -> dict:
    """Get pending approval for a thread."""
    if thread_id not in pending_approvals:
        return {"thread_id": thread_id, "pending": False}

    approval = pending_approvals[thread_id]
    return {
        "thread_id": thread_id,
        "pending": True,
        "tool": approval.get("tool"),
        "input": approval.get("input"),
        "reason": approval.get("reason", "Tool execution requires approval"),
    }


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


@router.get("/subagent-results/{thread_id}")
async def get_subagent_results(thread_id: str) -> dict:
    """Get the subagent results for an agent thread."""
    state = thread_states.get(thread_id, {})
    subagent_results = state.get("subagent_results", [])

    return {
        "thread_id": thread_id,
        "subagent_results": subagent_results,
    }


@router.get("/subagents/available")
async def get_available_subagents() -> dict:
    """Get the list of available built-in subagents."""
    return {
        "subagents": [
            {
                "name": "research_agent",
                "description": "Performs web research and information gathering",
                "tools": ["web_search", "browse_page", "summarize"],
            },
            {
                "name": "code_review_agent",
                "description": "Analyzes code for quality, security, and best practices",
                "tools": ["analyze_code", "find_bugs", "suggest_improvements"],
            },
            {
                "name": "documentation_agent",
                "description": "Generates and maintains documentation",
                "tools": ["write_docs", "generate_api_docs", "create_readme"],
            },
            {
                "name": "testing_agent",
                "description": "Creates and runs tests",
                "tools": ["write_tests", "run_tests", "analyze_coverage"],
            },
        ],
    }


@router.post("/subagents/custom")
async def create_custom_subagent(data: dict) -> dict:
    """Create a custom subagent configuration."""
    name = data.get("name")
    description = data.get("description", "")
    tools = data.get("tools", [])
    prompt = data.get("prompt", "")

    if not name:
        raise HTTPException(status_code=400, detail="Subagent name is required")

    return {
        "success": True,
        "subagent": {
            "name": name,
            "description": description,
            "tools": tools,
            "prompt": prompt,
        },
    }


@router.get("/subagents/custom")
async def list_custom_subagents() -> dict:
    """List all custom subagents."""
    return {
        "subagents": [],
    }
