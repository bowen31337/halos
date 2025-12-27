import { ReactNode, useState, useRef, useEffect } from 'react'

export type TooltipPosition = 'top' | 'bottom' | 'left' | 'right'
export type TooltipVariant = 'default' | 'primary' | 'success' | 'error'

interface TooltipProps {
  /**
   * The content to display in the tooltip
   */
  content: ReactNode
  /**
   * The element that triggers the tooltip
   */
  children: ReactNode
  /**
   * Position of the tooltip relative to the trigger
   * @default 'top'
   */
  position?: TooltipPosition
  /**
   * Visual style variant
   * @default 'default'
   */
  variant?: TooltipVariant
  /**
   * Delay before showing the tooltip (ms)
   * @default 200
   */
  delay?: number
  /**
   * Whether to show an arrow pointing to the trigger
   * @default true
   */
  showArrow?: boolean
  /**
   * Optional keyboard shortcut to display
   */
  shortcut?: string
}

/**
 * Tooltip component - shows contextual information on hover/focus
 *
 * Features:
 * - Consistent styling across the app
 * - Multiple positions (top, bottom, left, right)
 * - Multiple variants (default, primary, success, error)
 * - Keyboard shortcut hints
 * - Delayed appearance for better UX
 * - Accessible (works with keyboard focus)
 *
 * Usage:
 * ```tsx
 * <Tooltip content="Copy to clipboard" shortcut="Ctrl+C">
 *   <button>Copy</button>
 * </Tooltip>
 * ```
 */
export function Tooltip({
  content,
  children,
  position = 'top',
  variant = 'default',
  delay = 200,
  showArrow = true,
  shortcut,
}: TooltipProps) {
  const [isVisible, setIsVisible] = useState(false)
  const [isDelayed, setIsDelayed] = useState(false)
  const triggerRef = useRef<HTMLSpanElement>(null)
  const timeoutRef = useRef<NodeJS.Timeout | null>(null)

  const showTooltip = () => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current)
    }
    setIsVisible(true)
    timeoutRef.current = setTimeout(() => {
      setIsDelayed(true)
    }, delay)
  }

  const hideTooltip = () => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current)
      timeoutRef.current = null
    }
    setIsVisible(false)
    setIsDelayed(false)
  }

  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current)
      }
    }
  }, [])

  // Determine if tooltip should be visible
  const shouldShow = isVisible && isDelayed

  return (
    <span
      ref={triggerRef}
      className="tooltip-container"
      onMouseEnter={showTooltip}
      onMouseLeave={hideTooltip}
      onFocus={showTooltip}
      onBlur={hideTooltip}
    >
      {children}
      {shouldShow && (
        <div
          className={`tooltip ${position} ${variant === 'default' ? '' : variant}`}
          role="tooltip"
        >
          {content}
          {shortcut && <kbd>{shortcut}</kbd>}
          {!showArrow && <style>{`.tooltip::after { display: none; }`}</style>}
        </div>
      )}
    </span>
  )
}

/**
 * Convenience hook for creating tooltip props
 */
export function useTooltip() {
  const [isVisible, setIsVisible] = useState(false)

  return {
    tooltipProps: {
      onMouseEnter: () => setIsVisible(true),
      onMouseLeave: () => setIsVisible(false),
    },
    isVisible,
  }
}

/**
 * Icon button with built-in tooltip
 */
export function IconButtonWithTooltip({
  icon,
  tooltip,
  onClick,
  variant = 'default',
  shortcut,
}: {
  icon: ReactNode
  tooltip: string
  onClick?: () => void
  variant?: TooltipVariant
  shortcut?: string
}) {
  return (
    <Tooltip content={tooltip} variant={variant} shortcut={shortcut}>
      <button
        className="icon-button"
        onClick={onClick}
        aria-label={tooltip}
      >
        {icon}
      </button>
    </Tooltip>
  )
}
