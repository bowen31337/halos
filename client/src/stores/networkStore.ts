import { create } from 'zustand'

export interface QueuedAction {
  id: string
  type: 'send_message' | 'create_conversation' | 'update_settings'
  payload: any
  timestamp: number
  retryCount?: number
}

interface NetworkState {
  isOnline: boolean
  isOffline: boolean
  retryCount: number
  lastOnlineCheck: Date | null
  reconnectAttempts: number
  actionQueue: QueuedAction[]

  // Actions
  setOnline: (online: boolean) => void
  incrementRetry: () => void
  resetRetry: () => void
  incrementReconnectAttempts: () => void
  resetReconnectAttempts: () => void
  queueAction: (action: Omit<QueuedAction, 'id' | 'timestamp'>) => void
  dequeueAction: (id: string) => void
  getQueuedActions: () => QueuedAction[]
  clearQueue: () => void
  processQueue: () => Promise<void>
}

export const useNetworkStore = create<NetworkState>((set, get) => ({
  isOnline: typeof window !== 'undefined' ? navigator.onLine : true,
  isOffline: typeof window !== 'undefined' ? !navigator.onLine : false,
  retryCount: 0,
  lastOnlineCheck: null,
  reconnectAttempts: 0,
  actionQueue: [],

  setOnline: (online: boolean) => {
    set({
      isOnline: online,
      isOffline: !online,
      lastOnlineCheck: new Date()
    })
  },

  incrementRetry: () => {
    set((state) => ({ retryCount: state.retryCount + 1 }))
  },

  resetRetry: () => {
    set({ retryCount: 0 })
  },

  incrementReconnectAttempts: () => {
    set((state) => ({ reconnectAttempts: state.reconnectAttempts + 1 }))
  },

  resetReconnectAttempts: () => {
    set({ reconnectAttempts: 0 })
  },

  queueAction: (action: Omit<QueuedAction, 'id' | 'timestamp'>) => {
    const queuedAction: QueuedAction = {
      id: `${action.type}-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      ...action,
      timestamp: Date.now(),
      retryCount: 0
    }
    set((state) => ({
      actionQueue: [...state.actionQueue, queuedAction]
    }))
    // Persist queue to localStorage
    try {
      const existingQueue = JSON.parse(localStorage.getItem('claude-offline-queue') || '[]')
      localStorage.setItem('claude-offline-queue', JSON.stringify([...existingQueue, queuedAction]))
    } catch (e) {
      console.warn('Failed to persist offline queue:', e)
    }
  },

  dequeueAction: (id: string) => {
    set((state) => {
      const newQueue = state.actionQueue.filter(action => action.id !== id)
      // Update localStorage
      try {
        localStorage.setItem('claude-offline-queue', JSON.stringify(newQueue))
      } catch (e) {
        console.warn('Failed to update offline queue:', e)
      }
      return { actionQueue: newQueue }
    })
  },

  getQueuedActions: () => {
    return get().actionQueue
  },

  clearQueue: () => {
    set({ actionQueue: [] })
    try {
      localStorage.removeItem('claude-offline-queue')
    } catch (e) {
      console.warn('Failed to clear offline queue:', e)
    }
  },

  processQueue: async () => {
    const { actionQueue, dequeueAction, isOnline, clearQueue } = get()

    if (!isOnline || actionQueue.length === 0) {
      return
    }

    console.log(`Processing ${actionQueue.length} queued actions...`)

    // Process actions in order
    for (const action of actionQueue) {
      try {
        console.log('Processing queued action:', action.type, action.payload)

        // Process based on action type
        if (action.type === 'send_message') {
          // Use fetch directly to avoid circular dependencies
          const { conversationId, content } = action.payload

          // First, try to create the conversation if it's a placeholder
          let finalConvId = conversationId
          if (conversationId === 'offline-placeholder') {
            try {
              const convResponse = await fetch('/api/conversations', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ title: 'New Conversation' })
              })
              if (convResponse.ok) {
                const newConv = await convResponse.json()
                finalConvId = newConv.id
              }
            } catch (e) {
              console.warn('Could not create conversation:', e)
            }
          }

          // Send the message
          try {
            await fetch(`/api/messages/conversations/${finalConvId}/messages`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ content, role: 'user' })
            })
            console.log('Successfully sent queued message')
          } catch (e) {
            console.error('Failed to send queued message:', e)
            throw e
          }
        }

        // If successful, dequeue
        dequeueAction(action.id)
      } catch (error) {
        console.error('Failed to process queued action:', action.id, error)
        // Increment retry count - could be used for retry logic
        action.retryCount = (action.retryCount || 0) + 1
      }
    }

    // If all actions processed successfully, clear the queue
    if (actionQueue.length === 0) {
      clearQueue()
    }
  },
}))
