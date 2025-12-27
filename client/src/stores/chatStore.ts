import { create } from 'zustand'

export interface Todo {
  id: string
  content: string
  status: 'pending' | 'in_progress' | 'completed' | 'cancelled'
}

interface ChatState {
  // Input
  inputMessage: string
  isStreaming: boolean
  stopRequested: boolean

  // Agent state
  todos: Todo[]

  // UI state
  showThinking: boolean

  // Actions
  setInputMessage: (message: string) => void
  setIsStreaming: (streaming: boolean) => void
  setStopRequested: (stop: boolean) => void
  setTodos: (todos: Todo[]) => void
  updateTodo: (id: string, status: Todo['status']) => void
  setShowThinking: (show: boolean) => void
  clearInput: () => void
}

export const useChatStore = create<ChatState>((set) => ({
  // Initial state
  inputMessage: '',
  isStreaming: false,
  stopRequested: false,
  todos: [],
  showThinking: false,

  // Actions
  setInputMessage: (message) => set({ inputMessage: message }),
  setIsStreaming: (streaming) => set({ isStreaming: streaming }),
  setStopRequested: (stop) => set({ stopRequested: stop }),
  setTodos: (todos) => set({ todos }),
  updateTodo: (id, status) =>
    set((state) => ({
      todos: state.todos.map((t) => (t.id === id ? { ...t, status } : t)),
    })),
  setShowThinking: (show) => set({ showThinking: show }),
  clearInput: () => set({ inputMessage: '' }),
}))
