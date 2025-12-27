import { useEffect, useState } from 'react'
import { useSessionStore } from '../stores/sessionStore'

interface SessionTimeoutModalProps {
  onClose: () => void
  onExtendSession: () => Promise<void>
  onLogout: () => Promise<void>
}

/**
 * SessionTimeoutModal - Shows warning before session timeout
 * or handles the timeout state with re-authentication options
 */
export function SessionTimeoutModal({ onClose, onExtendSession, onLogout }: SessionTimeoutModalProps) {
  const {
    isTimedOut,
    timeoutWarningShown,
    checkSessionTimeout,
    extendSession,
    preserveCurrentData,
    preservedData
  } = useSessionStore()

  const [timeRemaining, setTimeRemaining] = useState(0)
  const [isExtending, setIsExtending] = useState(false)

  // Countdown timer
  useEffect(() => {
    if (!timeoutWarningShown && !isTimedOut) return

    const interval = setInterval(() => {
      checkSessionTimeout()
    }, 1000) // Check every second

    return () => clearInterval(interval)
  }, [timeoutWarningShown, isTimedOut, checkSessionTimeout])

  // Calculate time remaining for warning mode
  useEffect(() => {
    if (!timeoutWarningShown || isTimedOut) return

    const interval = setInterval(() => {
      const { lastActivity, timeoutDuration, warningDuration } = useSessionStore.getState()
      const now = Date.now()
      const minutesSinceLastActivity = (now - lastActivity) / (1000 * 60)
      const timeLeft = timeoutDuration - minutesSinceLastActivity
      setTimeRemaining(Math.max(0, timeLeft * 60)) // Convert to seconds
    }, 1000)

    return () => clearInterval(interval)
  }, [timeoutWarningShown, isTimedOut])

  const handleExtend = async () => {
    setIsExtending(true)
    try {
      // Call the parent's extend session handler (which refreshes JWT token)
      await onExtendSession()
      // Also update local session store
      await extendSession()
      onClose()
    } catch (error) {
      console.error('Failed to extend session:', error)
    } finally {
      setIsExtending(false)
    }
  }

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  if (isTimedOut) {
    return (
      <div className="fixed inset-0 z-[10000] flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
        <div
          className="w-full max-w-md bg-[var(--bg-primary)] border border-[var(--border-primary)] rounded-xl shadow-2xl p-6"
          role="dialog"
          aria-labelledby="timeout-title"
          aria-modal="true"
        >
          <div className="flex items-center gap-3 mb-4">
            <svg className="w-6 h-6 text-[var(--error)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <h2 id="timeout-title" className="text-lg font-semibold text-[var(--text-primary)]">
              Session Timed Out
            </h2>
          </div>

          <p className="text-[var(--text-secondary)] mb-6">
            Your session has expired due to inactivity. Your data has been preserved and can be restored after re-authentication.
          </p>

          {preservedData.conversations.length > 0 && (
            <div className="mb-6 p-3 bg-[var(--bg-secondary)] rounded-lg text-sm">
              <div className="font-medium text-[var(--text-primary)] mb-1">Preserved Data:</div>
              <div className="text-[var(--text-secondary)]">
                {preservedData.conversations.length} conversation(s) saved
                {preservedData.draftMessage && ' • Draft message saved'}
              </div>
            </div>
          )}

          <div className="flex gap-3">
            <button
              onClick={handleExtend}
              disabled={isExtending}
              className="flex-1 px-4 py-2 bg-[var(--primary)] hover:bg-[var(--primary-hover)] text-white rounded-lg transition-colors disabled:opacity-50"
            >
              {isExtending ? 'Restoring...' : 'Restore Session'}
            </button>
            <button
              onClick={async () => {
                await onLogout()
              }}
              className="px-4 py-2 border border-[var(--border-primary)] hover:bg-[var(--surface-elevated)] rounded-lg transition-colors"
            >
              Log Out
            </button>
          </div>
        </div>
      </div>
    )
  }

  if (!timeoutWarningShown) return null

  return (
    <div className="fixed bottom-4 right-4 z-[10000]">
      <div
        className="bg-[var(--bg-primary)] border border-[var(--warning)] rounded-lg shadow-lg p-4 w-80"
        role="alertdialog"
        aria-labelledby="timeout-warning-title"
      >
        <div className="flex items-start gap-3">
          <svg className="w-5 h-5 text-[var(--warning)] mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <div className="flex-1">
            <h3 id="timeout-warning-title" className="font-medium text-[var(--text-primary)] mb-1">
              Session Expiring Soon
            </h3>
            <p className="text-sm text-[var(--text-secondary)] mb-2">
              Your session will expire in {formatTime(timeRemaining)}.
              Click below to extend your session and preserve your data.
            </p>
            <div className="flex gap-2">
              <button
                onClick={handleExtend}
                disabled={isExtending}
                className="flex-1 px-3 py-1.5 bg-[var(--warning)] hover:bg-[var(--warning)]/90 text-white text-sm rounded transition-colors disabled:opacity-50"
              >
                {isExtending ? 'Extending...' : 'Extend Session'}
              </button>
              <button
                onClick={async () => {
                  await onLogout()
                }}
                className="px-3 py-1.5 border border-[var(--border-primary)] hover:bg-[var(--surface-elevated)] text-sm rounded transition-colors"
              >
                Log Out
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
