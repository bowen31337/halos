"""DeepAgents service for AI agent interactions."""

import os
from typing import Optional, Any
from uuid import uuid4

from deepagents import create_deep_agent
from deepagents.backends import StateBackend, StoreBackend
from langgraph.store.memory import InMemoryStore


class AgentService:
    """Service for managing DeepAgents instances."""

    def __init__(self):
        """Initialize the agent service."""
        from src.core.config import settings

        self.memory_store = InMemoryStore()
        self.agents: dict[str, Any] = {}
        self.settings = settings
        self.api_key = settings.get_anthropic_api_key()

        if not self.api_key:
            print("Warning: ANTHROPIC_API_KEY not set in .env or /tmp/api-key.")
            print("Agent features will be limited to mock responses.")
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

        Args:
            user_id: User identifier for agent context
            permission_mode: Permission mode (default, acceptEdits, plan, bypass)
            model: Model identifier to use

        Returns:
            Configured DeepAgent instance
        """
        # Configure interrupt based on permission mode
        interrupt_config = {}
        if permission_mode == "default":
            interrupt_config = {
                "execute": {"allowed_decisions": ["approve", "edit", "reject"]},
                "write_file": {"allowed_decisions": ["approve", "edit", "reject"]},
                "edit_file": {"allowed_decisions": ["approve", "edit", "reject"]},
            }
        elif permission_mode == "acceptEdits":
            interrupt_config = {
                "execute": {"allowed_decisions": ["approve", "edit", "reject"]},
            }
        # plan and bypassPermissions modes have no interrupts

        # Create system prompt
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

        # Create the agent with StateBackend for ephemeral files
        # Note: For production, you'd use CompositeBackend with StoreBackend for long-term memory
        try:
            agent = create_deep_agent(
                model=f"anthropic:{model}",
                system_prompt=system_prompt,
                backend=StateBackend(),  # Ephemeral file storage
                interrupt_on=interrupt_config if interrupt_config else None,
            )
            return agent
        except Exception as e:
            print(f"Error creating agent: {e}")
            # Return a mock agent if deepagents fails
            return None

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


# Global agent service instance
agent_service = AgentService()
