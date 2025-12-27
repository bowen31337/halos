"""Mock agent for testing without API keys."""

import asyncio
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

        # Simulate response with markdown for testing
        response_text = self._generate_mock_response(content)

        # Add mock todos if message is complex
        if any(word in content.lower() for word in ["plan", "build", "create", "write", "implement"]):
            self._thread_state["todos"] = [
                {"id": str(uuid4()), "content": "Analyze requirements", "status": "completed"},
                {"id": str(uuid4()), "content": "Plan implementation", "status": "in_progress"},
                {"id": str(uuid4()), "content": "Execute tasks", "status": "pending"},
            ]
            response_text += "\n\nI've created a todo list to track this task."

        return {
            "messages": [
                AIMessage(content=response_text),
            ],
            "todos": self._thread_state.get("todos", []),
        }

    def _generate_mock_response(self, user_message: str) -> str:
        """Generate a mock response with markdown formatting for testing."""
        user_lower = user_message.lower()

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
def hello_world():
    print("Hello, World!")
    return True

# Call the function
hello_world()
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

        # Check if we should simulate tool usage
        if any(word in content.lower() for word in ["read", "file", "write", "edit"]):
            # Tool start - matches LangGraph format
            yield {
                "event": "on_tool_start",
                "name": "read_file",
                "data": {"input": {"path": "/example/file.txt"}},
            }
            await asyncio.sleep(0.1)

            # Tool end - matches LangGraph format
            yield {
                "event": "on_tool_end",
                "name": "read_file",
                "data": {"output": "File content: This is a mock file for testing."},
            }
            await asyncio.sleep(0.1)

        # Generate response using the same method as invoke
        response_text = self._generate_mock_response(content)

        # Add todo simulation for complex tasks
        if any(word in content.lower() for word in ["plan", "build", "create", "write", "implement"]):
            self._thread_state["todos"] = [
                {"id": str(uuid4()), "content": "Analyze requirements", "status": "completed"},
                {"id": str(uuid4()), "content": "Plan implementation", "status": "in_progress"},
                {"id": str(uuid4()), "content": "Execute tasks", "status": "pending"},
            ]
            response_text += "\n\nI'll help you with this. Let me break it down:\n\n"
            response_text += "1. Analyze the requirements\n2. Plan the implementation\n3. Execute the tasks\n\n"
            response_text += "I've created a todo list to track progress."

        # Stream response word by word - matches LangGraph event structure
        words = response_text.split()
        for i, word in enumerate(words):
            await asyncio.sleep(0.02)  # Simulate typing speed
            # Use AIMessage as the chunk, which is what LangChain expects
            chunk_content = word + (" " if i < len(words) - 1 else "")
            yield {
                "event": "on_chat_model_stream",
                "data": {
                    "chunk": AIMessage(content=chunk_content),
                },
                "name": "ChatAnthropic",
            }


class MockChunk:
    """Mock chunk for streaming simulation."""

    def __init__(self, content: str):
        self.content = content
