import { useEffect, useState, useCallback } from 'react'
import { useSessionStore } from '../stores/sessionStore'
import { useAuthStore } from '../stores/authStore'
import { api } from '../lib/api'

/**
 * Enhanced session timeout hook that integrates with backend session management
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

  const { isAuthenticated, logout, refreshToken } = useAuthStore()

  const [showWarning, setShowWarning] = useState(false)
  const [showTimeout, setShowTimeout] = useState(false)
  const [isRefreshing, setIsRefreshing] = useState(false)

  // Monitor user activity
  useEffect(() => {
    if (!isAuthenticated) return

    const handleUserActivity = () => {
      if (isTimedOut) return // Don't update activity if timed out
      updateActivity()

      // Update backend session activity
      api.post('/auth/extend-session').catch(() => {
        // If backend session is invalid, refresh token
        handleTokenRefresh()
      })
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
  }, [isAuthenticated, isTimedOut, updateActivity])

  // Check for timeout periodically
  useEffect(() => {
    if (!isAuthenticated || !isSessionActive) return

    const interval = setInterval(() => {
      const timedOut = checkSessionTimeout()
      if (timedOut) {
        handleTimeout()
        setShowTimeout(true)
        setShowWarning(false)
      }
    }, 1000) // Check every second

    return () => clearInterval(interval)
  }, [isAuthenticated, isSessionActive, checkSessionTimeout, handleTimeout])

  // Sync warning state with store
  useEffect(() => {
    setShowWarning(timeoutWarningShown && !isTimedOut)
  }, [timeoutWarningShown, isTimedOut])

  // Handle token refresh for session extension
  const handleTokenRefresh = useCallback(async () => {
    if (isRefreshing) return

    setIsRefreshing(true)
    try {
      await refreshToken()
      // Reset session on successful refresh
      resetSession()
      setShowWarning(false)
      setShowTimeout(false)
    } catch (error) {
      console.error('Token refresh failed:', error)
      // If refresh fails, logout
      handleLogout()
    } finally {
      setIsRefreshing(false)
    }
  }, [refreshToken, resetSession, handleLogout, isRefreshing])

  // Handle session reset (e.g., after re-auth)
  const handleSessionReset = useCallback(async () => {
    try {
      // Try to refresh token first
      await handleTokenRefresh()
      resetSession()
      setShowWarning(false)
      setShowTimeout(false)
    } catch (error) {
      console.error('Session reset failed:', error)
      handleLogout()
    }
  }, [handleTokenRefresh, resetSession, handleLogout])

  const handleLogout = useCallback(() => {
    // Clear session data
    preserveCurrentData()
    resetSession()
    logout()
    setShowWarning(false)
    setShowTimeout(false)
  }, [preserveCurrentData, resetSession, logout])

  // Listen for session timeout headers from backend
  useEffect(() => {
    const handleResponse = (event: Event) => {
      const response = (event as CustomEvent).detail
      const sessionWarning = response.headers?.get('X-Session-Warning')
      const sessionStatus = response.headers?.get('X-Session-Status')

      if (sessionStatus === 'timeout') {
        setShowTimeout(true)
        setShowWarning(false)
      } else if (sessionWarning === 'token_expiring_soon') {
        setShowWarning(true)
      }
    }

    window.addEventListener('session-warning', handleResponse as EventListener)
    window.addEventListener('session-timeout', handleResponse as EventListener)

    return () => {
      window.removeEventListener('session-warning', handleResponse as EventListener)
      window.removeEventListener('session-timeout', handleResponse as EventListener)
    }
  }, [])

  return {
    showWarning,
    showTimeout,
    isTimedOut,
    isSessionActive,
    isRefreshing,
    handleSessionReset,
    handleLogout,
    handleTokenRefresh
  }
}