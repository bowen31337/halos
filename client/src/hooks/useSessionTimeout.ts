import { useEffect, useState } from 'react'
import { useSessionStore } from '../stores/sessionStore'
import { api } from '../services/api'

/**
 * Hook to monitor session timeout and show warnings
 * Integrates with the session store to track activity and handle timeouts
 * Also integrates with backend API for JWT token refresh
 */
export function useSessionTimeout() {
  const {
    lastActivity,
    isSessionActive,
    isTimedOut,
    timeoutWarningShown,
    updateActivity,
    checkSessionTimeout,
    handleTimeout,
    preserveCurrentData,
    resetSession
  } = useSessionStore()

  const [showWarning, setShowWarning] = useState(false)
  const [showTimeout, setShowTimeout] = useState(false)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [refreshError, setRefreshError] = useState<string | null>(null)

  // Monitor user activity
  useEffect(() => {
    const handleUserActivity = () => {
      if (isTimedOut) return // Don't update activity if timed out
      updateActivity()
    }

    // Listen for various user activities
    const events = ['mousedown', 'keydown', 'scroll', 'touchstart', 'mousemove']
    events.forEach(event => {
      window.addEventListener(event, handleUserActivity, { passive: true })
    })

    // Also track visibility changes
    const handleVisibility = () => {
      if (document.visibilityState === 'visible') {
        handleUserActivity()
      }
    }
    document.addEventListener('visibilitychange', handleVisibility)

    return () => {
      events.forEach(event => {
        window.removeEventListener(event, handleUserActivity)
      })
      document.removeEventListener('visibilitychange', handleVisibility)
    }
  }, [isTimedOut, updateActivity])

  // Check for timeout periodically
  useEffect(() => {
    if (!isSessionActive) return

    const interval = setInterval(() => {
      const timedOut = checkSessionTimeout()
      if (timedOut) {
        handleTimeout()
        setShowTimeout(true)
        setShowWarning(false)
      }
    }, 1000) // Check every second

    return () => clearInterval(interval)
  }, [isSessionActive, checkSessionTimeout, handleTimeout])

  // Sync warning state with store
  useEffect(() => {
    setShowWarning(timeoutWarningShown && !isTimedOut)
  }, [timeoutWarningShown, isTimedOut])

  // Handle session reset with backend integration
  const handleSessionReset = async () => {
    setIsRefreshing(true)
    setRefreshError(null)

    try {
      // Try to refresh the JWT token with backend
      const currentToken = api.getAccessToken()
      if (currentToken) {
        await api.refreshToken(currentToken)
      }

      // Reset local session state
      resetSession()
      setShowWarning(false)
      setShowTimeout(false)
    } catch (error) {
      console.error('Failed to refresh session:', error)
      setRefreshError('Failed to refresh session. Please log in again.')
      // Still reset local state even if backend refresh fails
      resetSession()
      setShowWarning(false)
      setShowTimeout(false)
    } finally {
      setIsRefreshing(false)
    }
  }

  const handleLogout = async () => {
    // Clear session data
    preserveCurrentData()

    try {
      // Call backend logout
      await api.logout()
    } catch (error) {
      console.error('Logout error:', error)
    }

    // Clear local state
    resetSession()
    setShowWarning(false)
    setShowTimeout(false)
    // In a real app, this would redirect to login
    console.log('User logged out due to timeout')
  }

  // Extend session (called when user clicks "Extend Session" in warning modal)
  const handleExtendSession = async () => {
    setIsRefreshing(true)
    setRefreshError(null)

    try {
      // Refresh the JWT token with backend
      const currentToken = api.getAccessToken()
      if (currentToken) {
        await api.refreshToken(currentToken)
      }

      // Update local activity to reset timeout timer
      updateActivity()
      setShowWarning(false)

      // Reset warning state in store
      const store = useSessionStore.getState()
      if (store.timeoutWarningShown) {
        resetSession()
      }
    } catch (error) {
      console.error('Failed to extend session:', error)
      setRefreshError('Failed to extend session. Please log in again.')
    } finally {
      setIsRefreshing(false)
    }
  }

  return {
    showWarning,
    showTimeout,
    isTimedOut,
    isSessionActive,
    isRefreshing,
    refreshError,
    handleSessionReset,
    handleLogout,
    handleExtendSession
  }
}
