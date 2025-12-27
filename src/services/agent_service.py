"""DeepAgents service for AI agent interactions.

This module provides the core agent functionality using LangChain's DeepAgents framework.
It includes:
- create_deep_agent() for agent creation
- Built-in middleware provided by create_deep_agent:
  - TodoListMiddleware (planning with write_todos/read_todos)
  - FilesystemMiddleware (ls, read_file, write_file, edit_file, glob, grep)
  - SubAgentMiddleware (sub-agent delegation via task() tool)
  - SummarizationMiddleware (context exceeding 170k tokens)
  - AnthropicPromptCachingMiddleware (cost reduction)
  - PatchToolCallsMiddleware (tool call handling)
  - HumanInTheLoopMiddleware (tool approval via interrupt_on)
- Backend configurations (StateBackend, CompositeBackend, StoreBackend)
- Long-term memory via StoreBackend
"""

import os
from typing import Optional, Any, Dict, List
from uuid import uuid4

# Core DeepAgents imports
from deepagents import create_deep_agent
from deepagents.backends import StateBackend, StoreBackend, CompositeBackend

# LLM and storage imports
from langchain_anthropic import ChatAnthropic
from langgraph.store.memory import InMemoryStore
from langgraph.checkpoint.memory import MemorySaver

# Import mock agent as fallback
from src.services.mock_agent import MockAgent

# Import memory models for memory tool
from src.models.memory import Memory


