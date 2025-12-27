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
        if any(word in actual_message.lower() for word in ["plan", "build", "create", "write", "implement"]):
            self._thread_state["todos"] = [
                {"id": str(uuid4()), "content": "Analyze requirements", "status": "completed"},
                {"id": str(uuid4()), "content": "Plan implementation", "status": "in_progress"},
                {"id": str(uuid4()), "content": "Execute tasks", "status": "pending"},
            ]
            response_text += "\n\nI've created a todo list to track this task."

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
        [System Instructions: <instructions>]\n\n<actual_message>

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

        # Check for custom instructions test
        if custom_instructions:
            if "spanish" in custom_instructions.lower():
                return f"Hola! Te respondo en español como solicitaste. {user_message} es una pregunta interesante."
            elif "shout" in custom_instructions.lower():
                return f"{user_message.upper()}! THIS IS A SHOUTING RESPONSE!"
            else:
                return f"Following instructions: {custom_instructions}. Response to: {user_message}"

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
        import random
        messages = input_data.get("messages", [])
        last_message = messages[-1] if messages else None
        content = last_message.content if last_message else ""
        thread_id = config.get("configurable", {}).get("thread_id", str(uuid4()))

        # Get model parameters from config
        extended_thinking = (
            config.get("configurable", {}).get("extended_thinking", False) or
            input_data.get("extended_thinking", False)
        )
        temperature = config.get("configurable", {}).get("temperature", 0.7)
        max_tokens = config.get("configurable", {}).get("max_tokens", 4096)

        # Extract custom instructions
        custom_instructions, actual_content = self._extract_custom_instructions(content)

        # Check if we should simulate tool usage
        if any(word in actual_content.lower() for word in ["read", "file", "write", "edit"]):
            # Tool start - matches LangGraph format
            yield {
                "event": "on_tool_start",
                "name": "read_file",
                "data": {"input": {"/example/file.txt": "example"}},
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
        response_text = self._generate_mock_response(actual_content, custom_instructions)

        # Apply temperature effect: higher temp = more creative/wordy, lower = concise
        if temperature < 0.3:
            # Very focused, remove fluff
            response_text = response_text.replace("I'll help you with this. Let me break it down:\n\n", "")
            response_text = response_text.replace("I've created a todo list to track progress.", "")
        elif temperature > 0.8:
            # More creative, add some variation
            creative_additions = [
                "\n\nHere's a creative approach to consider!",
                "\n\nLet me explore this from multiple angles.",
                "\n\nThis is an interesting problem with several solutions.",
            ]
            response_text += random.choice(creative_additions)

        # Add todo simulation for complex tasks
        if any(word in actual_content.lower() for word in ["plan", "build", "create", "write", "implement"]):
            self._thread_state["todos"] = [
                {"id": str(uuid4()), "content": "Analyze requirements", "status": "completed"},
                {"id": str(uuid4()), "content": "Plan implementation", "status": "in_progress"},
                {"id": str(uuid4()), "content": "Execute tasks", "status": "pending"},
            ]
            if temperature >= 0.3:  # Only add if not ultra-concise
                response_text += "\n\nI'll help you with this. Let me break it down:\n\n"
                response_text += "1. Analyze the requirements\n2. Plan the implementation\n3. Execute the tasks\n\n"
                response_text += "I've created a todo list to track progress."

        # Apply max_tokens limit (roughly - count words and truncate)
        words = response_text.split()
        if len(words) > max_tokens:
            response_text = " ".join(words[:max_tokens]) + "... (truncated)"

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
        words = response_text.split()
        for i, word in enumerate(words):
            # Adjust speed based on temperature (higher temp = slightly faster simulation)
            delay = 0.02 if temperature > 0.5 else 0.03
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


class MockChunk:
    """Mock chunk for streaming simulation."""

    def __init__(self, content: str):
        self.content = content
