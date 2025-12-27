import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface UIState {
  // Theme
  theme: 'light' | 'dark' | 'system'
  highContrast: boolean
  colorBlindMode: 'none' | 'deuteranopia' | 'protanopia' | 'tritanopia' | 'achromatopsia'

  // Sidebar
  sidebarOpen: boolean
  sidebarWidth: number

  // Panel
  panelOpen: boolean
  panelType: 'artifacts' | 'files' | 'todos' | 'diffs' | 'memory' | null
  panelWidth: number

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

  // Permission mode for HITL
  permissionMode: 'auto' | 'manual'

  // Memory enabled
  memoryEnabled: boolean

  // Actions
  setTheme: (theme: 'light' | 'dark' | 'system') => void
  setHighContrast: (enabled: boolean) => void
  toggleHighContrast: () => void
  setColorBlindMode: (mode: 'none' | 'deuteranopia' | 'protanopia' | 'tritanopia' | 'achromatopsia') => void
  toggleSidebar: () => void
  setSidebarOpen: (open: boolean) => void
  setSidebarWidth: (width: number) => void
  togglePanel: () => void
  setPanelOpen: (open: boolean) => void
  setPanelType: (type: 'artifacts' | 'files' | 'todos' | 'diffs' | 'memory' | null) => void
  setPanelWidth: (width: number) => void
  setSelectedModel: (model: string) => void
  toggleExtendedThinking: () => void
  setFontSize: (size: number) => void
  setCustomInstructions: (instructions: string) => void
  setTemperature: (temp: number) => void
  setMaxTokens: (tokens: number) => void
  setPermissionMode: (mode: 'auto' | 'manual') => void
  setMemoryEnabled: (enabled: boolean) => void
  toggleMemoryEnabled: () => void
}

export const useUIStore = create<UIState>()(
  persist(
    (set) => ({
      // Initial state
      theme: 'light',
      highContrast: false,
      colorBlindMode: 'none',
      sidebarOpen: true,
      sidebarWidth: 260,
      panelOpen: false,
      panelType: null,
      panelWidth: 450,
      selectedModel: 'claude-sonnet-4-5-20250929',
      extendedThinkingEnabled: false,
      fontSize: 16,
      customInstructions: '',
      temperature: 0.7,
      maxTokens: 4096,
      permissionMode: 'auto',
      memoryEnabled: true,

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

      setHighContrast: (enabled) => {
        set({ highContrast: enabled })
        // Apply high contrast class to document
        if (enabled) {
          document.documentElement.classList.add('high-contrast')
        } else {
          document.documentElement.classList.remove('high-contrast')
        }
      },

      toggleHighContrast: () => set((state) => {
        const newState = !state.highContrast
        // Apply to document
        if (newState) {
          document.documentElement.classList.add('high-contrast')
        } else {
          document.documentElement.classList.remove('high-contrast')
        }
        return { highContrast: newState }
      }),

      setColorBlindMode: (mode) => {
        set({ colorBlindMode: mode })
        // Remove all color blind classes first
        document.documentElement.classList.remove(
          'colorblind-deuteranopia',
          'colorblind-protanopia',
          'colorblind-tritanopia',
          'colorblind-achromatopsia'
        )
        // Apply the new class if not 'none'
        if (mode === 'deuteranopia') {
          document.documentElement.classList.add('colorblind-deuteranopia')
        } else if (mode === 'protanopia') {
          document.documentElement.classList.add('colorblind-protanopia')
        } else if (mode === 'tritanopia') {
          document.documentElement.classList.add('colorblind-tritanopia')
        } else if (mode === 'achromatopsia') {
          document.documentElement.classList.add('colorblind-achromatopsia')
        }
      },

      toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
      setSidebarOpen: (open) => set({ sidebarOpen: open }),
      setSidebarWidth: (width) => set({ sidebarWidth: width }),

      togglePanel: () => set((state) => ({ panelOpen: !state.panelOpen })),
      setPanelOpen: (open) => set({ panelOpen: open }),
      setPanelType: (type) => set({ panelType: type, panelOpen: type !== null }),
      setPanelWidth: (width) => set({ panelWidth: width }),

      setSelectedModel: (model) => set({ selectedModel: model }),
      toggleExtendedThinking: () =>
        set((state) => ({ extendedThinkingEnabled: !state.extendedThinkingEnabled })),

      setFontSize: (size) => {
        set({ fontSize: size })
        // Apply font size to document
        document.documentElement.style.setProperty('--base-font-size', `${size}px`)
      },

      setPermissionMode: (mode) => set({ permissionMode: mode }),
      setMemoryEnabled: (enabled) => set({ memoryEnabled: enabled }),
      toggleMemoryEnabled: () => set((state) => ({ memoryEnabled: !state.memoryEnabled })),

      setCustomInstructions: (instructions) => set({ customInstructions: instructions }),
      setTemperature: (temp) => set({ temperature: temp }),
      setMaxTokens: (tokens) => set({ maxTokens: tokens }),
    }),
    {
      name: 'claude-ui-settings',
      partialize: (state) => ({
        theme: state.theme,
        highContrast: state.highContrast,
        colorBlindMode: state.colorBlindMode,
        sidebarWidth: state.sidebarWidth,
        panelWidth: state.panelWidth,
        selectedModel: state.selectedModel,
        extendedThinkingEnabled: state.extendedThinkingEnabled,
        fontSize: state.fontSize,
        customInstructions: state.customInstructions,
        temperature: state.temperature,
        maxTokens: state.maxTokens,
        permissionMode: state.permissionMode,
        memoryEnabled: state.memoryEnabled,
      }),
    }
  )
)
