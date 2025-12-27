"""Mock agent for testing without API keys."""

import asyncio
import re
from typing import Any, AsyncIterator, Dict, List, Optional
from uuid import uuid4

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage


class MockAgent:
    """A mock agent that simulates deepagent behavior for testing."""

    def __init__(self, system_prompt: str = ""):
        self.system_prompt = system_prompt
        self._thread_state: Dict[str, Any] = {}

    def invoke(self, input_data: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Synchronous invoke that returns a mock response."""
        messages = input_data.get("messages", [])
        last_message = messages[-1] if messages else None
        content = last_message.content if last_message else ""

        # Extract custom instructions and actual message
        custom_instructions, actual_message = self._extract_custom_instructions(content)

        # Get model parameters from config
        temperature = config.get("configurable", {}).get("temperature", 0.7) if config else 0.7
        max_tokens = config.get("configurable", {}).get("max_tokens", 4096) if config else 4096

        # Simulate response with markdown for testing
        response_text = self._generate_mock_response(actual_message, custom_instructions)

        # Add mock todos if message is complex
        if any(word in actual_message.lower() for word in ["plan", "build", "create", "write", "implement", "task"]):
            self._thread_state["todos"] = [
                {"id": str(uuid4()), "content": "Analyze requirements", "status": "completed"},
                {"id": str(uuid4()), "content": "Plan implementation", "status": "in_progress"},
                {"id": str(uuid4()), "content": "Execute tasks", "status": "pending"},
            ]
            response_text += "\n\nI've created a todo list to track this task."

        # Add mock files if message mentions files or writing
        if any(word in actual_message.lower() for word in ["file", "write", "create", "code", "script"]):
            if "files" not in self._thread_state:
                self._thread_state["files"] = []

            # Only add files if they don't already exist (avoid duplicates)
            existing_file_names = [f.get("name") for f in self._thread_state["files"]]

            if "main.py" not in existing_file_names:
                self._thread_state["files"].append({
                    "id": str(uuid4()),
                    "name": "main.py",
                    "path": "main.py",
                    "content": "# Main application file\n\ndef main():\n    print('Hello, World!')\n\nif __name__ == '__main__':\n    main()",
                    "size": 85,
                    "file_type": "text/x-python",
                    "created_at": "2024-01-01T00:00:00Z"
                })

            if "utils.py" not in existing_file_names:
                self._thread_state["files"].append({
                    "id": str(uuid4()),
                    "name": "utils.py",
                    "path": "src/utils.py",
                    "content": "# Utility functions\n\ndef helper_function():\n    return 'helper'\n",
                    "size": 58,
                    "file_type": "text/x-python",
                    "created_at": "2024-01-01T00:00:00Z"
                })

        # Apply temperature effect
        if temperature > 0.8:
            response_text = f"(Creative mode - temp {temperature})\n\n{response_text}"
        elif temperature < 0.3:
            response_text = f"(Focused mode - temp {temperature})\n\n{response_text}"

        # Apply max_tokens limit
        max_chars = max_tokens * 4
        if len(response_text) > max_chars:
            response_text = response_text[:max_chars] + "... [truncated due to max_tokens limit]"

        return {
            "messages": [
                AIMessage(content=response_text),
            ],
            "todos": self._thread_state.get("todos", []),
        }

    def _extract_custom_instructions(self, message: str) -> tuple[str, str]:
        """Extract custom instructions from message.

        Custom instructions are prepended in format:
        [System Instructions: <instructions>]

<actual_message>

        Returns:
            tuple: (custom_instructions, actual_message)
        """
        # Pattern: [System Instructions: ...] followed by newlines
        pattern = r'^\[System Instructions:\s*([^\]]+)\]\s*\n\n(.*)$'
        match = re.match(pattern, message, re.DOTALL)

        if match:
            custom_instructions = match.group(1).strip()
            actual_message = match.group(2).strip()
            return custom_instructions, actual_message

        return "", message

    def _generate_mock_response(self, user_message: str, custom_instructions: str = "") -> str:
        """Generate a mock response with markdown formatting for testing."""
        user_lower = user_message.lower()

        # Handle custom instructions
        if custom_instructions:
            ci_lower = custom_instructions.lower()

            # Spanish instruction
            if "spanish" in ci_lower or "español" in ci_lower:
                return f"¡Hola! {user_message} - Responding in Spanish as requested. ¿Cómo puedo ayudarte hoy?"

            # French instruction
            elif "french" in ci_lower or "français" in ci_lower:
                return f"Bonjour! {user_message} - Réponse en français comme demandé. Comment puis-je vous aider?"

            # Short/concise instruction
            elif "short" in ci_lower or "concise" in ci_lower or "brief" in ci_lower:
                return f"Answer: {user_message} - Short response as requested."

            # Verbose/detailed instruction
            elif "verbose" in ci_lower or "detailed" in ci_lower or "long" in ci_lower:
                return f"Detailed response to: {user_message}. I will provide a comprehensive answer with multiple points and explanations, ensuring thorough coverage of the topic."

            # Custom format instruction
            elif "format" in ci_lower:
                return f"""[FORMATTED RESPONSE]

{user_message}

(Formatted as requested in custom instructions)"""

            # Generic custom instruction
            else:
                return f"""[Following custom instructions: {custom_instructions}]

Response to: {user_message}"""

        # Check for markdown test requests
        if any(word in user_lower for word in ["markdown", "format", "heading", "bold"]):
            return """# Heading 1
## Heading 2
### Heading 3

This is a **bold** text and this is *italic* text.

Here's a list:
- Item 1
- Item 2
- Item 3

Numbered list:
1. First
2. Second
3. Third

> This is a blockquote

And a [link](https://example.com)"""

        # Check for code test requests
        if any(word in user_lower for word in ["code", "python", "function", "javascript"]):
            return """Here's a Python code example:

```python
def greet(name: str) -> str:
    return f"Hello, {name}!"

print(greet("World"))
```

And here's some JavaScript:

```javascript
function greet(name) {
    return `Hello, ${name}!`;
}

console.log(greet("World"));
```"""

        # Default response
        return f"Mock response to: {user_message}"

    async def astream_events(
        self, input_data: Dict[str, Any], config: Optional[Dict[str, Any]] = None, version: str = "v2"
    ) -> AsyncIterator[Dict[str, Any]]:
        """Async stream events that simulates real agent streaming.

        This mimics the LangGraph astream_events format which returns:
        {
            "event": "on_chat_model_stream" | "on_tool_start" | "on_tool_end",
            "data": {...},
            "name": "tool_name" (for tool events)
        }
        """
        messages = input_data.get("messages", [])
        last_message = messages[-1] if messages else None
        content = last_message.content if last_message else ""
        thread_id = config.get("configurable", {}).get("thread_id", str(uuid4()))
        permission_mode = config.get("configurable", {}).get("permission_mode", "auto")

        # Extract custom instructions and actual message
        custom_instructions, actual_message = self._extract_custom_instructions(content)

        # Get model parameters from config
        extended_thinking = (
            config.get("configurable", {}).get("extended_thinking", False) or
            input_data.get("extended_thinking", False)
        )
        temperature = config.get("configurable", {}).get("temperature", 0.7)
        max_tokens = config.get("configurable", {}).get("max_tokens", 4096)
        memory_enabled = config.get("configurable", {}).get("memory_enabled", True)

        # Check if user wants to save a memory
        remember_keywords = ["remember", "save", "keep in mind", "note that", "my favorite", "i prefer", "i like"]
        if memory_enabled and any(word in actual_message.lower() for word in remember_keywords):
            # Extract what to remember (simple heuristic)
            # Pattern: "remember that X" or "my favorite is X"
            memory_content = actual_message
            for prefix in ["remember that", "remember", "save that", "note that", "keep in mind that"]:
                if actual_message.lower().startswith(prefix):
                    memory_content = actual_message[len(prefix):].strip()
                    break

            # Detect category
            category = "fact"
            if any(word in actual_message.lower() for word in ["favorite", "prefer", "like", "love", "enjoy"]):
                category = "preference"

            # Emit memory save event
            yield {
                "event": "on_custom_event",
                "name": "memory_save",
                "data": {
                    "content": memory_content,
                    "category": category,
                    "source_conversation_id": thread_id,
                },
            }

            # Confirm memory save
            confirmation = f"I'll remember that: {memory_content}"
            await asyncio.sleep(0.05)

            # Stream confirmation word by word
            for word in confirmation.split():
                await asyncio.sleep(0.03)
                yield {
                    "event": "on_chat_model_stream",
                    "data": {
                        "chunk": AIMessage(content=word + " "),
                    },
                    "name": "ChatAnthropic",
                }

            # End with done event
            yield {
                "event": "on_chain_end",
                "data": {
                    "input_tokens": len(actual_message.split()),
                    "output_tokens": len(confirmation.split()),
                    "cache_read_tokens": 0,
                    "cache_write_tokens": 0,
                },
            }
            return

        # Check if user is asking about something from memory
        # This will emit memories that might be relevant to the query
        if memory_enabled:
            query_keywords = ["what is my", "my favorite", "i prefer", "remember", "do you know"]
            if any(word in actual_message.lower() for word in query_keywords):
                # Emit memory retrieval event - backend will search memories
                # For mock, we'll just emit the event with the query
                yield {
                    "event": "on_custom_event",
                    "name": "memory_retrieve",
                    "data": {
                        "query": actual_message,
                    },
                }

        # Determine interrupt configuration based on permission mode
        # This matches what agent_service does
        interrupt_config = {}
        if permission_mode == "default":
            interrupt_config = {"execute": True, "write_file": True, "edit_file": True}
        elif permission_mode == "acceptEdits":
            interrupt_config = {"execute": True}
        # plan and bypassPermissions modes have no interrupts

        # Also support UI permission modes (auto, manual)
        # manual = default (all tools require approval)
        # auto = bypassPermissions (no approvals needed)
        if permission_mode == "manual":
            interrupt_config = {"execute": True, "write_file": True, "edit_file": True}
        elif permission_mode == "auto":
            interrupt_config = {}  # No interrupts

        # Check if we should simulate execute tool usage
        execute_keywords = ["execute", "run", "command", "shell", "bash", "terminal"]
        if any(word in actual_message.lower() for word in execute_keywords):
            tool_name = "execute"
            tool_input = {"command": actual_message}

            # Tool start - matches LangGraph format
            yield {
                "event": "on_tool_start",
                "name": tool_name,
                "data": {"input": tool_input},
            }
            await asyncio.sleep(0.1)

            # Check if this tool should interrupt based on permission mode
            if interrupt_config.get(tool_name, False):
                yield {
                    "event": "on_interrupt",
                    "name": "approval_required",
                    "data": {
                        "tool": tool_name,
                        "input": tool_input,
                        "reason": "Shell command execution requires approval in default permission mode"
                    },
                }
                # Stop the stream here - will be resumed after approval
                return

            # Tool end - matches LangGraph format
            yield {
                "event": "on_tool_end",
                "name": tool_name,
                "data": {"output": f"Command executed successfully: {actual_message}"},
            }
            await asyncio.sleep(0.1)

        # Check if user wants to use glob to find files
        glob_keywords = ["glob", "find files", "search for files", "list all files", "file pattern"]
        if any(word in actual_message.lower() for word in glob_keywords):
            tool_name = "glob"

            # Extract glob pattern from message
            # Look for patterns like **/*.py or src/**/*.ts
            import re
            pattern_match = re.search(r'[\*{}\[\]\?]+[^\s]*', actual_message)
            if pattern_match:
                glob_pattern = pattern_match.group(0)
            elif "python" in actual_message.lower() or ".py" in actual_message:
                glob_pattern = "**/*.py"
            elif "typescript" in actual_message.lower() or ".ts" in actual_message:
                glob_pattern = "**/*.ts"
            elif "markdown" in actual_message.lower() or ".md" in actual_message:
                glob_pattern = "**/*.md"
            elif "test" in actual_message.lower():
                glob_pattern = "**/*test*.py"
            elif "src" in actual_message.lower():
                glob_pattern = "src/**/*.py"
            else:
                glob_pattern = "**/*"

            tool_input = {"pattern": glob_pattern}

            # Tool start - matches LangGraph format
            yield {
                "event": "on_tool_start",
                "name": tool_name,
                "data": {"input": tool_input},
            }
            await asyncio.sleep(0.1)

            # Tool end - return mock results based on pattern
            # Simulate finding files
            mock_files = []
            if ".py" in glob_pattern:
                mock_files = ["main.py", "app.py", "utils.py", "config.py"]
                if "src" in glob_pattern:
                    mock_files = ["src/main.py", "src/utils.py", "src/config.py"]
            elif ".ts" in glob_pattern:
                mock_files = ["index.ts", "App.tsx", "utils.ts"]
                if "src" in glob_pattern:
                    mock_files = ["src/index.ts", "src/App.tsx", "src/components/Header.tsx"]
            elif ".md" in glob_pattern:
                mock_files = ["README.md", "CHANGELOG.md", "docs/api.md"]
            else:
                mock_files = ["file1.txt", "file2.txt", "file3.txt"]

            yield {
                "event": "on_tool_end",
                "name": tool_name,
                "data": {"output": f"Found {len(mock_files)} files matching pattern '{glob_pattern}':\n" + "\n".join(f"  {f}" for f in mock_files)},
            }
            await asyncio.sleep(0.1)

        # Check if user wants to use grep to search file contents
        grep_keywords = ["grep", "search in files", "find in files", "search for", "search content"]
        if any(word in actual_message.lower() for word in grep_keywords) and not any(word in actual_message.lower() for word in ["glob", "find files"]):
            tool_name = "grep"

            # Extract search pattern
            # Look for quoted strings or keywords
            pattern_match = re.search(r'"([^"]+)"', actual_message)
            if pattern_match:
                search_pattern = pattern_match.group(1)
            elif re.search(r"'([^']+)'", actual_message):
                search_pattern = re.search(r"'([^']+)'", actual_message).group(1)
            else:
                # Extract key search term
                words = actual_message.lower().split()
                stop_words = ["search", "find", "grep", "for", "in", "files", "content", "with", "pattern"]
                search_pattern = next((w for w in words if w not in stop_words and len(w) > 2), "pattern")

            tool_input = {"pattern": search_pattern, "path": "."}

            # Tool start
            yield {
                "event": "on_tool_start",
                "name": tool_name,
                "data": {"input": tool_input},
            }
            await asyncio.sleep(0.1)

            # Tool end - return mock results
            mock_matches = [
                f"main.py:42: def {search_pattern}()",
                f"utils.py:15: # TODO: Implement {search_pattern}",
                f"app.py:78: {search_pattern} = True",
            ]

            yield {
                "event": "on_tool_end",
                "name": tool_name,
                "data": {"output": f"Found {len(mock_matches)} matches for '{search_pattern}':\n" + "\n".join(f"  {m}" for m in mock_matches)},
            }
            await asyncio.sleep(0.1)

        # Check if we should simulate file tool usage
        elif any(word in actual_message.lower() for word in ["read", "write", "edit"]):
            tool_name = "write_file" if any(word in actual_message.lower() for word in ["write", "edit"]) else "read_file"
            tool_input = {"path": "/example/file.txt", "content": "example content"} if tool_name == "write_file" else {"path": "/example/file.txt"}

            # Tool start - matches LangGraph format
            yield {
                "event": "on_tool_start",
                "name": tool_name,
                "data": {"input": tool_input},
            }
            await asyncio.sleep(0.1)

            # Check if this tool should interrupt based on permission mode
            if interrupt_config.get(tool_name, False):
                yield {
                    "event": "on_interrupt",
                    "name": "approval_required",
                    "data": {
                        "tool": tool_name,
                        "input": tool_input,
                        "reason": f"{tool_name} requires approval in {permission_mode} permission mode"
                    },
                }
                # Stop the stream here - will be resumed after approval
                return

            # Tool end - matches LangGraph format
            yield {
                "event": "on_tool_end",
                "name": tool_name,
                "data": {"output": f"Tool {tool_name} executed successfully with input {tool_input}"},
            }
            await asyncio.sleep(0.1)

        # Check if we should simulate sub-agent delegation
        # Trigger sub-agent for messages containing research, code review, documentation, or testing keywords
        sub_agent_keywords = ["research", "investigate", "delegate", "sub-agent", "subagent", "specialist", "expert", "review", "documentation", "docs", "test", "testing"]
        if any(word in actual_message.lower() for word in sub_agent_keywords):
            # Determine which sub-agent to use based on message content
            # Use hyphenated naming to match test expectations
            sub_agent_name = "research-agent"
            task_description = "Gathering information and analyzing the request"

            if "code" in actual_message.lower() or "review" in actual_message.lower():
                sub_agent_name = "code-review-agent"
                task_description = "Analyzing code quality and suggesting improvements"
            elif "doc" in actual_message.lower() or "documentation" in actual_message.lower():
                sub_agent_name = "docs-agent"
                task_description = "Creating comprehensive documentation"
            elif "test" in actual_message.lower():
                sub_agent_name = "test-agent"
                task_description = "Writing and running test cases"

            # Sub-agent start event - emit as on_custom_event which the agent routes handle
            yield {
                "event": "on_custom_event",
                "name": "subagent_start",
                "data": {
                    "subagent": sub_agent_name,
                    "reason": task_description,
                },
            }
            await asyncio.sleep(0.2)

            # Sub-agent progress events (simulate work being done)
            for progress in [20, 40, 60, 80]:
                yield {
                    "event": "on_custom_event",
                    "name": "subagent_progress",
                    "data": {
                        "subagent": sub_agent_name,
                        "progress": progress,
                    },
                }
                await asyncio.sleep(0.15)

            # Sub-agent end event with result
            result = f"Sub-agent {sub_agent_name} completed analysis. Result: The task was successfully delegated and completed."
            yield {
                "event": "on_custom_event",
                "name": "subagent_end",
                "data": {
                    "subagent": sub_agent_name,
                    "output": result,
                },
            }
            await asyncio.sleep(0.1)

            # Add sub-agent result to the response
            response_text = self._generate_mock_response(actual_message, custom_instructions)
            response_text += f"\n\n**Sub-agent {sub_agent_name} Report:**\n\n{result}"

        # Generate response using the same method as invoke
        else:
            response_text = self._generate_mock_response(actual_message, custom_instructions)

        # Add todo simulation for complex tasks
        has_todos = any(word in actual_message.lower() for word in ["plan", "build", "create", "write", "implement", "task"])
        if has_todos:
            self._thread_state["todos"] = [
                {"id": str(uuid4()), "content": "Analyze requirements", "status": "completed"},
                {"id": str(uuid4()), "content": "Plan implementation", "status": "in_progress"},
                {"id": str(uuid4()), "content": "Execute tasks", "status": "pending"},
            ]
            response_text += """

I'll help you with this. Let me break it down:

"""
            response_text += """1. Analyze the requirements
2. Plan the implementation
3. Execute the tasks

"""
            response_text += "I've created a todo list to track progress."

        # Add file simulation for file-related tasks
        has_files = any(word in actual_message.lower() for word in ["file", "write", "create", "code", "script"])
        if has_files:
            if "files" not in self._thread_state:
                self._thread_state["files"] = []

            # Only add files if they don't already exist
            existing_file_names = [f.get("name") for f in self._thread_state["files"]]

            if "main.py" not in existing_file_names:
                self._thread_state["files"].append({
                    "id": str(uuid4()),
                    "name": "main.py",
                    "path": "main.py",
                    "content": "# Main application file\n\ndef main():\n    print('Hello, World!')\n\nif __name__ == '__main__':\n    main()",
                    "size": 85,
                    "file_type": "text/x-python",
                    "created_at": "2024-01-01T00:00:00Z"
                })

            if "utils.py" not in existing_file_names:
                self._thread_state["files"].append({
                    "id": str(uuid4()),
                    "name": "utils.py",
                    "path": "src/utils.py",
                    "content": "# Utility functions\n\ndef helper_function():\n    return 'helper'\n",
                    "size": 58,
                    "file_type": "text/x-python",
                    "created_at": "2024-01-01T00:00:00Z"
                })

        # Apply temperature effect (higher temp = more creative/varied responses)
        # For mock purposes, we'll add some variation based on temperature
        if temperature > 0.8:
            response_text = f"""(Creative mode - temp {temperature})

{response_text}"""
        elif temperature < 0.3:
            response_text = f"""(Focused mode - temp {temperature})

{response_text}"""

        # Apply max_tokens limit (truncate if needed)
        # Rough estimate: 1 token ≈ 4 characters
        max_chars = max_tokens * 4
        if len(response_text) > max_chars:
            response_text = response_text[:max_chars] + "... [truncated due to max_tokens limit]"

        # If extended thinking is enabled, emit thinking events first
        if extended_thinking:
            thinking_phrases = [
                "Let me think about this step by step...",
                "Analyzing the requirements carefully...",
                "Considering different approaches...",
                "Evaluating the best solution...",
                "Synthesizing my thoughts...",
            ]

            for phrase in thinking_phrases:
                await asyncio.sleep(0.05)
                yield {
                    "event": "on_chain_stream",
                    "data": {
                        "chunk": AIMessage(content=phrase + "\n"),
                    },
                    "name": "think_step",
                }

            await asyncio.sleep(0.1)

        # Stream response word by word - matches LangGraph event structure
        # Adjust streaming speed based on temperature (higher temp = slightly slower for "thinking")
        base_delay = 0.02
        delay = base_delay + (0.01 * (1 - temperature))  # Higher temp = slightly slower
        words = response_text.split()

        # Track if we've emitted todos already
        todos_emitted = False

        for i, word in enumerate(words):
            await asyncio.sleep(delay)
            # Use AIMessage as the chunk, which is what LangChain expects
            chunk_content = word + (" " if i < len(words) - 1 else "")
            yield {
                "event": "on_chat_model_stream",
                "data": {
                    "chunk": AIMessage(content=chunk_content),
                },
                "name": "ChatAnthropic",
            }

            # Emit todos mid-stream if they exist and haven't been emitted yet
            # Do this after some content has been streamed (after ~4 words)
            if not todos_emitted and i > 3 and has_todos:
                todos_emitted = True
                yield {
                    "event": "on_custom_event",
                    "name": "todo_update",
                    "data": {"todos": self._thread_state["todos"]},
                }

            # Emit final tokens at the end of streaming
            if i == len(words) - 1:
                yield {
                    "event": "on_chain_end",
                    "data": {
                        "input_tokens": len(actual_message.split()),
                        "output_tokens": len(response_text.split()),
                        "cache_read_tokens": 0,
                        "cache_write_tokens": 0,
                    },
                }


class MockChunk:
    """Mock chunk for streaming simulation."""

    def __init__(self, content: str):
        self.content = content
