import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface UIState {
  // Theme
  theme: 'light' | 'dark' | 'system'

  // Sidebar
  sidebarOpen: boolean
  sidebarWidth: number

  // Panel
  panelOpen: boolean
  panelType: 'artifacts' | 'files' | 'todos' | null

  // Model
  selectedModel: string

  // Extended thinking
  extendedThinkingEnabled: boolean

  // Font size
  fontSize: number

  // Custom instructions
  customInstructions: string

  // Model parameters
  temperature: number
  maxTokens: number

  // Actions
  setTheme: (theme: 'light' | 'dark' | 'system') => void
  toggleSidebar: () => void
  setSidebarOpen: (open: boolean) => void
  setSidebarWidth: (width: number) => void
  togglePanel: () => void
  setPanelOpen: (open: boolean) => void
  setPanelType: (type: 'artifacts' | 'files' | 'todos' | null) => void
  setSelectedModel: (model: string) => void
  toggleExtendedThinking: () => void
  setFontSize: (size: number) => void
  setCustomInstructions: (instructions: string) => void
  setTemperature: (temp: number) => void
  setMaxTokens: (tokens: number) => void
}

export const useUIStore = create<UIState>()(
  persist(
    (set) => ({
      // Initial state
      theme: 'light',
      sidebarOpen: true,
      sidebarWidth: 260,
      panelOpen: false,
      panelType: null,
      selectedModel: 'claude-sonnet-4-5-20250929',
      extendedThinkingEnabled: false,
      fontSize: 16,
      customInstructions: '',
      temperature: 0.7,
      maxTokens: 4096,

      // Actions
      setTheme: (theme) => {
        set({ theme })
        // Apply theme to document
        if (theme === 'dark') {
          document.documentElement.classList.add('dark')
        } else if (theme === 'light') {
          document.documentElement.classList.remove('dark')
        } else {
          // System preference
          const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
          document.documentElement.classList.toggle('dark', prefersDark)
        }
      },

      toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
      setSidebarOpen: (open) => set({ sidebarOpen: open }),
      setSidebarWidth: (width) => set({ sidebarWidth: width }),

      togglePanel: () => set((state) => ({ panelOpen: !state.panelOpen })),
      setPanelOpen: (open) => set({ panelOpen: open }),
      setPanelType: (type) => set({ panelType: type, panelOpen: type !== null }),

      setSelectedModel: (model) => set({ selectedModel: model }),
      toggleExtendedThinking: () =>
        set((state) => ({ extendedThinkingEnabled: !state.extendedThinkingEnabled })),

      setFontSize: (size) => {
        set({ fontSize: size })
        // Apply font size to document
        document.documentElement.style.setProperty('--base-font-size', `${size}px`)
      },

      setCustomInstructions: (instructions) => set({ customInstructions: instructions }),
      setTemperature: (temp) => set({ temperature: temp }),
      setMaxTokens: (tokens) => set({ maxTokens: tokens }),
    }),
    {
      name: 'claude-ui-settings',
      partialize: (state) => ({
        theme: state.theme,
        sidebarWidth: state.sidebarWidth,
        selectedModel: state.selectedModel,
        extendedThinkingEnabled: state.extendedThinkingEnabled,
        fontSize: state.fontSize,
        customInstructions: state.customInstructions,
        temperature: state.temperature,
        maxTokens: state.maxTokens,
      }),
    }
  )
)
