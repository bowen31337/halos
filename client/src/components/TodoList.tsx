import { useEffect, useState } from 'react'
import { useChatStore, type Todo } from '../stores/chatStore'
import { api } from '../services/api'

interface TodoListProps {
  threadId?: string
  conversationId?: string
}

export function TodoList({ threadId, conversationId }: TodoListProps) {
  const { todos, setTodos, updateTodo } = useChatStore()
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [isOpen, setIsOpen] = useState(true)

  // Fetch todos when threadId changes
  useEffect(() => {
    if (!threadId) {
      setTodos([])
      return
    }

    const fetchTodos = async () => {
      setIsLoading(true)
      setError(null)
      try {
        const response = await api.getTodos(threadId)
        if (response.todos) {
          setTodos(response.todos)
        }
      } catch (err) {
        setError('Failed to load todos')
        console.error('Error fetching todos:', err)
      } finally {
        setIsLoading(false)
      }
    }

    fetchTodos()
    // Poll for updates every 2 seconds
    const interval = setInterval(fetchTodos, 2000)
    return () => clearInterval(interval)
  }, [threadId, setTodos])

  const toggleTodo = (id: string, currentStatus: Todo['status']) => {
    const newStatus: Todo['status'] = currentStatus === 'completed' ? 'pending' : 'completed'
    updateTodo(id, newStatus)
    // Optimistically update on backend if needed
    if (threadId) {
      // Note: The backend todos are read-only from agent state
      // This is just for UI feedback
    }
  }

  if (!threadId) {
    return null
  }

  return (
    <div className="border-t border-[var(--border)] bg-[var(--surface-secondary)]">
      {/* Header */}
      <div
        className="flex items-center justify-between px-4 py-3 cursor-pointer hover:bg-[var(--surface-elevated)] transition-colors"
        onClick={() => setIsOpen(!isOpen)}
      >
        <div className="flex items-center gap-2">
          <svg className="w-4 h-4 text-[var(--text-primary)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
          </svg>
          <span className="text-sm font-medium text-[var(--text-primary)]">Task List</span>
          {todos.length > 0 && (
            <span className="text-xs px-2 py-0.5 rounded-full bg-[var(--primary)] text-white">
              {todos.filter(t => t.status === 'completed').length}/{todos.length}
            </span>
          )}
        </div>
        <svg
          className={`w-4 h-4 text-[var(--text-secondary)] transition-transform ${isOpen ? 'rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </div>

      {/* Content */}
      {isOpen && (
        <div className="px-4 pb-3">
          {isLoading && todos.length === 0 ? (
            <div className="text-xs text-[var(--text-secondary)] py-2">Loading todos...</div>
          ) : error ? (
            <div className="text-xs text-[var(--error)] py-2">{error}</div>
          ) : todos.length === 0 ? (
            <div className="text-xs text-[var(--text-secondary)] py-2 italic">
              No tasks yet. Ask the agent to plan a complex task.
            </div>
          ) : (
            <ul className="space-y-2 mt-2">
              {todos.map((todo) => (
                <li
                  key={todo.id}
                  className="group flex items-start gap-2 p-2 rounded hover:bg-[var(--surface-elevated)] transition-colors"
                >
                  <button
                    onClick={() => toggleTodo(todo.id, todo.status)}
                    className={`mt-0.5 flex-shrink-0 w-4 h-4 rounded border flex items-center justify-center transition-colors ${
                      todo.status === 'completed'
                        ? 'bg-[var(--primary)] border-[var(--primary)] text-white'
                        : 'border-[var(--border)] hover:border-[var(--primary)]'
                    }`}
                    title={todo.status === 'completed' ? 'Mark as pending' : 'Mark as completed'}
                  >
                    {todo.status === 'completed' && (
                      <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                      </svg>
                    )}
                  </button>
                  <div className="flex-1 min-w-0">
                    <span
                      className={`text-sm block ${
                        todo.status === 'completed'
                          ? 'text-[var(--text-secondary)] line-through'
                          : 'text-[var(--text-primary)]'
                      }`}
                    >
                      {todo.content}
                    </span>
                    <span className="text-[10px] px-1.5 py-0.5 rounded-full inline-block mt-1">
                      {todo.status === 'pending' && (
                        <span className="text-[var(--text-secondary)]">Pending</span>
                      )}
                      {todo.status === 'in_progress' && (
                        <span className="text-[var(--primary)]">In Progress</span>
                      )}
                      {todo.status === 'completed' && (
                        <span className="text-[var(--success)]">Completed</span>
                      )}
                      {todo.status === 'cancelled' && (
                        <span className="text-[var(--error)]">Cancelled</span>
                      )}
                    </span>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  )
}
