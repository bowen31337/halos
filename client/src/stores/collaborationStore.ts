import { create } from 'zustand'
import { devtools } from 'zustand/middleware'

export interface CursorPosition {
  x: number
  y: number
  line?: number
  character?: number
}

export interface Collaborator {
  userId: string
  name: string
  color: string
  cursor?: CursorPosition
  lastSeen: string
}

export interface CollaborationEvent {
  eventType: 'cursor' | 'edit' | 'join' | 'leave' | 'presence'
  userId: string
  name?: string
  color?: string
  data?: any
  timestamp?: string
}

interface CollaborationState {
  // Connection state
  isConnected: boolean
  isConnecting: boolean
  connectionError: string | null

  // Active collaborators
  collaborators: Map<string, Collaborator>

  // Current user
  currentUserId: string
  currentUserName: string

  // WebSocket connection
  ws: WebSocket | null

  // Actions
  connect: (conversationId: string, userId: string, name: string) => void
  disconnect: () => void
  sendCursor: (position: CursorPosition) => void
  sendEdit: (editData: any) => void
  setUserName: (name: string) => void
  clearError: () => void
}

export const useCollaborationStore = create<CollaborationState>()(
  devtools((set, get) => ({
    isConnected: false,
    isConnecting: false,
    connectionError: null,
    collaborators: new Map(),
    currentUserId: '',
    currentUserName: 'Anonymous',
    ws: null,

    connect: (conversationId: string, userId: string, name: string) => {
      // Close existing connection
      if (get().ws) {
        get().ws.close()
      }

      set({ isConnecting: true, connectionError: null, currentUserId: userId, currentUserName: name })

      // Use WebSocket v2 for real-time collaboration
      const wsUrl = `ws://localhost:8000/api/collaboration/ws/v2/${conversationId}/${userId}?name=${encodeURIComponent(name)}`

      const ws = new WebSocket(wsUrl)

      ws.onopen = () => {
        set({ isConnected: true, isConnecting: false, ws })
        console.log('Collaboration connected')
      }

      ws.onclose = () => {
        set({ isConnected: false, isConnecting: false, ws: null })
        console.log('Collaboration disconnected')
      }

      ws.onerror = (error) => {
        set({
          isConnected: false,
          isConnecting: false,
          connectionError: 'Connection failed',
          ws: null
        })
        console.error('Collaboration error:', error)
      }

      ws.onmessage = (event) => {
        try {
          const data: CollaborationEvent = JSON.parse(event.data)
          handleCollaborationEvent(data, set, get)
        } catch (e) {
          console.error('Failed to parse collaboration message:', e)
        }
      }
    },

    disconnect: () => {
      const { ws } = get()
      if (ws) {
        ws.close()
      }
      set({
        isConnected: false,
        isConnecting: false,
        ws: null,
        collaborators: new Map()
      })
    },

    sendCursor: (position: CursorPosition) => {
      const { ws, isConnected } = get()
      if (ws && isConnected) {
        ws.send(JSON.stringify({
          event_type: 'cursor',
          data: position
        }))
      }
    },

    sendEdit: (editData: any) => {
      const { ws, isConnected } = get()
      if (ws && isConnected) {
        ws.send(JSON.stringify({
          event_type: 'edit',
          data: editData
        }))
      }
    },

    setUserName: (name: string) => {
      set({ currentUserName: name })
    },

    clearError: () => {
      set({ connectionError: null })
    }
  }))
)

// Handle incoming collaboration events
function handleCollaborationEvent(
  event: CollaborationEvent,
  set: any,
  get: () => CollaborationState
) {
  const { collaborators } = get()

  switch (event.eventType) {
    case 'presence':
      // Initial presence list
      if (event.data?.active_users) {
        const newCollaborators = new Map<string, Collaborator>()
        event.data.active_users.forEach((user: any) => {
          newCollaborators.set(user.user_id, {
            userId: user.user_id,
            name: user.name,
            color: user.color,
            cursor: user.cursor,
            lastSeen: user.last_seen
          })
        })
        set({ collaborators: newCollaborators })
      }
      break

    case 'join':
      if (event.userId && event.name && event.color) {
        const updated = new Map(collaborators)
        updated.set(event.userId, {
          userId: event.userId,
          name: event.name,
          color: event.color,
          lastSeen: event.timestamp || new Date().toISOString()
        })
        set({ collaborators: updated })
      }
      break

    case 'leave':
      const updatedLeave = new Map(collaborators)
      updatedLeave.delete(event.userId)
      set({ collaborators: updatedLeave })
      break

    case 'cursor':
      if (event.userId && event.data) {
        const updatedCursor = new Map(collaborators)
        const existing = updatedCursor.get(event.userId)
        if (existing) {
          updatedCursor.set(event.userId, {
            ...existing,
            cursor: event.data,
            lastSeen: event.timestamp || new Date().toISOString()
          })
          set({ collaborators: updatedCursor })
        }
      }
      break

    case 'edit':
      // Handle edit events - could trigger UI updates or notifications
      console.log('Collaborator edit:', event)
      break
  }
}
