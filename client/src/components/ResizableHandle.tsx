import { useState, useRef, useEffect, useCallback } from 'react'

interface ResizableHandleProps {
  onResize: (width: number) => void
  minWidth?: number
  maxWidth?: number
  direction?: 'left' | 'right'
  className?: string
}

export function ResizableHandle({
  onResize,
  minWidth = 200,
  maxWidth = 800,
  direction = 'right',
  className = ''
}: ResizableHandleProps) {
  const [isDragging, setIsDragging] = useState(false)
  const handleRef = useRef<HTMLDivElement>(null)
  const startXRef = useRef(0)
  const startWidthRef = useRef(0)

  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    e.preventDefault()
    setIsDragging(true)
    startXRef.current = e.clientX
    startWidthRef.current = handleRef.current?.parentElement?.offsetWidth || 0

    // Add temporary event listeners
    document.addEventListener('mousemove', handleMouseMove)
    document.addEventListener('mouseup', handleMouseUp)

    // Add cursor style to body
    document.body.style.cursor = direction === 'right' ? 'col-resize' : 'col-resize'
    document.body.style.userSelect = 'none'
  }, [direction])

  const handleMouseMove = useCallback((e: MouseEvent) => {
    if (!isDragging) return

    const deltaX = direction === 'right'
      ? e.clientX - startXRef.current
      : startXRef.current - e.clientX

    const newWidth = startWidthRef.current + deltaX

    // Constrain within min and max bounds
    const constrainedWidth = Math.max(minWidth, Math.min(maxWidth, newWidth))

    onResize(constrainedWidth)
  }, [isDragging, direction, minWidth, maxWidth, onResize])

  const handleMouseUp = useCallback(() => {
    setIsDragging(false)

    // Remove temporary event listeners
    document.removeEventListener('mousemove', handleMouseMove)
    document.removeEventListener('mouseup', handleMouseUp)

    // Reset body styles
    document.body.style.cursor = ''
    document.body.style.userSelect = ''
  }, [handleMouseMove])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      document.removeEventListener('mousemove', handleMouseMove)
      document.removeEventListener('mouseup', handleMouseUp)
      document.body.style.cursor = ''
      document.body.style.userSelect = ''
    }
  }, [handleMouseMove, handleMouseUp])

  return (
    <div
      ref={handleRef}
      className={`
        absolute top-0 bottom-0 w-1 bg-transparent hover:bg-[var(--primary)]
        transition-colors cursor-col-resize z-10 group
        ${isDragging ? 'bg-[var(--primary)]' : ''}
        ${direction === 'right' ? '-right-0.5' : '-left-0.5'}
        ${className}
      `}
      onMouseDown={handleMouseDown}
      role="separator"
      aria-orientation="vertical"
      aria-label="Resize handle"
      tabIndex={0}
      onKeyDown={(e) => {
        // Keyboard accessibility: arrow keys to resize
        if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') {
          e.preventDefault()
          const currentWidth = handleRef.current?.parentElement?.offsetWidth || 0
          const step = e.shiftKey ? 50 : 10 // Shift+arrow for larger steps
          const directionMultiplier = e.key === 'ArrowRight' ? 1 : -1
          const newWidth = currentWidth + (step * directionMultiplier)
          const constrainedWidth = Math.max(minWidth, Math.min(maxWidth, newWidth))
          onResize(constrainedWidth)
        }
      }}
    >
      {/* Visual indicator */}
      <div
        className={`
          absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2
          w-1 h-8 bg-[var(--primary)] rounded-full opacity-0 group-hover:opacity-100
          transition-opacity ${isDragging ? 'opacity-100' : ''}
        `}
      />
    </div>
  )
}
