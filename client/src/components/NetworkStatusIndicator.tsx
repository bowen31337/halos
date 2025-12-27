import { useEffect, useState } from 'react'
import { useNetworkStore } from '../stores/networkStore'

/**
 * NetworkStatusIndicator - Shows network connection status
 * Displays a banner when offline and shows reconnection attempts
 */
export function NetworkStatusIndicator() {
  const { isOnline, isOffline, retryCount, reconnectAttempts, processQueue, setOnline, resetReconnectAttempts, incrementReconnectAttempts, actionQueue } = useNetworkStore()
  const [showBanner, setShowBanner] = useState(false)
  const [isConnecting, setIsConnecting] = useState(false)
  const [queueCount, setQueueCount] = useState(0)

  // Load queue from localStorage on mount
  useEffect(() => {
    try {
      const savedQueue = localStorage.getItem('claude-offline-queue')
      if (savedQueue) {
        const parsed = JSON.parse(savedQueue)
        // Update store with saved queue
        useNetworkStore.setState({ actionQueue: parsed })
        setQueueCount(parsed.length)
      }
    } catch (e) {
      console.warn('Failed to load offline queue:', e)
    }
  }, [])

  // Update queue count when queue changes
  useEffect(() => {
    setQueueCount(actionQueue.length)
  }, [actionQueue])

  useEffect(() => {
    // Show banner when going offline
    if (isOffline) {
      setShowBanner(true)
    } else {
      // Hide banner after coming back online with a delay
      const timer = setTimeout(() => {
        setShowBanner(false)
        setIsConnecting(false)
      }, 3000)
      return () => clearTimeout(timer)
    }
  }, [isOnline, isOffline])

  const handleRetry = async () => {
    setIsConnecting(true)
    // Attempt to reconnect by checking health endpoint
    try {
      const response = await fetch('/api/health', { method: 'HEAD' })
      if (response.ok) {
        setOnline(true)
        resetReconnectAttempts()
        // Process queued actions when connection is restored
        await processQueue()
      } else {
        incrementReconnectAttempts()
      }
    } catch (e) {
      incrementReconnectAttempts()
    } finally {
      setIsConnecting(false)
    }
  }

  // Auto-process queue when coming back online
  useEffect(() => {
    if (isOnline && queueCount > 0) {
      // Small delay to ensure connection is stable
      const timer = setTimeout(() => {
        processQueue()
      }, 1000)
      return () => clearTimeout(timer)
    }
  }, [isOnline, queueCount, processQueue])

  if (!showBanner && isOnline && queueCount === 0) return null

  return (
    <div className="fixed top-0 left-0 right-0 z-[9999]">
      {isOffline ? (
        <div className="bg-[var(--status-error)] text-white p-3 flex items-center justify-between shadow-lg">
          <div className="flex items-center gap-3">
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
            <div>
              <div className="font-semibold">You are offline</div>
              <div className="text-sm opacity-90">
                Some features may be limited until connection is restored
                {reconnectAttempts > 0 && ` • Attempt ${reconnectAttempts}`}
                {queueCount > 0 && ` • ${queueCount} action${queueCount > 1 ? 's' : ''} queued`}
              </div>
            </div>
          </div>
          <button
            onClick={handleRetry}
            disabled={isConnecting}
            className="px-4 py-1.5 bg-white/20 hover:bg-white/30 rounded font-medium transition-colors disabled:opacity-50"
          >
            {isConnecting ? 'Connecting...' : 'Retry'}
          </button>
        </div>
      ) : (
        <div className="bg-[var(--status-success)] text-white p-2 text-center text-sm font-medium shadow-lg">
          Connection restored{queueCount > 0 ? ` - Processing ${queueCount} queued action${queueCount > 1 ? 's' : ''}` : ''}
        </div>
      )}
    </div>
  )
}

/**
 * NetworkStatusBadge - Small badge for header showing connection status
 */
export function NetworkStatusBadge() {
  const { isOnline, isOffline } = useNetworkStore()

  if (isOnline) return null

  return (
    <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-[var(--status-error)] text-white text-xs font-medium">
      <span className="relative flex h-2 w-2">
        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-white opacity-75"></span>
        <span className="relative inline-flex rounded-full h-2 w-2 bg-white"></span>
      </span>
      Offline
    </div>
  )
}
