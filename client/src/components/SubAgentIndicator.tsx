import { useState, useEffect } from 'react'
import { useUIStore } from '../stores/uiStore'

interface SubAgentIndicatorProps {
  isVisible: boolean
  subAgentName?: string
  progress?: number
  isCompleted?: boolean
}

export function SubAgentIndicator({
  isVisible,
  subAgentName = "research-agent",
  progress = 0,
  isCompleted = false
}: SubAgentIndicatorProps) {
  const { extendedThinkingEnabled } = useUIStore()

  if (!isVisible && !extendedThinkingEnabled) {
    return null
  }

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
                {isVisible ? 'Task Delegated' : 'Extended Thinking'}
              </h4>
              {isVisible && (
                <span className="px-2 py-1 bg-[var(--surface-elevated)] text-xs rounded-full text-[var(--text-secondary)]">
                  {subAgentName}
                </span>
              )}
            </div>

            {isVisible ? (
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
            ) : (
              <p className="text-sm text-[var(--text-secondary)] mt-1">
                Extended thinking mode is active
              </p>
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