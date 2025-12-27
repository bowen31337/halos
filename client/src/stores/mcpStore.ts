import { create } from 'zustand'

export interface MCPServer {
  id: string
  name: string
  server_type: string
  config: Record<string, any>
  description?: string
  is_active: boolean
  last_health_check?: string
  health_status?: string
  available_tools: string[]
  usage_count: number
  created_at: string
  updated_at: string
}

export interface MCPState {
  servers: MCPServer[]
  serverTypes: Array<{
    type: string
    label: string
    description: string
    config_fields: string[]
  }>
  isLoading: boolean
  error: string | null

  // Actions
  fetchServers: () => Promise<void>
  fetchServerTypes: () => Promise<void>
  createServer: (data: {
    name: string
    server_type: string
    config: Record<string, any>
    description?: string
  }) => Promise<MCPServer>
  updateServer: (id: string, data: {
    name?: string
    config?: Record<string, any>
    description?: string
    is_active?: boolean
  }) => Promise<void>
  deleteServer: (id: string) => Promise<void>
  testServer: (id: string) => Promise<any>
  testConnection: (server_type: string, config: Record<string, any>) => Promise<any>
  getServerTools: (id: string) => Promise<any>
}

export const useMCPStore = create<MCPState>((set, get) => ({
  servers: [],
  serverTypes: [],
  isLoading: false,
  error: null,

  fetchServers: async () => {
    set({ isLoading: true, error: null })
    try {
      const response = await fetch('/api/mcp')
      if (!response.ok) throw new Error('Failed to fetch servers')
      const servers = await response.json()
      set({ servers, isLoading: false })
    } catch (error) {
      set({ error: (error as Error).message, isLoading: false })
      throw error
    }
  },

  fetchServerTypes: async () => {
    set({ isLoading: true, error: null })
    try {
      const response = await fetch('/api/mcp/types/list')
      if (!response.ok) throw new Error('Failed to fetch server types')
      const serverTypes = await response.json()
      set({ serverTypes, isLoading: false })
    } catch (error) {
      set({ error: (error as Error).message, isLoading: false })
      throw error
    }
  },

  createServer: async (data) => {
    set({ isLoading: true, error: null })
    try {
      const response = await fetch('/api/mcp', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      })
      if (!response.ok) throw new Error('Failed to create server')
      const server = await response.json()
      set((state) => ({ servers: [...state.servers, server], isLoading: false }))
      return server
    } catch (error) {
      set({ error: (error as Error).message, isLoading: false })
      throw error
    }
  },

  updateServer: async (id, data) => {
    set({ isLoading: true, error: null })
    try {
      const response = await fetch(`/api/mcp/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      })
      if (!response.ok) throw new Error('Failed to update server')
      set((state) => ({
        servers: state.servers.map((s) => (s.id === id ? { ...s, ...data } : s)),
        isLoading: false,
      }))
    } catch (error) {
      set({ error: (error as Error).message, isLoading: false })
      throw error
    }
  },

  deleteServer: async (id) => {
    set({ isLoading: true, error: null })
    try {
      const response = await fetch(`/api/mcp/${id}`, { method: 'DELETE' })
      if (!response.ok) throw new Error('Failed to delete server')
      set((state) => ({
        servers: state.servers.filter((s) => s.id !== id),
        isLoading: false,
      }))
    } catch (error) {
      set({ error: (error as Error).message, isLoading: false })
      throw error
    }
  },

  testServer: async (id) => {
    set({ isLoading: true, error: null })
    try {
      const response = await fetch(`/api/mcp/${id}/test`, { method: 'POST' })
      if (!response.ok) throw new Error('Failed to test server')
      const result = await response.json()
      set({ isLoading: false })
      return result
    } catch (error) {
      set({ error: (error as Error).message, isLoading: false })
      throw error
    }
  },

  testConnection: async (server_type, config) => {
    set({ isLoading: true, error: null })
    try {
      const response = await fetch('/api/mcp/test-connection', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ server_type, config }),
      })
      if (!response.ok) throw new Error('Failed to test connection')
      const result = await response.json()
      set({ isLoading: false })
      return result
    } catch (error) {
      set({ error: (error as Error).message, isLoading: false })
      throw error
    }
  },

  getServerTools: async (id) => {
    set({ isLoading: true, error: null })
    try {
      const response = await fetch(`/api/mcp/${id}/tools`, { method: 'POST' })
      if (!response.ok) throw new Error('Failed to get server tools')
      const result = await response.json()
      set({ isLoading: false })
      return result
    } catch (error) {
      set({ error: (error as Error).message, isLoading: false })
      throw error
    }
  },
}))