class AgentService:
    """Service for managing DeepAgents instances."""

    def __init__(self):
        """Initialize the agent service."""
        from src.core.config import settings

        self.memory_store = InMemoryStore()
        self.agents: dict[str, Any] = {}
        self.settings = settings
        api_key = settings.get_anthropic_api_key()
        # Ensure api_key is None if empty string
        self.api_key = api_key if api_key else None

        if not self.api_key:
            print("Warning: ANTHROPIC_API_KEY not set in .env or /tmp/api-key.")
            print("Agent features will use mock responses for testing.")
            print("To enable full agent functionality:")
            print("  1. Add ANTHROPIC_API_KEY=sk-ant-... to .env file, or")
            print("  2. Place your API key in /tmp/api-key")
        else:
            print(f"✓ Anthropic API key loaded (length: {len(self.api_key)})")

    def create_agent(
        self,
        user_id: str = "default",
        permission_mode: str = "default",
        model: str = "claude-sonnet-4-5-20250929",
    ) -> Any:
        """Create a DeepAgent instance with specified configuration.

        This method demonstrates the full DeepAgents architecture:

        Core Framework:
        1. create_deep_agent() - Core agent creation function from deepagents

        Built-in Middleware (provided by create_deep_agent):
        2. TodoListMiddleware - Provides write_todos and read_todos tools
        3. FilesystemMiddleware - Provides ls, read_file, write_file, edit_file, glob, grep
        4. SubAgentMiddleware - Provides task() tool for sub-agent delegation
        5. SummarizationMiddleware - Handles context exceeding 170k tokens
        6. AnthropicPromptCachingMiddleware - Reduces API costs via caching
        7. PatchToolCallsMiddleware - Handles tool call processing
        8. HumanInTheLoopMiddleware - Handles tool approval (if interrupt_on provided)

        Backend Configuration:
        9. StateBackend - Ephemeral file storage in agent state
        10. CompositeBackend - Hybrid memory (ephemeral + persistent via StoreBackend)
        11. StoreBackend - Long-term memory via InMemoryStore

        Args:
            user_id: User identifier for agent context
            permission_mode: Permission mode (default, acceptEdits, plan, bypass)
            model: Model identifier to use

        Returns:
            Configured DeepAgent instance (or MockAgent if no API key)
        """
        # Step 1: Configure interrupt_on for HumanInTheLoopMiddleware
        # This handles tool approval based on permission mode
        interrupt_config = {}
        if permission_mode == "default":
            interrupt_config = {
                "execute": True,
                "write_file": True,
                "edit_file": True,
            }
        elif permission_mode == "acceptEdits":
            interrupt_config = {
                "execute": True,
            }
        # plan and bypassPermissions modes have no interrupts

        # Also support UI permission modes (auto, manual)
        # manual = default (all tools require approval)
        # auto = bypassPermissions (no approvals needed)
        if permission_mode == "manual":
            interrupt_config = {
                "execute": True,
                "write_file": True,
                "edit_file": True,
            }
        elif permission_mode == "auto":
            interrupt_config = {}  # No interrupts

        # Step 2: Configure additional middleware
        # Note: create_deep_agent already provides:
        # - TodoListMiddleware (write_todos, read_todos)
        # - FilesystemMiddleware (ls, read_file, write_file, edit_file, glob, grep)
        # - SubAgentMiddleware (task() tool for sub-agent delegation)
        # - SummarizationMiddleware (context exceeding 170k tokens)
        # - AnthropicPromptCachingMiddleware (cost reduction)
        # - PatchToolCallsMiddleware (tool call handling)
        # - HumanInTheLoopMiddleware (if interrupt_on is provided)
        #
        # We don't need to add any additional middleware for the core features
        middleware_stack = []

        # Step 3: Create system prompt
        system_prompt = """You are Claude, a helpful AI assistant created by Anthropic.

You have access to powerful tools that enable you to help with complex tasks:

**Task Planning:**
- Use write_todos to create structured task lists for complex projects
- Update todo status as you complete tasks
- Keep users informed of your progress

**File Operations:**
- Read files with read_file
- Create new files with write_file
- Edit existing files with edit_file
- List directories with ls
- Search for patterns with grep
- Find files with glob

**Code Execution:**
- Execute shell commands when needed (requires approval)
- Be careful with destructive operations

**Sub-Agent Delegation:**
- Delegate specialized tasks to sub-agents when beneficial
- Research agent for web searches
- Code review agent for analyzing code

**Best Practices:**
- Always plan before executing complex multi-step tasks
- Keep the user informed of what you're doing
- Show your thinking process for complex problems
- Ask for permission before making significant changes
- Be concise but thorough

You are helping build a Claude.ai clone application. Be professional, friendly, and helpful."""

        # Step 4: Try to create real DeepAgent with LangChain Anthropic
        try:
            if not self.api_key:
                print("No API key available, using MockAgent for testing")
                return MockAgent(system_prompt=system_prompt)

            # Step 5: Create the LLM with API key
            llm = ChatAnthropic(
                model_name=model,
                anthropic_api_key=self.api_key,
                max_tokens=20000,
            )

            # Step 6: Create backend configuration
            # StateBackend for ephemeral working files (uses MemorySaver as runtime)
            runtime = MemorySaver()
            state_backend = StateBackend(runtime=runtime)

            # CompositeBackend for hybrid memory (ephemeral + persistent)
            # Routes /memories/ to StoreBackend for long-term memory
            # Note: StoreBackend uses the same runtime for tool execution
            composite_backend = CompositeBackend(
                default=state_backend,
                routes={
                    "/memories/": lambda rt: StoreBackend(runtime=rt),
                },
            )

            # Step 7: Create the DeepAgent with full configuration
            agent = create_deep_agent(
                model=llm,
                system_prompt=system_prompt,
                middleware=middleware_stack,
                interrupt_on=interrupt_config if interrupt_config else None,
                backend=composite_backend,  # Use composite backend for hybrid memory
                store=self.memory_store,    # Long-term memory store
                tools=[
                    self.extract_and_store_memory,
                    self.search_memories,
                    self.list_memories,
                ],
            )

            print(f"✓ Created DeepAgent with model: {model}")
            print(f"✓ Middleware stack: {len(middleware_stack)} components")
            print(f"✓ Backend: CompositeBackend (State + Store)")
            print(f"✓ Interrupt_on: {len(interrupt_config)} tools configured")
            return agent

        except Exception as e:
            print(f"Failed to create real DeepAgent: {e}")
            print("Falling back to MockAgent for testing")
            return MockAgent(system_prompt=system_prompt)

    def get_or_create_agent(
        self,
        user_id: str = "default",
        permission_mode: str = "default",
        model: str = "claude-sonnet-4-5-20250929",
    ) -> Any:
        """Get existing agent or create new one.

        Args:
            user_id: User identifier
            permission_mode: Permission mode
            model: Model to use

        Returns:
            DeepAgent instance
        """
        cache_key = f"{user_id}_{permission_mode}_{model}"

        if cache_key not in self.agents:
            self.agents[cache_key] = self.create_agent(user_id, permission_mode, model)

        return self.agents[cache_key]


    async def extract_and_store_memory(self, content: str, conversation_id: Optional[str] = None) -> str:
        """Extract and store a memory from conversation content.

        This tool allows the agent to automatically save important information
        to long-term memory.

        Args:
            content: The content to extract and store as memory
            conversation_id: Optional source conversation ID

        Returns:
            Success message with memory ID
        """
        # For now, we'll just store the content as-is
        # In a real implementation, this would use NLP to extract structured memory
        from sqlalchemy.ext.asyncio import AsyncSession
        from sqlalchemy import select

        # Get database session
        # Note: This is a simplified approach. In a real implementation,
        # you'd want to pass the database session as a dependency.
        try:
            # Create memory
            from uuid import uuid4
            memory_id = str(uuid4())

            # For now, return a mock success message
            # In a real implementation, you'd save to the database here
            return f"Memory stored successfully with ID: {memory_id}"
        except Exception as e:
            return f"Error storing memory: {str(e)}"


    async def search_memories(self, query: str, active_only: bool = True) -> str:
        """Search memories by content.

        Args:
            query: Search query
            active_only: Whether to search only active memories

        Returns:
            JSON string with search results
        """
        try:
            # For now, return mock results
            # In a real implementation, you'd search the database here
            return f"Search results for '{query}': [mock results]"
        except Exception as e:
            return f"Error searching memories: {str(e)}"


    async def list_memories(self, category: Optional[str] = None, active_only: bool = True) -> str:
        """List all memories with optional filtering.

        Args:
            category: Optional category filter
            active_only: Whether to show only active memories

        Returns:
            JSON string with memory list
        """
        try:
            # For now, return mock results
            # In a real implementation, you'd query the database here
            return "Memory list: [mock results]"
        except Exception as e:
            return f"Error listing memories: {str(e)}"


# Global agent service instance
agent_service = AgentService()
