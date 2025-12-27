import { useState, useEffect } from 'react'

interface ThinkingIndicatorProps {
  /**
   * Show progress indicator with animated dots
   */
  showProgress?: boolean
  /**
   * Progress percentage (0-100) - if provided, shows a progress bar
   */
  progress?: number
  /**
   * Custom message to display
   */
  message?: string
  /**
   * Whether the thinking is complete
   */
  complete?: boolean
}

/**
 * ThinkingIndicator component with animated progress indicator
 *
 * Features:
 * - Animated pulsing dots showing active thinking
 * - Optional progress bar
 * - Smooth fade-in animation
 * - Clear completion state
 *
 * Usage:
 * ```tsx
 * // Basic thinking indicator
 * <ThinkingIndicator />
 *
 * // With progress
 * <ThinkingIndicator progress={45} />
 *
 * // Complete state
 * <ThinkingIndicator complete />
 * ```
 */
export function ThinkingIndicator({
  showProgress = true,
  progress,
  message = 'Thinking...',
  complete = false,
}: ThinkingIndicatorProps) {
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  if (complete) {
    return (
      <div className="thinking-block">
        <div className="thinking-complete">
          <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
          <span>Thinking complete</span>
        </div>
      </div>
    )
  }

  return (
    <div className="thinking-block" style={{ opacity: mounted ? 1 : 0, transition: 'opacity 0.3s ease-out' }}>
      {/* Progress bar if progress is provided */}
      {progress !== undefined && (
        <div
          className="thinking-progress"
          style={{
            width: `${Math.min(100, Math.max(0, progress))}%`,
            animation: 'none',
          }}
        />
      )}

      {/* Animated progress bar when no specific progress */}
      {progress === undefined && showProgress && (
        <div className="thinking-progress" />
      )}

      {/* Thinking indicator with dots */}
      <div className="thinking-indicator">
        {showProgress && (
          <div className="progress-dots">
            <span />
            <span />
            <span />
          </div>
        )}
        <span>{message}</span>
        {progress !== undefined && (
          <span style={{ marginLeft: 'auto', color: 'var(--text-muted)' }}>
            {progress}%
          </span>
        )}
      </div>

      {/* Thinking content placeholder */}
      <div className="thinking-content">
        <div style={{ opacity: 0.6 }}>
          Analyzing request and formulating response...
        </div>
      </div>
    </div>
  )
}

/**
 * EnhancedThinking component with simulated progress
 * Use this when you want to show incremental progress
 */
export function EnhancedThinkingIndicator({
  message = 'Thinking...',
}: Pick<ThinkingIndicatorProps, 'message'>) {
  const [progress, setProgress] = useState(0)
  const [complete, setComplete] = useState(false)

  useEffect(() => {
    // Simulate progress
    const interval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 100) {
          clearInterval(interval)
          setTimeout(() => setComplete(true), 500)
          return 100
        }
        // Increment by random amount between 5-15
        return Math.min(100, prev + Math.random() * 10 + 5)
      })
    }, 300)

    return () => clearInterval(interval)
  }, [])

  return <ThinkingIndicator progress={progress} complete={complete} message={message} />
}
