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

        # Extract custom instructions and actual message
        custom_instructions, actual_message = self._extract_custom_instructions(content)

        # Get model parameters from config
        extended_thinking = (
            config.get("configurable", {}).get("extended_thinking", False) or
            input_data.get("extended_thinking", False)
        )
        temperature = config.get("configurable", {}).get("temperature", 0.7)
        max_tokens = config.get("configurable", {}).get("max_tokens", 4096)

        # Check if we should simulate tool usage
        if any(word in actual_message.lower() for word in ["read", "file", "write", "edit"]):
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
        response_text = self._generate_mock_response(actual_message, custom_instructions)

        # Add todo simulation for complex tasks
        if any(word in actual_message.lower() for word in ["plan", "build", "create", "write", "implement"]):
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


class MockChunk:
    """Mock chunk for streaming simulation."""

    def __init__(self, content: str):
        self.content = content
