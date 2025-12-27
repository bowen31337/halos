"""Test todo system UI components and structure.

This test verifies that all required UI components for the todo system exist
and are properly configured.
"""

import pytest
import os


def test_todo_panel_component_exists():
    """Test that the TodoPanel component exists and has required structure."""
    component_path = "/media/DATA/projects/autonomous-coding-clone-cc/talos/client/src/components/TodoPanel.tsx"
    assert os.path.exists(component_path), "TodoPanel component should exist"

    with open(component_path, 'r') as f:
        content = f.read()

    # Verify it imports the chat store
    assert "useChatStore" in content
    assert "todos" in content
    assert "setTodos" in content

    # Verify it has status badges for all states
    assert "pending" in content
    assert "in_progress" in content
    assert "completed" in content
    assert "cancelled" in content

    # Verify it has progress display (completed/total)
    assert "filter(t => t.status === 'completed')" in content or "completed" in content

    # Verify it has toggle functionality
    assert "toggleTodo" in content or "updateTodo" in content


def test_todo_list_component_exists():
    """Test that the TodoList component exists."""
    component_path = "/media/DATA/projects/autonomous-coding-clone-cc/talos/client/src/components/TodoList.tsx"
    assert os.path.exists(component_path), "TodoList component should exist"

    with open(component_path, 'r') as f:
        content = f.read()

    # Verify it has todo display logic
    assert "todos" in content
    assert "status" in content
    assert "toggleTodo" in content


def test_chat_input_handles_todos_events():
    """Test that ChatInput component handles todos events from SSE stream."""
    component_path = "/media/DATA/projects/autonomous-coding-clone-cc/talos/client/src/components/ChatInput.tsx"
    assert os.path.exists(component_path), "ChatInput component should exist"

    with open(component_path, 'r') as f:
        content = f.read()

    # Verify it handles todos events
    assert "case 'todos':" in content
    assert "setTodos" in content
    assert "eventData.todos" in content

    # Verify it auto-opens todo panel when first todos are received
    assert "previousTodos.length === 0" in content
    assert "setPanelType('todos')" in content
    assert "setPanelOpen(true)" in content


def test_header_has_todo_button():
    """Test that the Header component has a todo button."""
    component_path = "/media/DATA/projects/autonomous-coding-clone-cc/talos/client/src/components/Header.tsx"
    assert os.path.exists(component_path), "Header component should exist"

    with open(component_path, 'r') as f:
        content = f.read()

    # Verify todo button exists
    assert "panelType === 'todos'" in content
    assert "setPanelType('todos')" in content
    assert "setPanelOpen" in content


def test_chat_page_renders_todo_panel():
    """Test that ChatPage renders TodoPanel based on panelType."""
    component_path = "/media/DATA/projects/autonomous-coding-clone-cc/talos/client/src/pages/ChatPage.tsx"
    assert os.path.exists(component_path), "ChatPage should exist"

    with open(component_path, 'r') as f:
        content = f.read()

    # Verify TodoPanel is imported and rendered conditionally
    assert "TodoPanel" in content
    assert "panelType === 'todos'" in content


def test_ui_store_has_todo_panel_type():
    """Test that UI store supports todo panel type."""
    store_path = "/media/DATA/projects/autonomous-coding-clone-cc/talos/client/src/stores/uiStore.ts"
    assert os.path.exists(store_path), "UI store should exist"

    with open(store_path, 'r') as f:
        content = f.read()

    # Verify todos is a valid panel type
    assert "'todos'" in content
    assert "panelType:" in content
    assert "setPanelType" in content


def test_chat_store_has_todo_interface():
    """Test that chat store has todo interface and actions."""
    store_path = "/media/DATA/projects/autonomous-coding-clone-cc/talos/client/src/stores/chatStore.ts"
    assert os.path.exists(store_path), "Chat store should exist"

    with open(store_path, 'r') as f:
        content = f.read()

    # Verify Todo interface exists
    assert "interface Todo" in content
    assert "id: string" in content
    assert "content: string" in content
    assert "status:" in content

    # Verify store actions
    assert "setTodos:" in content
    assert "updateTodo:" in content


def test_api_service_has_get_todos():
    """Test that API service has getTodos method."""
    api_path = "/media/DATA/projects/autonomous-coding-clone-cc/talos/client/src/services/api.ts"
    assert os.path.exists(api_path), "API service should exist"

    with open(api_path, 'r') as f:
        content = f.read()

    # Verify getTodos method exists
    assert "async getTodos" in content
    assert "/agent/todos/" in content


def test_sse_event_type_includes_todos():
    """Test that SSE event type includes todos."""
    api_path = "/media/DATA/projects/autonomous-coding-clone-cc/talos/client/src/services/api.ts"

    with open(api_path, 'r') as f:
        content = f.read()

    # Verify todos is in SSE event type
    assert "'todos'" in content
    assert "SSEEvent" in content


def test_complete_todo_workflow_integration():
    """Test that all components are connected for the complete todo workflow.

    This verifies the integration points:
    1. ChatInput receives 'todos' events and calls setTodos
    2. setTodos updates the chat store
    3. TodoPanel reads from chat store and displays todos
    4. Header has button to toggle todo panel
    """
    # 1. Verify ChatInput handles todos events
    chat_input_path = "/media/DATA/projects/autonomous-coding-clone-cc/talos/client/src/components/ChatInput.tsx"
    with open(chat_input_path, 'r') as f:
        chat_input = f.read()

    assert "case 'todos':" in chat_input
    assert "useChatStore" in chat_input
    assert "setTodos(eventData.todos)" in chat_input

    # 2. Verify chat store has setTodos
    chat_store_path = "/media/DATA/projects/autonomous-coding-clone-cc/talos/client/src/stores/chatStore.ts"
    with open(chat_store_path, 'r') as f:
        chat_store = f.read()

    assert "setTodos: (todos) => set({ todos })" in chat_store

    # 3. Verify TodoPanel reads todos from store
    todo_panel_path = "/media/DATA/projects/autonomous-coding-clone-cc/talos/client/src/components/TodoPanel.tsx"
    with open(todo_panel_path, 'r') as f:
        todo_panel = f.read()

    assert "const { todos, setTodos, updateTodo } = useChatStore()" in todo_panel
    assert "todos.map" in todo_panel

    # 4. Verify Header can toggle todo panel
    header_path = "/media/DATA/projects/autonomous-coding-clone-cc/talos/client/src/components/Header.tsx"
    with open(header_path, 'r') as f:
        header = f.read()

    assert "setPanelType('todos')" in header
    assert "setPanelOpen(true)" in header

    # 5. Verify ChatPage renders TodoPanel conditionally
    chat_page_path = "/media/DATA/projects/autonomous-coding-clone-cc/talos/client/src/pages/ChatPage.tsx"
    with open(chat_page_path, 'r') as f:
        chat_page = f.read()

    assert "panelType === 'todos'" in chat_page
    assert "<TodoPanel />" in chat_page


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
