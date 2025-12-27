import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export interface RecentItem {
  id: string
  type: 'conversation' | 'file' | 'project'
  title: string
  subtitle?: string
  timestamp: string
  metadata?: Record<string, any>
}

interface RecentItemsState {
  items: RecentItem[]
  maxItems: number

  // Actions
  addRecentItem: (item: RecentItem) => void
  removeRecentItem: (id: string) => void
  clearRecentItems: () => void
  getRecentItems: (type?: 'conversation' | 'file' | 'project') => RecentItem[]
}

export const useRecentItemsStore = create<RecentItemsState>()(
  persist(
    (set, get) => ({
      items: [],
      maxItems: 10, // Keep only the 10 most recent items

      addRecentItem: (item: RecentItem) => {
        set((state) => {
          // Remove existing item with same ID
          const filtered = state.items.filter(i => i.id !== item.id)

          // Add new item at the beginning
          const newItems = [item, ...filtered]

          // Keep only the most recent maxItems
          return { items: newItems.slice(0, state.maxItems) }
        })
      },

      removeRecentItem: (id: string) => {
        set((state) => ({
          items: state.items.filter(item => item.id !== id)
        }))
      },

      clearRecentItems: () => {
        set({ items: [] })
      },

      getRecentItems: (type?: 'conversation' | 'file' | 'project') => {
        const state = get()
        if (type) {
          return state.items.filter(item => item.type === type)
        }
        return state.items
      },
    }),
    {
      name: 'claude-recent-items',
      partialize: (state) => ({ items: state.items }),
    }
  )
)
