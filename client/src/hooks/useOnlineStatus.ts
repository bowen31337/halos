import { useEffect } from 'react'
import { useNetworkStore } from '../stores/networkStore'

/**
 * Hook to monitor online/offline status
 * Listens to browser online and offline events
 */
export function useOnlineStatus() {
  const { setOnline, processQueue } = useNetworkStore()

  useEffect(() => {
    // Check initial status
    setOnline(navigator.onLine)

    // Handle online event
    const handleOnline = () => {
      console.log('Connection restored')
      setOnline(true)
      // Process queued actions when connection is restored
      setTimeout(() => {
        processQueue()
      }, 100)
    }

    // Handle offline event
    const handleOffline = () => {
      console.log('Connection lost')
      setOnline(false)
    }

    // Add event listeners
    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)

    // Cleanup
    return () => {
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
    }
  }, [setOnline, processQueue])
}
