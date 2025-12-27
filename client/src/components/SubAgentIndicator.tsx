import { useEffect, useState } from 'react'
import { useChatStore } from '../stores/chatStore'
import { useUIStore } from '../stores/uiStore'

export function SubAgentIndicator() {
  const { extendedThinkingEnabled } = useUIStore()
  const { subAgent } = useChatStore()
  const [showResult, setShowResult] = useState(false)

  const isVisible = subAgent.isDelegated || subAgent.status === 'working' || subAgent.status === 'completed'
  const subAgentName = subAgent.subAgentName || 'unknown'
  const progress = subAgent.progress || 0
  const isCompleted = subAgent.status === 'completed'

  // Show result briefly when completed
  useEffect(() => {
    if (isCompleted && subAgent.result) {
      setShowResult(true)
      const timer = setTimeout(() => {
        setShowResult(false)
      }, 5000)
      return () => clearTimeout(timer)
    }
  }, [isCompleted, subAgent.result])

  if (!isVisible && !extendedThinkingEnabled) {
    return null
  }

  // Show extended thinking indicator
  if (!isVisible && extendedThinkingEnabled) {
    return (
      <div className="fixed top-4 right-4 z-50 animate-in slide-in-from-right-2 duration-300">
        <div className="bg-[var(--bg-primary)] border border-[var(--border-primary)] rounded-lg shadow-lg p-4 min-w-64">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-[var(--primary)] rounded-full flex items-center justify-center animate-pulse">
              <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
            </div>
            <div>
              <h4 className="font-medium text-[var(--text-primary)]">Extended Thinking</h4>
              <p className="text-sm text-[var(--text-secondary)]">Analyzing your request...</p>
            </div>
          </div>
        </div>
      </div>
    )
  }

  // Show completed result briefly
  if (isCompleted && showResult && subAgent.result) {
    return (
      <div className="fixed top-4 right-4 z-50 animate-in slide-in-from-right-2 duration-300">
        <div className="bg-[var(--bg-primary)] border border-[var(--border-primary)] rounded-lg shadow-lg p-4 min-w-80 max-w-md">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center">
              <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <div>
              <h4 className="font-medium text-[var(--text-primary)]">Sub-agent Complete</h4>
              <p className="text-xs text-[var(--text-secondary)]">{subAgentName}</p>
            </div>
          </div>
          <div className="text-sm text-[var(--text-secondary)] bg-[var(--surface-elevated)] p-2 rounded">
            {subAgent.result}
          </div>
        </div>
      </div>
    )
  }

  // Show delegation in progress
  return (
    <div className="fixed top-4 right-4 z-50 animate-in slide-in-from-right-2 duration-300">
      <div className="bg-[var(--bg-primary)] border border-[var(--border-primary)] rounded-lg shadow-lg p-4 min-w-64">
        <div className="flex items-center gap-3">
          <div className="relative">
            <div className="w-8 h-8 bg-[var(--primary)] rounded-full flex items-center justify-center">
              <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
            </div>
            {isVisible && (
              <div className="absolute -bottom-1 -right-1 w-3 h-3 bg-green-500 rounded-full animate-pulse" />
            )}
          </div>

          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <h4 className="font-medium text-[var(--text-primary)] truncate">
                {isCompleted ? 'Task Complete' : 'Task Delegated'}
              </h4>
              {isVisible && (
                <span className="px-2 py-1 bg-[var(--surface-elevated)] text-xs rounded-full text-[var(--text-secondary)]">
                  {subAgentName}
                </span>
              )}
            </div>

            {isCompleted ? (
              <>
                <p className="text-sm text-[var(--text-secondary)] mt-1">
                  Sub-agent has completed the task
                </p>
                <div className="mt-2 w-full bg-[var(--surface-elevated)] rounded-full h-2">
                  <div className="bg-green-500 h-2 rounded-full transition-all duration-300 ease-out" style={{ width: '100%' }} />
                </div>
                <div className="flex justify-between text-xs text-[var(--text-secondary)] mt-1">
                  <span>Complete</span>
                  <span>100%</span>
                </div>
              </>
            ) : (
              <>
                <p className="text-sm text-[var(--text-secondary)] mt-1">
                  Sub-agent is working on your request
                </p>

                {/* Progress bar */}
                <div className="mt-2 w-full bg-[var(--surface-elevated)] rounded-full h-2">
                  <div
                    className="bg-[var(--primary)] h-2 rounded-full transition-all duration-300 ease-out"
                    style={{ width: `${progress}%` }}
                  />
                </div>

                <div className="flex justify-between text-xs text-[var(--text-secondary)] mt-1">
                  <span>Working...</span>
                  <span>{progress}% complete</span>
                </div>
              </>
            )}
          </div>

          <button
            className="p-1 hover:bg-[var(--surface-elevated)] rounded-full transition-colors"
            onClick={() => {
              // Could add functionality to cancel delegation or view progress
            }}
            title="View details"
          >
            <svg className="w-4 h-4 text-[var(--text-secondary)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  )
}