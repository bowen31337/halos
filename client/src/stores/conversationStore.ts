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
  inputMessage: string

  // Actions
  setCurrentConversation: (id: string | null) => void
  setConversations: (conversations: Conversation[]) => void
  addConversation: (conversation: Conversation) => void
  updateConversation: (id: string, updates: Partial<Conversation>) => void
  deleteConversation: (id: string) => void

  // API Actions
  loadConversations: () => Promise<void>
  loadMessages: (conversationId: string) => Promise<void>
  createConversation: (title?: string) => Promise<Conversation>
  updateConversationTitle: (id: string, title: string) => Promise<void>
  removeConversation: (id: string) => Promise<void>
  archiveConversation: (id: string) => Promise<void>
  unarchiveConversation: (id: string) => Promise<void>

  setMessages: (messages: Message[]) => void
  addMessage: (message: Message) => void
  updateMessage: (id: string, updates: Partial<Message>) => void
  appendToLastMessage: (content: string) => void
  regenerateLastResponse: (messageId: string) => Promise<void>
  editAndResend: (messageId: string, newContent: string) => Promise<void>

  setTodos: (todos: Todo[]) => void

  setLoading: (loading: boolean) => void
  setStreaming: (streaming: boolean) => void
  setError: (error: string | null) => void
  setInputMessage: (message: string) => void

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
  inputMessage: '',
}

