/**
 * Sharing Store - Manages conversation sharing state
 */

import { create } from 'zustand'
import { api } from '@/services/api'

export interface ShareLink {
  id: string
  share_token: string
  conversation_id: string
  access_level: 'read' | 'comment' | 'edit'
  allow_comments: boolean
  is_public: boolean
  created_at: string
  expires_at: string | null
  view_count: number
  last_viewed_at: string | null
}

export interface SharedConversation {
  id: string
  title: string
  model: string
  messages: Array<{
    id: string
    role: string
    content: string
    created_at: string
  }>
  access_level: string
  allow_comments: boolean
}

interface SharingState {
  shares: ShareLink[]
  sharedConversation: SharedConversation | null
  isLoading: boolean
  error: string | null

  // Actions
  loadShares: (conversationId: string) => Promise<void>
  createShareLink: (conversationId: string, config: {
    access_level?: 'read' | 'comment' | 'edit'
    allow_comments?: boolean
    expires_in_days?: number
  }) => Promise<ShareLink>
  loadSharedConversation: (shareToken: string) => Promise<void>
  revokeShareLink: (shareToken: string) => Promise<void>
  revokeAllShares: (conversationId: string) => Promise<void>
  clearSharedConversation: () => void
  setError: (error: string | null) => void
}

export const useSharingStore = create<SharingState>((set, get) => ({
  shares: [],
  sharedConversation: null,
  isLoading: false,
  error: null,

  loadShares: async (conversationId: string) => {
    set({ isLoading: true, error: null })
    try {
      const shares = await api.listShares(conversationId)
      set({ shares, isLoading: false })
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Failed to load shares',
        isLoading: false
      })
    }
  },

  createShareLink: async (conversationId: string, config) => {
    set({ isLoading: true, error: null })
    try {
      const share = await api.createShareLink(conversationId, config)
      set((state) => ({
        shares: [share, ...state.shares],
        isLoading: false
      }))
      return share
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Failed to create share link',
        isLoading: false
      })
      throw error
    }
  },

  loadSharedConversation: async (shareToken: string) => {
    set({ isLoading: true, error: null })
    try {
      const conversation = await api.getSharedConversation(shareToken)
      set({ sharedConversation: conversation, isLoading: false })
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Failed to load shared conversation',
        isLoading: false
      })
      throw error
    }
  },

  revokeShareLink: async (shareToken: string) => {
    set({ isLoading: true, error: null })
    try {
      await api.revokeShareLink(shareToken)
      set((state) => ({
        shares: state.shares.filter(s => s.share_token !== shareToken),
        isLoading: false
      }))
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Failed to revoke share link',
        isLoading: false
      })
      throw error
    }
  },

  revokeAllShares: async (conversationId: string) => {
    set({ isLoading: true, error: null })
    try {
      await api.revokeAllShares(conversationId)
      set({ shares: [], isLoading: false })
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Failed to revoke all shares',
        isLoading: false
      })
      throw error
    }
  },

  clearSharedConversation: () => {
    set({ sharedConversation: null, error: null })
  },

  setError: (error: string | null) => {
    set({ error })
  }
}))
