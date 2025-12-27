import { create } from 'zustand'

export interface Message {
  id: string
  conversationId: string
  role: 'user' | 'assistant' | 'system' | 'tool'
  content: string
  createdAt: string
  toolName?: string
  toolInput?: Record<string, unknown>
  toolOutput?: string
  isStreaming?: boolean
}

export interface Conversation {
  id: string
  title: string
  model: string
  projectId?: string
  isArchived: boolean
  isPinned: boolean
  messageCount: number
  createdAt: string
  updatedAt: string
}

export interface Todo {
  id: string
  content: string
  status: 'pending' | 'in_progress' | 'completed' | 'cancelled'
}

interface ConversationState {
  // Current conversation
  currentConversationId: string | null
  conversations: Conversation[]
  messages: Message[]
  todos: Todo[]

  // UI state
  isLoading: boolean
  isStreaming: boolean
  error: string | null

  // Actions
  setCurrentConversation: (id: string | null) => void
  setConversations: (conversations: Conversation[]) => void
  addConversation: (conversation: Conversation) => void
  updateConversation: (id: string, updates: Partial<Conversation>) => void
  deleteConversation: (id: string) => void

  setMessages: (messages: Message[]) => void
  addMessage: (message: Message) => void
  updateMessage: (id: string, updates: Partial<Message>) => void
  appendToLastMessage: (content: string) => void

  setTodos: (todos: Todo[]) => void

  setLoading: (loading: boolean) => void
  setStreaming: (streaming: boolean) => void
  setError: (error: string | null) => void

  reset: () => void
}

const initialState = {
  currentConversationId: null,
  conversations: [],
  messages: [],
  todos: [],
  isLoading: false,
  isStreaming: false,
  error: null,
}

export const useConversationStore = create<ConversationState>((set) => ({
  ...initialState,

  setCurrentConversation: (id) => set({ currentConversationId: id }),

  setConversations: (conversations) => set({ conversations }),

  addConversation: (conversation) =>
    set((state) => ({
      conversations: [conversation, ...state.conversations]
    })),

  updateConversation: (id, updates) =>
    set((state) => ({
      conversations: state.conversations.map((c) =>
        c.id === id ? { ...c, ...updates } : c
      ),
    })),

  deleteConversation: (id) =>
    set((state) => ({
      conversations: state.conversations.filter((c) => c.id !== id),
      currentConversationId:
        state.currentConversationId === id ? null : state.currentConversationId,
    })),

  setMessages: (messages) => set({ messages }),

  addMessage: (message) =>
    set((state) => ({ messages: [...state.messages, message] })),

  updateMessage: (id, updates) =>
    set((state) => ({
      messages: state.messages.map((m) =>
        m.id === id ? { ...m, ...updates } : m
      ),
    })),

  appendToLastMessage: (content) =>
    set((state) => {
      const messages = [...state.messages]
      const lastMessage = messages[messages.length - 1]
      if (lastMessage && lastMessage.role === 'assistant') {
        messages[messages.length - 1] = {
          ...lastMessage,
          content: lastMessage.content + content,
        }
      }
      return { messages }
    }),

  setTodos: (todos) => set({ todos }),

  setLoading: (isLoading) => set({ isLoading }),
  setStreaming: (isStreaming) => set({ isStreaming }),
  setError: (error) => set({ error }),

  reset: () => set(initialState),
}))