// Helper to transform API response (snake_case) to frontend format (camelCase)
const transformConversation = (apiConv: any): Conversation => ({
  id: apiConv.id,
  title: apiConv.title,
  model: apiConv.model,
  projectId: apiConv.project_id,
  isArchived: apiConv.is_archived,
  isPinned: apiConv.is_pinned,
  messageCount: apiConv.message_count,
  createdAt: apiConv.created_at,
  updatedAt: apiConv.updated_at,
})

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

  // API Actions
  loadConversations: async () => {
    try {
      const response = await fetch('/api/conversations')
      if (response.ok) {
        const data = await response.json()
        const transformed = data.map(transformConversation)
        set({ conversations: transformed })
      }
    } catch (error) {
      console.error('Failed to load conversations:', error)
    }
  },

  loadMessages: async (conversationId: string) => {
    try {
      const response = await fetch(`/api/messages/conversations/${conversationId}/messages`)
      if (response.ok) {
        const data = await response.json()
        set({ messages: data })
      }
    } catch (error) {
      console.error('Failed to load messages:', error)
    }
  },

  createConversation: async (title = 'New Conversation') => {
    const response = await fetch('/api/conversations', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title }),
    })
    if (!response.ok) throw new Error('Failed to create conversation')

    const apiConv = await response.json()
    const conv = transformConversation(apiConv)
    set((state) => ({ conversations: [conv, ...state.conversations] }))
    return conv
  },

  updateConversationTitle: async (id: string, title: string) => {
    const response = await fetch(`/api/conversations/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title }),
    })
    if (response.ok) {
      set((state) => ({
        conversations: state.conversations.map((c) =>
          c.id === id ? { ...c, title } : c
        ),
      }))
    }
  },

  removeConversation: async (id: string) => {
    const response = await fetch(`/api/conversations/${id}`, {
      method: 'DELETE',
    })
    if (response.ok) {
      set((state) => ({
        conversations: state.conversations.filter((c) => c.id !== id),
        currentConversationId:
          state.currentConversationId === id ? null : state.currentConversationId,
      }))
    }
  },

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
  setInputMessage: (message) => set({ inputMessage: message }),

  regenerateLastResponse: async (messageId: string) => {
    const state = useConversationStore.getState()
    const messageIndex = state.messages.findIndex(m => m.id === messageId)

    if (messageIndex === -1) return

    // Remove all messages after this one (including this one)
    const messagesToKeep = state.messages.slice(0, messageIndex)
    set({ messages: messagesToKeep })

    // Get the last user message to resend
    const lastUserMessage = [...messagesToKeep].reverse().find(m => m.role === 'user')

    if (lastUserMessage) {
      // Trigger resend by calling the stream endpoint
      const convId = state.currentConversationId || 'default'
      const sendMessage = async () => {
        set({ isLoading: true, isStreaming: true })

        // Create assistant message placeholder
        const assistantMessage = {
          id: Date.now().toString(),
          conversationId: convId,
          role: 'assistant' as const,
          content: '',
          createdAt: new Date().toISOString(),
          isStreaming: true,
        }
        set((state) => ({ messages: [...state.messages, assistantMessage] }))

        try {
          const response = await fetch('/api/agent/stream', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              message: lastUserMessage.content,
              conversationId: convId,
              thread_id: convId
            }),
          })

          if (!response.ok) throw new Error('Failed to regenerate')

          const reader = response.body?.getReader()
          if (!reader) throw new Error('No response body')
          const decoder = new TextDecoder()
          let buffer = ''

          while (true) {
            const { done, value } = await reader.read()
            if (done) break

            buffer += decoder.decode(value, { stream: true })
            const lines = buffer.split('\n')
            buffer = lines.pop() || ''

            for (const line of lines) {
              if (line.startsWith('data: ')) {
                const dataStr = line.slice(6)
                if (!dataStr) continue

                try {
                  const eventData = JSON.parse(dataStr)
                  if (eventData.content) {
                    set((state) => {
                      const messages = [...state.messages]
                      const lastMsg = messages[messages.length - 1]
                      if (lastMsg && lastMsg.role === 'assistant') {
                        messages[messages.length - 1] = {
                          ...lastMsg,
                          content: lastMsg.content + eventData.content,
                        }
                      }
                      return { messages }
                    })
                  }
                } catch (e) {
                  // Ignore parse errors
                }
              }
            }
          }

          // Mark as complete
          set((state) => {
            const messages = [...state.messages]
            const lastMsg = messages[messages.length - 1]
            if (lastMsg && lastMsg.role === 'assistant') {
              messages[messages.length - 1] = { ...lastMsg, isStreaming: false }
            }
            return { messages, isLoading: false, isStreaming: false }
          })
        } catch (error) {
          console.error('Regenerate failed:', error)
          set({ isLoading: false, isStreaming: false })
        }
      }

      sendMessage()
    }
  },

  editAndResend: async (messageId: string, newContent: string) => {
    const state = useConversationStore.getState()
    const messageIndex = state.messages.findIndex(m => m.id === messageId)

    if (messageIndex === -1) return

    // Update the message content
    set((state) => ({
      messages: state.messages.map((m, i) =>
        i === messageIndex ? { ...m, content: newContent } : m
      ),
    }))

    // Remove all messages after this one
    const messagesToKeep = state.messages.slice(0, messageIndex + 1)
    set({ messages: messagesToKeep })

    // Send the edited message
    const convId = state.currentConversationId || 'default'
    set({ isLoading: true, isStreaming: true })

    const assistantMessage = {
      id: Date.now().toString(),
      conversationId: convId,
      role: 'assistant' as const,
      content: '',
      createdAt: new Date().toISOString(),
      isStreaming: true,
    }
    set((state) => ({ messages: [...state.messages, assistantMessage] }))

    try {
      const response = await fetch('/api/agent/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: newContent,
          conversationId: convId,
          thread_id: convId
        }),
      })

      if (!response.ok) throw new Error('Failed to send')

      const reader = response.body?.getReader()
      if (!reader) throw new Error('No response body')
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const dataStr = line.slice(6)
            if (!dataStr) continue

            try {
              const eventData = JSON.parse(dataStr)
              if (eventData.content) {
                set((state) => {
                  const messages = [...state.messages]
                  const lastMsg = messages[messages.length - 1]
                  if (lastMsg && lastMsg.role === 'assistant') {
                    messages[messages.length - 1] = {
                      ...lastMsg,
                      content: lastMsg.content + eventData.content,
                    }
                  }
                  return { messages }
                })
              }
            } catch (e) {
              // Ignore parse errors
            }
          }
        }
      }

      set((state) => {
        const messages = [...state.messages]
        const lastMsg = messages[messages.length - 1]
        if (lastMsg && lastMsg.role === 'assistant') {
          messages[messages.length - 1] = { ...lastMsg, isStreaming: false }
        }
        return { messages, isLoading: false, isStreaming: false }
      })
    } catch (error) {
      console.error('Send failed:', error)
      set({ isLoading: false, isStreaming: false })
    }
  },

  archiveConversation: async (id: string) => {
    const response = await fetch(`/api/conversations/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ is_archived: true }),
    })
    if (response.ok) {
      set((state) => ({
        conversations: state.conversations.map((c) =>
          c.id === id ? { ...c, isArchived: true } : c
        ),
      }))
    }
  },

  unarchiveConversation: async (id: string) => {
    const response = await fetch(`/api/conversations/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ is_archived: false }),
    })
    if (response.ok) {
      set((state) => ({
        conversations: state.conversations.map((c) =>
          c.id === id ? { ...c, isArchived: false } : c
        ),
      }))
    }
  },

  reset: () => set(initialState),
}))
