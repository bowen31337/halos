import { create } from 'zustand'

export interface Template {
  id: string
  user_id: string
  title: string
  description: string | null
  category: string
  system_prompt: string | null
  initial_message: string
  model: string
  tags: Record<string, any> | null
  is_builtin: boolean
  is_active: boolean
  usage_count: number
  created_at: string
  updated_at: string
}

interface TemplateStore {
  templates: Template[]
  categories: Array<{ category: string; count: string }>
  selectedTemplate: Template | null
  isLoading: boolean
  error: string | null

  // Actions
  loadTemplates: () => Promise<void>
  loadCategories: () => Promise<void>
  selectTemplate: (template: Template | null) => void
  createTemplate: (data: Partial<Template>) => Promise<Template>
  updateTemplate: (id: string, data: Partial<Template>) => Promise<void>
  deleteTemplate: (id: string) => Promise<void>
  useTemplate: (id: string) => Promise<void>
  createFromConversation: (conversationId: string, title: string, description?: string, category?: string) => Promise<Template>
}

export const useTemplateStore = create<TemplateStore>((set, get) => ({
  templates: [],
  categories: [],
  selectedTemplate: null,
  isLoading: false,
  error: null,

  loadTemplates: async (category?: string) => {
    set({ isLoading: true, error: null })
    try {
      const url = category
        ? `/api/templates?category=${category}&is_active=true`
        : '/api/templates?is_active=true'
      const response = await fetch(url)
      if (!response.ok) throw new Error('Failed to load templates')
      const templates = await response.json()
      set({ templates, isLoading: false })
    } catch (error) {
      set({ error: (error as Error).message, isLoading: false })
    }
  },

  loadCategories: async () => {
    try {
      const response = await fetch('/api/templates/categories')
      if (!response.ok) throw new Error('Failed to load categories')
      const categories = await response.json()
      set({ categories })
    } catch (error) {
      console.error('Failed to load categories:', error)
    }
  },

  selectTemplate: (template) => {
    set({ selectedTemplate: template })
  },

  createTemplate: async (data) => {
    set({ isLoading: true, error: null })
    try {
      const response = await fetch('/api/templates', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      })
      if (!response.ok) throw new Error('Failed to create template')
      const template = await response.json()
      set((state) => ({ templates: [...state.templates, template], isLoading: false }))
      return template
    } catch (error) {
      set({ error: (error as Error).message, isLoading: false })
      throw error
    }
  },

  updateTemplate: async (id, data) => {
    set({ isLoading: true, error: null })
    try {
      const response = await fetch(`/api/templates/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      })
      if (!response.ok) throw new Error('Failed to update template')
      const updated = await response.json()
      set((state) => ({
        templates: state.templates.map((t) => (t.id === id ? updated : t)),
        isLoading: false,
      }))
    } catch (error) {
      set({ error: (error as Error).message, isLoading: false })
      throw error
    }
  },

  deleteTemplate: async (id) => {
    set({ isLoading: true, error: null })
    try {
      const response = await fetch(`/api/templates/${id}`, {
        method: 'DELETE',
      })
      if (!response.ok) throw new Error('Failed to delete template')
      set((state) => ({
        templates: state.templates.filter((t) => t.id !== id),
        isLoading: false,
      }))
    } catch (error) {
      set({ error: (error as Error).message, isLoading: false })
      throw error
    }
  },

  useTemplate: async (id) => {
    try {
      const response = await fetch(`/api/templates/${id}/use`, {
        method: 'POST',
      })
      if (!response.ok) throw new Error('Failed to use template')
      const updated = await response.json()
      set((state) => ({
        templates: state.templates.map((t) => (t.id === id ? updated : t)),
      }))
    } catch (error) {
      console.error('Failed to use template:', error)
      throw error
    }
  },

  createFromConversation: async (conversationId, title, description, category) => {
    set({ isLoading: true, error: null })
    try {
      const params = new URLSearchParams({
        title,
        ...(description && { description }),
        ...(category && { category }),
      })

      const response = await fetch(`/api/templates/from-conversation/${conversationId}?${params}`, {
        method: 'POST',
      })
      if (!response.ok) throw new Error('Failed to create template from conversation')
      const template = await response.json()
      set((state) => ({ templates: [...state.templates, template], isLoading: false }))
      return template
    } catch (error) {
      set({ error: (error as Error).message, isLoading: false })
      throw error
    }
  },
}))
