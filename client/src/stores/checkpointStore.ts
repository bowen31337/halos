/**
 * Checkpoint Store
 * Manages conversation checkpoint functionality - creating, viewing, and restoring checkpoints
 */

import { create } from 'zustand'
import { api } from '../services/api'

export interface Checkpoint {
  id: string
  conversation_id: string
  name: string
  notes?: string
  state_snapshot: {
    messages: Array<{
      id: string
      role: 'user' | 'assistant'
      content: string
      created_at: string
    }>
    conversation_metadata: {
      title: string
      model: string
      thread_id?: string
      extended_thinking_enabled: boolean
    }
    artifacts: Array<{
      id: string
      title: string
      artifact_type: string
      content: string
    }>
  }
  created_at: string
  updated_at: string
}

interface CheckpointState {
  // State
  checkpoints: Checkpoint[]
  currentCheckpoint: Checkpoint | null
  isLoading: boolean
  isCreating: boolean
  isRestoring: boolean
  error: string | null

  // Actions
  loadCheckpoints: (conversationId: string) => Promise<void>
  createCheckpoint: (
    conversationId: string,
    name?: string,
    notes?: string
  ) => Promise<Checkpoint>
  getCheckpoint: (checkpointId: string) => Promise<Checkpoint>
  updateCheckpoint: (
    checkpointId: string,
    data: { name?: string; notes?: string }
  ) => Promise<Checkpoint>
  restoreCheckpoint: (checkpointId: string) => Promise<any>
  deleteCheckpoint: (checkpointId: string) => Promise<void>
  setCurrentCheckpoint: (checkpoint: Checkpoint | null) => void
  clearError: () => void
  clearCheckpoints: () => void
}

export const useCheckpointStore = create<CheckpointState>((set, get) => ({
  // Initial state
  checkpoints: [],
  currentCheckpoint: null,
  isLoading: false,
  isCreating: false,
  isRestoring: false,
  error: null,

  // Load all checkpoints for a conversation
  loadCheckpoints: async (conversationId: string) => {
    set({ isLoading: true, error: null })

    try {
      const checkpoints = await api.listCheckpoints(conversationId)
      set({ checkpoints })
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to load checkpoints'
      set({ error: errorMsg })
      throw err
    } finally {
      set({ isLoading: false })
    }
  },

  // Create a new checkpoint
  createCheckpoint: async (
    conversationId: string,
    name?: string,
    notes?: string
  ): Promise<Checkpoint> => {
    set({ isCreating: true, error: null })

    try {
      const checkpoint = await api.createCheckpoint(conversationId, { name, notes })
      set((state) => ({
        checkpoints: [checkpoint, ...state.checkpoints],
      }))
      return checkpoint
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to create checkpoint'
      set({ error: errorMsg })
      throw err
    } finally {
      set({ isCreating: false })
    }
  },

  // Get a specific checkpoint
  getCheckpoint: async (checkpointId: string): Promise<Checkpoint> => {
    set({ isLoading: true, error: null })

    try {
      const checkpoint = await api.getCheckpoint(checkpointId)
      set({ currentCheckpoint: checkpoint })
      return checkpoint
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to get checkpoint'
      set({ error: errorMsg })
      throw err
    } finally {
      set({ isLoading: false })
    }
  },

  // Update a checkpoint (name or notes)
  updateCheckpoint: async (
    checkpointId: string,
    data: { name?: string; notes?: string }
  ): Promise<Checkpoint> => {
    set({ error: null })

    try {
      const checkpoint = await api.updateCheckpoint(checkpointId, data)
      set((state) => ({
        checkpoints: state.checkpoints.map((cp) =>
          cp.id === checkpointId ? checkpoint : cp
        ),
        currentCheckpoint: state.currentCheckpoint?.id === checkpointId ? checkpoint : state.currentCheckpoint,
      }))
      return checkpoint
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to update checkpoint'
      set({ error: errorMsg })
      throw err
    }
  },

  // Restore conversation to a checkpoint
  restoreCheckpoint: async (checkpointId: string): Promise<any> => {
    set({ isRestoring: true, error: null })

    try {
      const result = await api.restoreCheckpoint(checkpointId)
      return result
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to restore checkpoint'
      set({ error: errorMsg })
      throw err
    } finally {
      set({ isRestoring: false })
    }
  },

  // Delete a checkpoint
  deleteCheckpoint: async (checkpointId: string): Promise<void> => {
    set({ error: null })

    try {
      await api.deleteCheckpoint(checkpointId)
      set((state) => ({
        checkpoints: state.checkpoints.filter((cp) => cp.id !== checkpointId),
        currentCheckpoint: state.currentCheckpoint?.id === checkpointId ? null : state.currentCheckpoint,
      }))
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to delete checkpoint'
      set({ error: errorMsg })
      throw err
    }
  },

  // Set current checkpoint
  setCurrentCheckpoint: (checkpoint: Checkpoint | null) => {
    set({ currentCheckpoint: checkpoint })
  },

  // Clear error
  clearError: () => {
    set({ error: null })
  },

  // Clear checkpoints
  clearCheckpoints: () => {
    set({ checkpoints: [], currentCheckpoint: null, error: null })
  },
}))
