import { useState, useEffect } from 'react'
import { api } from '../services/api'

interface CacheStats {
  cache_hits: number
  cache_misses: number
  hit_rate: number
  tokens_saved: number
  cost_saved: number
}

interface CacheIndicatorProps {
  conversationId?: string
}

export function CacheIndicator({ conversationId }: CacheIndicatorProps) {
  const [stats, setStats] = useState<CacheStats | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const loadStats = async () => {
    setLoading(true)
    setError(null)
    try {
      if (conversationId) {
        // Load conversation-specific stats
        const data = await api.getConversationUsage(conversationId)
        setStats({
          cache_hits: data.cache_hits || 0,
          cache_misses: data.cache_misses || 0,
          hit_rate: data.hit_rate || 0,
          tokens_saved: data.tokens_saved || 0,
          cost_saved: data.cost_saved || 0,
        })
      } else {
        // Load global cache stats
        const data = await api.getCacheStats()
        setStats(data)
      }
    } catch (err) {
      console.error('Failed to load cache stats:', err)
      setError('Failed to load cache statistics')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadStats()
    // Refresh stats periodically
    const interval = setInterval(loadStats, 30000) // Refresh every 30 seconds
    return () => clearInterval(interval)
  }, [conversationId])

  if (loading) {
    return (
      <div className="bg-[var(--bg-secondary)] border border-[var(--border-primary)] rounded-lg p-4">
        <div className="flex items-center gap-3">
          <div className="w-4 h-4 border-2 border-[var(--primary)] border-t-transparent rounded-full animate-spin"></div>
          <span className="text-sm text-[var(--text-secondary)]">Loading cache statistics...</span>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-[var(--bg-secondary)] border border-[var(--border-primary)] rounded-lg p-4">
        <div className="flex items-center gap-3">
          <div className="w-4 h-4 bg-red-500 rounded-full"></div>
          <span className="text-sm text-[var(--text-secondary)]">{error}</span>
        </div>
      </div>
    )
  }

  if (!stats) {
    return null
  }

  const totalRequests = stats.cache_hits + stats.cache_misses
  const hitPercentage = totalRequests > 0 ? (stats.cache_hits / totalRequests) * 100 : 0

  return (
    <div className="bg-[var(--bg-secondary)] border border-[var(--border-primary)] rounded-lg p-4 space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-[var(--text-primary)]">Prompt Cache Statistics</h3>
        <button
          onClick={loadStats}
          className="text-xs text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors"
        >
          Refresh
        </button>
      </div>

      <div className="grid grid-cols-2 gap-4 text-sm">
        <div>
          <span className="text-xs text-[var(--text-secondary)]">Cache Hits</span>
          <div className="font-medium text-[var(--text-primary)]">{stats.cache_hits.toLocaleString()}</div>
        </div>
        <div>
          <span className="text-xs text-[var(--text-secondary)]">Cache Misses</span>
          <div className="font-medium text-[var(--text-primary)]">{stats.cache_misses.toLocaleString()}</div>
        </div>
      </div>

      <div>
        <div className="flex justify-between text-xs text-[var(--text-secondary)] mb-1">
          <span>Hit Rate</span>
          <span>{hitPercentage.toFixed(1)}%</span>
        </div>
        <div className="w-full bg-[var(--bg-primary)] rounded-full h-2">
          <div
            className="h-2 bg-[var(--primary)] rounded-full transition-all duration-300"
            style={{ width: `${Math.min(hitPercentage, 100)}%` }}
          ></div>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 text-sm">
        <div>
          <span className="text-xs text-[var(--text-secondary)]">Tokens Saved</span>
          <div className="font-medium text-[var(--text-primary)]">{stats.tokens_saved.toLocaleString()}</div>
        </div>
        <div>
          <span className="text-xs text-[var(--text-secondary)]">Cost Savings</span>
          <div className="font-medium text-[var(--text-primary)]">
            ${stats.cost_saved.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
        </div>
      </div>

      <div className="text-xs text-[var(--text-secondary)]">
        Cache helps reduce API costs by reusing prompt embeddings for similar requests.
      </div>
    </div>
  )
}