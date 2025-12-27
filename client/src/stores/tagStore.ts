import { create } from 'zustand'
import { api } from '../services/api'
import type { Tag } from './conversationStore'

interface TagState {
  tags: Tag[]
  isLoading: boolean
  error: string | null

  // Actions
  loadTags: () => Promise<void>
  createTag: (name: string, color?: string) => Promise<Tag>
  updateTag: (tagId: string, data: { name?: string; color?: string }) => Promise<Tag>
  deleteTag: (tagId: string) => Promise<void>
  updateConversationTags: (conversationId: string, tagIds: string[]) => Promise<void>
  filterConversationsByTags: (tagIds: string[]) => Promise<void>

  // UI state
  selectedTags: string[]
  setSelectedTags: (tagIds: string[]) => void
  clearSelectedTags: () => void
}

export const useTagStore = create<TagState>((set, get) => ({
  tags: [],
  isLoading: false,
  error: null,
  selectedTags: [],

  loadTags: async () => {
    set({ isLoading: true, error: null })
    try {
      const tags = await api.listTags()
      set({ tags, isLoading: false })
    } catch (error) {
      console.error('Failed to load tags:', error)
      set({ error: String(error), isLoading: false })
    }
  },

  createTag: async (name: string, color?: string) => {
    set({ isLoading: true, error: null })
    try {
      const tag = await api.createTag({ name, color })
      set((state) => ({ tags: [...state.tags, tag], isLoading: false }))
      return tag
    } catch (error) {
      console.error('Failed to create tag:', error)
      set({ error: String(error), isLoading: false })
      throw error
    }
  },

  updateTag: async (tagId: string, data: { name?: string; color?: string }) => {
    set({ isLoading: true, error: null })
    try {
      const updatedTag = await api.updateTag(tagId, data)
      set((state) => ({
        tags: state.tags.map((t) => (t.id === tagId ? updatedTag : t)),
        isLoading: false,
      }))
      return updatedTag
    } catch (error) {
      console.error('Failed to update tag:', error)
      set({ error: String(error), isLoading: false })
      throw error
    }
  },

  deleteTag: async (tagId: string) => {
    set({ isLoading: true, error: null })
    try {
      await api.deleteTag(tagId)
      set((state) => ({
        tags: state.tags.filter((t) => t.id !== tagId),
        selectedTags: state.selectedTags.filter((id) => id !== tagId),
        isLoading: false,
      }))
    } catch (error) {
      console.error('Failed to delete tag:', error)
      set({ error: String(error), isLoading: false })
      throw error
    }
  },

  updateConversationTags: async (conversationId: string, tagIds: string[]) => {
    set({ isLoading: true, error: null })
    try {
      const result = await api.updateConversationTags(conversationId, tagIds)

      // Update the conversation in the conversation store
      const { useConversationStore } = await import('./conversationStore')
      useConversationStore.getState().updateConversation(conversationId, {
        tags: result.tags
      })

      set({ isLoading: false })
    } catch (error) {
      console.error('Failed to update conversation tags:', error)
      set({ error: String(error), isLoading: false })
      throw error
    }
  },

  filterConversationsByTags: async (tagIds: string[]) => {
    set({ isLoading: true, error: null })
    try {
      await api.filterConversationsByTags(tagIds)
      set({ isLoading: false })
    } catch (error) {
      console.error('Failed to filter conversations by tags:', error)
      set({ error: String(error), isLoading: false })
      throw error
    }
  },

  setSelectedTags: (tagIds: string[]) => {
    set({ selectedTags: tagIds })
  },

  clearSelectedTags: () => {
    set({ selectedTags: [] })
  },
}))
