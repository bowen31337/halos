import { useEffect, useState, useRef } from 'react'
import { useOnboardingStore } from '../stores/onboardingStore'

interface TourStep {
  title: string
  description: string
  target: string // CSS selector for the element to highlight
  position: 'top' | 'bottom' | 'left' | 'right'
  highlight?: boolean
}

const TOUR_STEPS: TourStep[] = [
  {
    title: 'Welcome to Claude!',
    description: 'Let me show you around the key features to get you started.',
    target: 'body',
    position: 'bottom',
    highlight: false
  },
  {
    title: 'Sidebar',
    description: 'Access your conversation history and projects here. You can organize conversations into projects for better management.',
    target: '[data-tour="sidebar"]',
    position: 'right'
  },
  {
    title: 'Model Selection',
    description: 'Choose between different Claude models. Each has different capabilities and speed characteristics.',
    target: '[data-tour="model-selector"]',
    position: 'bottom'
  },
  {
    title: 'Extended Thinking',
    description: 'Enable extended thinking mode for complex problems that require deeper reasoning.',
    target: '[data-tour="thinking-toggle"]',
    position: 'bottom'
  },
  {
    title: 'Prompt Library',
    description: 'Save and reuse your favorite prompts. Access your saved prompts anytime from the header.',
    target: '[data-tour="prompt-library"]',
    position: 'bottom'
  },
  {
    title: 'MCP Servers',
    description: 'Connect to external tools and services using the Model Context Protocol. Add filesystem access, search APIs, and more.',
    target: '[data-tour="mcp-servers"]',
    position: 'bottom'
  },
  {
    title: 'Chat Input',
    description: 'Type your message here. You can also attach images or use voice input to speak your message.',
    target: '[data-tour="chat-input"]',
    position: 'top'
  },
  {
    title: 'You\'re Ready!',
    description: 'That\'s it! You can always access these features anytime. Enjoy using Claude!',
    target: 'body',
    position: 'bottom',
    highlight: false
  }
]

export function OnboardingTour() {
  const {
    isTourActive,
    currentStep,
    hasCompletedTour,
    shouldShowTour,
    nextStep,
    previousStep,
    completeTour,
    skipTour
  } = useOnboardingStore()

  const [elementPosition, setElementPosition] = useState<{
    top: number
    left: number
    width: number
    height: number
  } | null>(null)

  const tooltipRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    // Auto-start tour for new users
    if (!hasCompletedTour && shouldShowTour && !isTourActive) {
      // Small delay to let the app fully load
      const timer = setTimeout(() => {
        useOnboardingStore.getState().startTour()
      }, 1000)
      return () => clearTimeout(timer)
    }
  }, [hasCompletedTour, shouldShowTour, isTourActive])

  useEffect(() => {
    if (!isTourActive || currentStep >= TOUR_STEPS.length) return

    const step = TOUR_STEPS[currentStep]
    if (step.target === 'body') {
      setElementPosition(null)
      return
    }

    // Wait for DOM to be ready
    const updatePosition = () => {
      const element = document.querySelector(step.target)
      if (element) {
        const rect = element.getBoundingClientRect()
        setElementPosition({
          top: rect.top + window.scrollY,
          left: rect.left + window.scrollX,
          width: rect.width,
          height: rect.height
        })
      } else {
        // Retry after a short delay if element not found
        setTimeout(updatePosition, 100)
      }
    }

    updatePosition()
  }, [currentStep, isTourActive])

  if (!isTourActive || currentStep >= TOUR_STEPS.length) {
    return null
  }

  const step = TOUR_STEPS[currentStep]
  const isFirstStep = currentStep === 0
  const isLastStep = currentStep === TOUR_STEPS.length - 1

  // Calculate tooltip position
  const getTooltipStyle = () => {
    if (!elementPosition) {
      // Center of screen for intro/outro
      return {
        position: 'fixed' as const,
        top: '50%',
        left: '50%',
        transform: 'translate(-50%, -50%)',
        maxWidth: '500px'
      }
    }

    const spacing = 20
    let top = 0
    let left = 0

    switch (step.position) {
      case 'top':
        top = elementPosition.top - spacing
        left = elementPosition.left + elementPosition.width / 2
        break
      case 'bottom':
        top = elementPosition.top + elementPosition.height + spacing
        left = elementPosition.left + elementPosition.width / 2
        break
      case 'left':
        top = elementPosition.top + elementPosition.height / 2
        left = elementPosition.left - spacing
        break
      case 'right':
        top = elementPosition.top + elementPosition.height / 2
        left = elementPosition.left + elementPosition.width + spacing
        break
    }

    return {
      position: 'fixed' as const,
      top: `${top}px`,
      left: `${left}px`,
      transform: step.position === 'bottom' || step.position === 'top' ? 'translateX(-50%)' : 'translateY(-50%)',
      maxWidth: '400px'
    }
  }

  return (
    <>
      {/* Overlay */}
      <div className="fixed inset-0 z-[100] bg-black/60 backdrop-blur-sm transition-opacity" />

      {/* Highlight overlay for target element */}
      {elementPosition && (
        <div
          className="fixed z-[101] border-4 border-yellow-400 rounded-lg shadow-[0_0_0_9999px_rgba(0,0,0,0.6)] transition-all duration-300 pointer-events-none"
          style={{
            top: elementPosition.top - 4,
            left: elementPosition.left - 4,
            width: elementPosition.width + 8,
            height: elementPosition.height + 8
          }}
        />
      )}

      {/* Tooltip */}
      <div
        ref={tooltipRef}
        className="fixed z-[102] bg-[var(--bg-primary)] border border-[var(--border-primary)] rounded-xl shadow-2xl p-6 max-w-md"
        style={getTooltipStyle()}
      >
        {/* Progress indicator */}
        <div className="flex items-center gap-1 mb-3">
          {TOUR_STEPS.map((_, idx) => (
            <div
              key={idx}
              className={`h-1 flex-1 rounded-full transition-colors ${
                idx === currentStep ? 'bg-yellow-400' : idx < currentStep ? 'bg-[var(--primary)]' : 'bg-[var(--border-primary)]'
              }`}
            />
          ))}
        </div>

        {/* Content */}
        <h3 className="text-xl font-semibold text-[var(--text-primary)] mb-2">
          {step.title}
        </h3>
        <p className="text-[var(--text-secondary)] mb-4 leading-relaxed">
          {step.description}
        </p>

        {/* Actions */}
        <div className="flex items-center justify-between gap-2">
          <div className="flex gap-2">
            {!isFirstStep && (
              <button
                onClick={previousStep}
                className="px-4 py-2 rounded-lg bg-[var(--surface-elevated)] hover:bg-[var(--bg-primary)] text-[var(--text-primary)] transition-colors"
              >
                Back
              </button>
            )}
            <button
              onClick={skipTour}
              className="px-4 py-2 rounded-lg text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors"
            >
              Skip Tour
            </button>
          </div>

          <button
            onClick={() => {
              if (isLastStep) {
                completeTour()
              } else {
                nextStep()
              }
            }}
            className="px-6 py-2 rounded-lg bg-yellow-500 hover:bg-yellow-600 text-black font-medium transition-colors"
          >
            {isLastStep ? 'Finish' : 'Next'}
          </button>
        </div>
      </div>
    </>
  )
}
