import { useEffect, useState } from 'react'
import { useChatStore, type Todo } from '../stores/chatStore'
import { useConversationStore } from '../stores/conversationStore'
import { api } from '../services/api'

export function TodoPanel() {
  const { todos, setTodos, updateTodo } = useChatStore()
  const { currentConversationId } = useConversationStore()
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Fetch todos when conversation changes
  useEffect(() => {
    if (!currentConversationId) {
      setTodos([])
      return
    }

    const fetchTodos = async () => {
      setIsLoading(true)
      setError(null)
      try {
        // Use conversationId as threadId
        const response = await api.getTodos(currentConversationId)
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
  }, [currentConversationId, setTodos])

  const toggleTodo = (id: string, currentStatus: Todo['status']) => {
    const newStatus: Todo['status'] = currentStatus === 'completed' ? 'pending' : 'completed'
    updateTodo(id, newStatus)
  }

  const getStatusBadge = (status: Todo['status']) => {
    const styles = {
      pending: 'bg-[var(--text-secondary)]/20 text-[var(--text-secondary)]',
      in_progress: 'bg-[var(--primary)]/20 text-[var(--primary)]',
      completed: 'bg-[var(--success)]/20 text-[var(--success)]',
      cancelled: 'bg-[var(--error)]/20 text-[var(--error)]',
    }
    const labels = {
      pending: 'Pending',
      in_progress: 'In Progress',
      completed: 'Completed',
      cancelled: 'Cancelled',
    }
    return (
      <span className={`text-[10px] px-2 py-0.5 rounded-full ${styles[status]}`}>
        {labels[status]}
      </span>
    )
  }

  // Calculate progress
  const totalTodos = todos.length
  const completedTodos = todos.filter(t => t.status === 'completed').length
  const inProgressTodos = todos.filter(t => t.status === 'in_progress').length
  const progressPercentage = totalTodos > 0 ? (completedTodos / totalTodos) * 100 : 0

  return (
    <div className="fixed right-0 top-14 bottom-0 w-80 bg-[var(--bg-primary)] border-l border-[var(--border)] shadow-xl z-20 flex flex-col lg:w-80 md:w-full">
      {/* Header */}
      <div className="px-4 py-3 border-b border-[var(--border)] flex items-center justify-between">
        <div className="flex items-center gap-2">
          <svg className="w-4 h-4 text-[var(--text-primary)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
          </svg>
          <span className="text-sm font-semibold text-[var(--text-primary)]">Task List</span>
          {totalTodos > 0 && (
            <span className="text-xs px-2 py-0.5 rounded-full bg-[var(--primary)] text-white">
              {completedTodos}/{totalTodos}
            </span>
          )}
        </div>
      </div>

      {/* Progress Bar */}
      {totalTodos > 0 && (
        <div className="px-4 py-2 bg-[var(--surface-secondary)] border-b border-[var(--border)]">
          <div className="flex items-center justify-between mb-1">
            <span className="text-[10px] text-[var(--text-secondary)]">Progress</span>
            <span className="text-[10px] font-medium text-[var(--text-primary)]">
              {Math.round(progressPercentage)}%
            </span>
          </div>
          <div className="w-full h-2 rounded-full bg-[var(--border)] overflow-hidden">
            <div
              className="h-full bg-[var(--success)] transition-all duration-300"
              style={{ width: `${progressPercentage}%` }}
            />
          </div>
          <div className="flex gap-2 mt-1 text-[9px] text-[var(--text-secondary)]">
            {completedTodos > 0 && <span>✓ {completedTodos} done</span>}
            {inProgressTodos > 0 && <span>⋯ {inProgressTodos} in progress</span>}
            {totalTodos - completedTodos - inProgressTodos > 0 && (
              <span>○ {totalTodos - completedTodos - inProgressTodos} pending</span>
            )}
          </div>
        </div>
      )}

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4">
        {isLoading && todos.length === 0 ? (
          <div className="text-sm text-[var(--text-secondary)] text-center py-8">
            <div className="loading-spinner primary mb-2 mx-auto"></div>
            Loading todos...
          </div>
        ) : error ? (
          <div className="text-sm text-[var(--error)] text-center py-4">{error}</div>
        ) : todos.length === 0 ? (
          <div className="text-sm text-[var(--text-secondary)] text-center py-8">
            <svg className="w-12 h-12 mx-auto mb-3 opacity-30" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
            No tasks yet.
            <div className="text-xs mt-2 opacity-70">
              Ask the agent to plan a complex task.
            </div>
          </div>
        ) : (
          <div className="space-y-3">
            {todos.map((todo) => (
              <div
                key={todo.id}
                className="group rounded-lg border border-[var(--border)] hover:border-[var(--primary)] transition-colors bg-[var(--surface-secondary)]"
              >
                <div className="flex items-start gap-3 p-3">
                  <button
                    onClick={() => toggleTodo(todo.id, todo.status)}
                    className={`mt-0.5 flex-shrink-0 w-5 h-5 rounded border flex items-center justify-center transition-colors ${
                      todo.status === 'completed'
                        ? 'bg-[var(--success)] border-[var(--success)] text-white'
                        : 'border-[var(--border)] hover:border-[var(--primary)]'
                    }`}
                    title={todo.status === 'completed' ? 'Mark as pending' : 'Mark as completed'}
                  >
                    {todo.status === 'completed' && (
                      <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                      </svg>
                    )}
                  </button>
                  <div className="flex-1 min-w-0">
                    <span
                      className={`text-sm block mb-1 ${
                        todo.status === 'completed'
                          ? 'text-[var(--text-secondary)] line-through'
                          : 'text-[var(--text-primary)]'
                      }`}
                    >
                      {todo.content}
                    </span>
                    <div className="flex items-center gap-2">
                      {getStatusBadge(todo.status)}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="px-4 py-3 border-t border-[var(--border)] text-xs text-[var(--text-secondary)]">
        <div className="flex items-center gap-2">
          <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          Todos are updated automatically during agent streaming
        </div>
      </div>
    </div>
  )
}
