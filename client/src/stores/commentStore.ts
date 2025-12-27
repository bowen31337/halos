/**
 * Comment Store - Manages comments on shared conversations
 */

import { create } from 'zustand'
import { api } from '@/services/api'

export interface Comment {
  id: string
  message_id: string
  conversation_id: string
  user_id: string | null
  anonymous_name: string | null
  content: string
  parent_comment_id: string | null
  created_at: string
  updated_at: string | null
  replies: Comment[]
}

interface CommentState {
  comments: Comment[]
  isLoading: boolean
  error: string | null
  activeMessageId: string | null
  replyToComment: Comment | null

  // Actions
  loadComments: (shareToken: string, messageId?: string) => Promise<void>
  createComment: (shareToken: string, data: {
    message_id: string
    content: string
    parent_comment_id?: string
    anonymous_name?: string
  }) => Promise<Comment>
  updateComment: (shareToken: string, commentId: string, content: string) => Promise<Comment>
  deleteComment: (shareToken: string, commentId: string) => Promise<void>
  setActiveMessageId: (messageId: string | null) => void
  setReplyToComment: (comment: Comment | null) => void
  clearComments: () => void
  setError: (error: string | null) => void
}

export const useCommentStore = create<CommentState>((set, get) => ({
  comments: [],
  isLoading: false,
  error: null,
  activeMessageId: null,
  replyToComment: null,

  loadComments: async (shareToken: string, messageId?: string) => {
    set({ isLoading: true, error: null })
    try {
      const comments = await api.getComments(shareToken, messageId)
      set({ comments, isLoading: false })
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Failed to load comments',
        isLoading: false
      })
    }
  },

  createComment: async (shareToken: string, data) => {
    set({ isLoading: true, error: null })
    try {
      const comment = await api.createComment(shareToken, data)
      set((state) => ({
        comments: [...state.comments, comment],
        isLoading: false
      }))
      return comment
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Failed to create comment',
        isLoading: false
      })
      throw error
    }
  },

  updateComment: async (shareToken: string, commentId: string, content: string) => {
    set({ isLoading: true, error: null })
    try {
      const updated = await api.updateComment(shareToken, commentId, content)
      set((state) => ({
        comments: state.comments.map(c => c.id === commentId ? updated : c),
        isLoading: false
      }))
      return updated
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Failed to update comment',
        isLoading: false
      })
      throw error
    }
  },

  deleteComment: async (shareToken: string, commentId: string) => {
    set({ isLoading: true, error: null })
    try {
      await api.deleteComment(shareToken, commentId)
      set((state) => ({
        comments: state.comments.filter(c => c.id !== commentId),
        isLoading: false
      }))
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Failed to delete comment',
        isLoading: false
      })
      throw error
    }
  },

  setActiveMessageId: (messageId: string | null) => {
    set({ activeMessageId: messageId })
  },

  setReplyToComment: (comment: Comment | null) => {
    set({ replyToComment: comment })
  },

  clearComments: () => {
    set({ comments: [], error: null, activeMessageId: null, replyToComment: null })
  },

  setError: (error: string | null) => {
    set({ error })
  }
}))
