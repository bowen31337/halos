/**
 * Conversation Branching Store
 * Manages conversation branching functionality in the frontend
 */

import { create } from 'zustand'
import { api } from '../services/api'
import type { Conversation } from './conversationStore'

export interface BranchInfo {
  id: string
  title: string
  branchName?: string
  branchColor?: string
  parentId?: string
  createdAt: string
}

export interface BranchPathNode {
  id: string
  title: string
  branchColor?: string
}

interface BranchingState {
  // State
  branches: BranchInfo[]
  branchHistory: any[]
  branchPath: BranchPathNode[]
  isBranching: boolean
  currentBranchInfo: any
  error: string | null

  // Actions
  createBranch: (
    conversationId: string,
    branchPointMessageId: string,
    branchName?: string,
    branchColor?: string
  ) => Promise<Conversation>
  loadBranches: (conversationId: string) => Promise<void>
  loadBranchHistory: (conversationId: string) => Promise<void>
  loadBranchPath: (conversationId: string) => Promise<void>
  switchBranch: (conversationId: string, targetConversationId: string) => Promise<any>
  clearBranches: () => void
  clearError: () => void
  initialize: (conversationId: string) => Promise<void>
}

export const useBranchingStore = create<BranchingState>((set, get) => ({
  // Initial state
  branches: [],
  branchHistory: [],
  branchPath: [],
  isBranching: false,
  currentBranchInfo: null,
  error: null,

  // Create a new branch from a message
  createBranch: async (
    conversationId: string,
    branchPointMessageId: string,
    branchName?: string,
    branchColor?: string
  ): Promise<Conversation> => {
    set({ isBranching: true, error: null })

    try {
      const result = await api.createConversationBranch(
        conversationId,
        branchPointMessageId,
        branchName,
        branchColor
      )

      // Update branches list
      const newBranch: BranchInfo = {
        id: result.conversation.id,
        title: result.conversation.title,
        branchName: result.conversation.branch_name,
        branchColor: result.conversation.branch_color,
        parentId: result.conversation.parent_id,
        createdAt: result.conversation.created_at
      }

      set((state) => ({
        branches: [...state.branches, newBranch]
      }))

      return result.conversation
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to create branch'
      set({ error: errorMsg })
      throw err
    } finally {
      set({ isBranching: false })
    }
  },

  // Load all branches for a conversation
  loadBranches: async (conversationId: string) => {
    set({ error: null })

    try {
      const result = await api.listConversationBranches(conversationId)
      // Transform the response to our BranchInfo format
      const branches: BranchInfo[] = result.branches?.map((b: any) => ({
        id: b.id,
        title: b.title,
        branchName: b.branch_name,
        branchColor: b.branch_color,
        parentId: b.parent_id,
        createdAt: b.created_at
      })) || []
      set({ branches })
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to load branches'
      set({ error: errorMsg })
    }
  },

  // Load branch history
  loadBranchHistory: async (conversationId: string) => {
    set({ error: null })

    try {
      const result = await api.getConversationBranchHistory(conversationId)
      set({
        branchHistory: result.branch_history || [],
        currentBranchInfo: {
          depth: result.current_branch_depth,
          isBranch: result.current_branch_depth > 1
        }
      })
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to load branch history'
      set({ error: errorMsg })
    }
  },

  // Load branch path (the lineage from root to current)
  loadBranchPath: async (conversationId: string) => {
    set({ error: null })

    try {
      const result = await api.getConversationBranchPath(conversationId)
      const branchPath: BranchPathNode[] = result.branch_path?.map((p: any) => ({
        id: p.id,
        title: p.title,
        branchColor: p.branch_color
      })) || []

      set({
        branchPath,
        currentBranchInfo: {
          isBranch: result.is_branch,
          rootConversationId: result.root_conversation_id
        }
      })
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to load branch path'
      set({ error: errorMsg })
    }
  },

  // Switch to a different branch
  switchBranch: async (conversationId: string, targetConversationId: string) => {
    set({ isBranching: true, error: null })

    try {
      const result = await api.switchToBranch(conversationId, targetConversationId)
      return result
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to switch branch'
      set({ error: errorMsg })
      throw err
    } finally {
      set({ isBranching: false })
    }
  },

  // Clear all branch data
  clearBranches: () => {
    set({
      branches: [],
      branchHistory: [],
      branchPath: [],
      currentBranchInfo: null,
      error: null
    })
  },

  // Clear error
  clearError: () => {
    set({ error: null })
  },

  // Initialize with current conversation
  initialize: async (conversationId: string) => {
    await Promise.all([
      get().loadBranches(conversationId),
      get().loadBranchPath(conversationId)
    ])
  }
}))
