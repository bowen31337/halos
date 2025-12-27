import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface OnboardingState {
  // Whether the user has completed the onboarding tour
  hasCompletedTour: boolean
  // Whether the tour is currently active
  isTourActive: boolean
  // Current step in the tour
  currentStep: number
  // Whether to show the tour on next visit
  shouldShowTour: boolean

  // Actions
  startTour: () => void
  skipTour: () => void
  completeTour: () => void
  nextStep: () => void
  previousStep: () => void
  resetTour: () => void
}

export const useOnboardingStore = create<OnboardingState>()(
  persist(
    (set, get) => ({
      hasCompletedTour: false,
      isTourActive: false,
      currentStep: 0,
      shouldShowTour: true,

      startTour: () => {
        set({ isTourActive: true, currentStep: 0 })
      },

      skipTour: () => {
        set({ isTourActive: false, hasCompletedTour: true })
      },

      completeTour: () => {
        set({ isTourActive: false, hasCompletedTour: true, currentStep: 0 })
      },

      nextStep: () => {
        const { currentStep } = get()
        set({ currentStep: currentStep + 1 })
      },

      previousStep: () => {
        const { currentStep } = get()
        set({ currentStep: Math.max(0, currentStep - 1) })
      },

      resetTour: () => {
        set({
          hasCompletedTour: false,
          isTourActive: false,
          currentStep: 0,
          shouldShowTour: true
        })
      },
    }),
    {
      name: 'claude-onboarding',
      partialize: (state) => ({
        hasCompletedTour: state.hasCompletedTour,
        shouldShowTour: state.shouldShowTour,
      }),
    }
  )
)
