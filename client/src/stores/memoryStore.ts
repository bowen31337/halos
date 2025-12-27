import { create } from 'zustand'

export interface Memory {
  id: string
  content: string
  category: 'fact' | 'preference' | 'context'
  source_conversation_id: string | null
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface MemoryState {
  // State
  memories: Memory[]
  isLoading: boolean
  error: string | null
  memoryEnabled: boolean

  // Actions
  fetchMemories: () => Promise<void>
  createMemory: (content: string, category?: string) => Promise<Memory>
  updateMemory: (id: string, updates: Partial<Memory>) => Promise<Memory>
  deleteMemory: (id: string) => Promise<void>
  searchMemories: (query: string) => Promise<Memory[]>
  toggleMemoryEnabled: (enabled: boolean) => void
  clearError: () => void
}

export const useMemoryStore = create<MemoryState>((set, get) => ({
  // Initial state
  memories: [],
  isLoading: false,
  error: null,
  memoryEnabled: true,

  // Actions
  fetchMemories: async () => {
    set({ isLoading: true, error: null })
    try {
      const response = await fetch('/api/memory')
      if (!response.ok) throw new Error('Failed to fetch memories')
      const memories = await response.json()
      set({ memories, isLoading: false })
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Failed to fetch memories',
        isLoading: false
      })
    }
  },

  createMemory: async (content: string, category: string = 'fact') => {
    set({ isLoading: true, error: null })
    try {
      const response = await fetch('/api/memory', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content, category })
      })
      if (!response.ok) throw new Error('Failed to create memory')
      const memory = await response.json()
      set(state => ({
        memories: [memory, ...state.memories],
        isLoading: false
      }))
      return memory
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to create memory'
      set({ error: message, isLoading: false })
      throw error
    }
  },

  updateMemory: async (id: string, updates: Partial<Memory>) => {
    set({ isLoading: true, error: null })
    try {
      const response = await fetch(`/api/memory/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updates)
      })
      if (!response.ok) throw new Error('Failed to update memory')
      const memory = await response.json()
      set(state => ({
        memories: state.memories.map(m => m.id === id ? memory : m),
        isLoading: false
      }))
      return memory
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to update memory'
      set({ error: message, isLoading: false })
      throw error
    }
  },

  deleteMemory: async (id: string) => {
    set({ isLoading: true, error: null })
    try {
      const response = await fetch(`/api/memory/${id}`, {
        method: 'DELETE'
      })
      if (!response.ok) throw new Error('Failed to delete memory')
      set(state => ({
        memories: state.memories.filter(m => m.id !== id),
        isLoading: false
      }))
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to delete memory'
      set({ error: message, isLoading: false })
      throw error
    }
  },

  searchMemories: async (query: string) => {
    set({ isLoading: true, error: null })
    try {
      const response = await fetch(`/api/memory/search?q=${encodeURIComponent(query)}`)
      if (!response.ok) throw new Error('Failed to search memories')
      const memories = await response.json()
      set({ isLoading: false })
      return memories
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to search memories'
      set({ error: message, isLoading: false })
      throw error
    }
  },

  toggleMemoryEnabled: (enabled: boolean) => {
    set({ memoryEnabled: enabled })
  },

  clearError: () => {
    set({ error: null })
  }
}))
