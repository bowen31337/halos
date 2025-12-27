import { useState, useEffect } from 'react'
import { api } from '../services/api'

export function UsageDashboard() {
  const [dailyStats, setDailyStats] = useState<any>(null)
  const [monthlyStats, setMonthlyStats] = useState<any>(null)
  const [byModelStats, setByModelStats] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<'daily' | 'monthly' | 'models'>('daily')

  useEffect(() => {
    loadUsageData()
  }, [])

  const loadUsageData = async () => {
    try {
      setLoading(true)
      const [daily, monthly, byModel] = await Promise.all([
        api.getDailyUsage(),
        api.getMonthlyUsage(),
        api.getUsageByModel(),
      ])

      setDailyStats(daily)
      setMonthlyStats(monthly)
      setByModelStats(byModel)
    } catch (error) {
      console.error('Failed to load usage data:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="fixed bottom-20 right-4 bg-[var(--bg-primary)] border border-[var(--border-primary)] rounded-lg p-4 shadow-lg z-50 w-80">
        <div className="animate-pulse space-y-3">
          <div className="h-4 bg-[var(--surface)] rounded w-3/4" />
          <div className="h-4 bg-[var(--surface)] rounded w-full" />
          <div className="h-4 bg-[var(--surface)] rounded w-1/2" />
        </div>
      </div>
    )
  }

  return (
    <div className="fixed bottom-20 right-4 bg-[var(--bg-primary)] border border-[var(--border-primary)] rounded-lg shadow-lg z-50 w-96 max-h-96 overflow-hidden">
      {/* Header */}
      <div className="p-4 border-b border-[var(--border-primary)]">
        <h3 className="text-lg font-semibold text-[var(--text-primary)]">Usage Dashboard</h3>
        <p className="text-xs text-[var(--text-secondary)] mt-1">Track your AI usage and costs</p>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-[var(--border-primary)]">
        {['daily', 'monthly', 'models'].map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab as any)}
            className={`flex-1 py-2 text-sm font-medium capitalize ${
              activeTab === tab
                ? 'text-[var(--primary)] border-b-2 border-[var(--primary)]'
                : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="p-4 max-h-64 overflow-y-auto">
        {activeTab === 'daily' && dailyStats && (
          <div className="space-y-3">
            <div className="grid grid-cols-2 gap-2 text-sm">
              <div className="bg-[var(--surface)] p-2 rounded">
                <div className="text-xs text-[var(--text-secondary)]">Total Tokens</div>
                <div className="font-bold text-[var(--text-primary)]">{dailyStats.total_tokens.toLocaleString()}</div>
              </div>
              <div className="bg-[var(--surface)] p-2 rounded">
                <div className="text-xs text-[var(--text-secondary)]">Conversations</div>
                <div className="font-bold text-[var(--text-primary)]">{dailyStats.conversations}</div>
              </div>
              <div className="bg-[var(--surface)] p-2 rounded">
                <div className="text-xs text-[var(--text-secondary)]">Messages</div>
                <div className="font-bold text-[var(--text-primary)]">{dailyStats.messages}</div>
              </div>
              <div className="bg-[var(--surface)] p-2 rounded">
                <div className="text-xs text-[var(--text-secondary)]">Cost</div>
                <div className="font-bold text-[var(--text-primary)]">${dailyStats.estimated_cost.toFixed(4)}</div>
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex justify-between text-xs text-[var(--text-secondary)]">
                <span>Input tokens:</span>
                <span className="text-[var(--text-primary)]">{dailyStats.input_tokens.toLocaleString()}</span>
              </div>
              <div className="flex justify-between text-xs text-[var(--text-secondary)]">
                <span>Output tokens:</span>
                <span className="text-[var(--text-primary)]">{dailyStats.output_tokens.toLocaleString()}</span>
              </div>
              <div className="flex justify-between text-xs text-[var(--text-secondary)]">
                <span>Cache saved:</span>
                <span className="text-[var(--text-primary)]">{dailyStats.cache_read_tokens.toLocaleString()}</span>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'monthly' && monthlyStats && (
          <div className="space-y-3">
            <div className="text-sm text-[var(--text-secondary)]">Month: {monthlyStats.month}</div>
            <div className="grid grid-cols-2 gap-2 text-sm">
              <div className="bg-[var(--surface)] p-2 rounded">
                <div className="text-xs text-[var(--text-secondary)]">Total Tokens</div>
                <div className="font-bold text-[var(--text-primary)]">{monthlyStats.total_tokens.toLocaleString()}</div>
              </div>
              <div className="bg-[var(--surface)] p-2 rounded">
                <div className="text-xs text-[var(--text-secondary)]">Conversations</div>
                <div className="font-bold text-[var(--text-primary)]">{monthlyStats.conversations}</div>
              </div>
              <div className="bg-[var(--surface)] p-2 rounded">
                <div className="text-xs text-[var(--text-secondary)]">Messages</div>
                <div className="font-bold text-[var(--text-primary)]">{monthlyStats.messages}</div>
              </div>
              <div className="bg-[var(--surface)] p-2 rounded">
                <div className="text-xs text-[var(--text-secondary)]">Cost</div>
                <div className="font-bold text-[var(--text-primary)]">${monthlyStats.estimated_cost.toFixed(4)}</div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'models' && byModelStats.length > 0 && (
          <div className="space-y-2">
            {byModelStats.map((model) => (
              <div key={model.model} className="bg-[var(--surface)] p-3 rounded">
                <div className="flex justify-between items-center">
                  <div>
                    <div className="font-medium text-[var(--text-primary)]">{model.model}</div>
                    <div className="text-xs text-[var(--text-secondary)]">{model.messages} messages</div>
                  </div>
                  <div className="text-right">
                    <div className="font-bold text-[var(--text-primary)]">${model.estimated_cost.toFixed(4)}</div>
                    <div className="text-xs text-[var(--text-secondary)]">{model.total_tokens.toLocaleString()} tokens</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}