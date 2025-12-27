import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { api } from '../services/api'

interface SessionState {
  // Session state
  lastActivity: number
  sessionStartTime: number
  isSessionActive: boolean
  isTimedOut: boolean
  timeoutWarningShown: boolean

  // Timeout configuration (in minutes)
  timeoutDuration: number
  warningDuration: number

  // Actions
  updateActivity: () => void
  checkSessionTimeout: () => boolean
  showTimeoutWarning: () => void
  handleTimeout: () => void
  resetSession: () => void
  extendSession: () => Promise<void>

  // Data preservation
  preservedData: {
    conversations: any[]
    messages: Record<string, any[]>
    settings: any
    draftMessage: string
  }
  preserveCurrentData: () => void
  restorePreservedData: () => void
  clearPreservedData: () => void
}

export const useSessionStore = create<SessionState>()(
  persist(
    (set, get) => ({
      // Initial state
      lastActivity: Date.now(),
      sessionStartTime: Date.now(),
      isSessionActive: true,
      isTimedOut: false,
      timeoutWarningShown: false,

      // 30 minute timeout, 5 minute warning
      timeoutDuration: 30,
      warningDuration: 5,

      // Actions
      updateActivity: () => {
        set({
          lastActivity: Date.now(),
          isSessionActive: true,
          timeoutWarningShown: false
        })
      },

      checkSessionTimeout: () => {
        const { lastActivity, timeoutDuration, isSessionActive, isTimedOut } = get()
        const now = Date.now()
        const minutesSinceLastActivity = (now - lastActivity) / (1000 * 60)

        if (isSessionActive && minutesSinceLastActivity >= timeoutDuration) {
          // Session timed out
          if (!isTimedOut) {
            set({ isTimedOut: true, isSessionActive: false })
            return true
          }
        }

        // Check if warning should be shown
        if (isSessionActive && !get().timeoutWarningShown) {
          const warningThreshold = timeoutDuration - get().warningDuration
          if (minutesSinceLastActivity >= warningThreshold) {
            set({ timeoutWarningShown: true })
          }
        }

        return false
      },

      showTimeoutWarning: () => {
        set({ timeoutWarningShown: true })
      },

      handleTimeout: () => {
        // Preserve data before clearing
        get().preserveCurrentData()
        set({
          isTimedOut: true,
          isSessionActive: false,
          timeoutWarningShown: false
        })
      },

      resetSession: () => {
        set({
          lastActivity: Date.now(),
          sessionStartTime: Date.now(),
          isSessionActive: true,
          isTimedOut: false,
          timeoutWarningShown: false
        })
      },

      extendSession: async () => {
        // Called when user clicks "extend session" or re-authenticates
        try {
          // Try to refresh the access token using refresh token
          const refreshToken = api.getRefreshToken()
          if (refreshToken) {
            await api.refreshToken(refreshToken)
            console.log('Access token refreshed on backend')
          } else {
            // Fallback to keep-alive endpoint
            await api.keepSessionAlive()
            console.log('Session kept alive on backend')
          }
        } catch (e) {
          console.warn('Could not refresh session on backend:', e)
        }
        get().resetSession()
        // Restore preserved data if available
        get().restorePreservedData()
      },

      // Data preservation
      preservedData: {
        conversations: [],
        messages: {},
        settings: {},
        draftMessage: ''
      },

      preserveCurrentData: () => {
        // This will be called before timeout to save current state
        // In a real app, this would pull from other stores
        const { useUIStore } = require('./uiStore')
        const { useConversationStore } = require('./conversationStore')

        try {
          const uiStore = useUIStore.getState()
          const convStore = useConversationStore ? useConversationStore.getState() : null

          const preservedData = {
            conversations: convStore?.conversations || [],
            messages: convStore?.messages || {},
            settings: {
              theme: uiStore.theme,
              fontSize: uiStore.fontSize,
              highContrast: uiStore.highContrast,
              colorBlindMode: uiStore.colorBlindMode
            },
            draftMessage: uiStore.inputMessage || ''
          }

          set({ preservedData })

          // Also save to localStorage for extra persistence
          localStorage.setItem('claude-session-preserved', JSON.stringify(preservedData))
        } catch (e) {
          console.warn('Failed to preserve session data:', e)
        }
      },

      restorePreservedData: () => {
        try {
          // Try to restore from store first
          const { preservedData } = get()

          // If store is empty, try localStorage
          if (!preservedData.conversations.length) {
            const saved = localStorage.getItem('claude-session-preserved')
            if (saved) {
              const parsed = JSON.parse(saved)
              set({ preservedData: parsed })
              return parsed
            }
          }

          return preservedData
        } catch (e) {
          console.warn('Failed to restore session data:', e)
          return null
        }
      },

      clearPreservedData: () => {
        set({
          preservedData: {
            conversations: [],
            messages: {},
            settings: {},
            draftMessage: ''
          }
        })
        localStorage.removeItem('claude-session-preserved')
      }
    }),
    {
      name: 'claude-session-state',
      partialize: (state) => ({
        lastActivity: state.lastActivity,
        sessionStartTime: state.sessionStartTime,
        isSessionActive: state.isSessionActive,
        isTimedOut: state.isTimedOut,
        timeoutWarningShown: state.timeoutWarningShown,
        preservedData: state.preservedData
      })
    }
  )
)
