import { useEffect, useState, useRef } from 'react'
import { api } from '../services/api'

export function PromptCacheIndicator() {
  const [cacheStats, setCacheStats] = useState({
    cache_hits: 0,
    cache_misses: 0,
    hit_rate: 0,
    tokens_saved: 0,
    cost_saved: 0,
  })
  const [isVisible, setIsVisible] = useState(false)
  const intervalRef = useRef<NodeJS.Timeout>()

  useEffect(() => {
    // Fetch initial stats
    fetchCacheStats()

    // Update stats every 30 seconds
    intervalRef.current = setInterval(fetchCacheStats, 30000)

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
      }
    }
  }, [])

  const fetchCacheStats = async () => {
    try {
      const stats = await api.getCacheStats()
      setCacheStats(stats)

      // Show indicator if there are cache hits
      if (stats.cache_hits > 0) {
        setIsVisible(true)
      }
    } catch (error) {
      console.error('Failed to fetch cache stats:', error)
    }
  }

  // Don't show if no cache activity
  if (!isVisible || (cacheStats.cache_hits === 0 && cacheStats.cache_misses === 0)) {
    return null
  }

  const hitRate = cacheStats.hit_rate * 100

  return (
    <div className="fixed bottom-4 right-4 bg-[var(--bg-primary)] border border-[var(--border-primary)] rounded-lg p-3 shadow-lg z-50">
      <div className="flex items-center gap-2">
        <div className="flex items-center gap-1">
          <span className="text-sm font-medium text-[var(--text-primary)]">Cache</span>
          <div className="w-2 h-2 bg-green-400 rounded-full loading-pulse" />
        </div>

        <div className="text-xs text-[var(--text-secondary)]">
          Hits: {cacheStats.cache_hits} | Misses: {cacheStats.cache_misses}
        </div>

        <div className="text-xs text-[var(--text-secondary)]">
          Hit Rate: {hitRate.toFixed(1)}%
        </div>

        <div className="text-xs text-[var(--text-secondary)]">
          Saved: {cacheStats.tokens_saved.toLocaleString()} tokens
        </div>

        <div className="text-xs text-[var(--text-secondary)]">
          Cost: ${cacheStats.cost_saved.toFixed(4)}
        </div>
      </div>

      {/* Progress bar */}
      <div className="mt-2 w-full bg-[var(--surface)] rounded-full h-2">
        <div
          className="bg-green-500 h-2 rounded-full transition-all duration-300"
          style={{ width: `${hitRate}%` }}
        />
      </div>
    </div>
  )
}