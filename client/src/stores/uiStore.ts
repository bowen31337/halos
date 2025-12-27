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

  // Model Comparison Mode
  comparisonMode: boolean
  comparisonModels: string[]  // Array of 2 model IDs for comparison

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

  // Content filtering
  contentFilterLevel: 'off' | 'low' | 'medium' | 'high'
  contentFilterCategories: string[]

  // Locale preference for timestamp formatting
  locale: string

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
  setContentFilterLevel: (level: 'off' | 'low' | 'medium' | 'high') => void
  setContentFilterCategories: (categories: string[]) => void
  setLocale: (locale: string) => void
  // Comparison mode actions
  setComparisonMode: (enabled: boolean) => void
  toggleComparisonMode: () => void
  setComparisonModels: (models: string[]) => void
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
      comparisonMode: false,
      comparisonModels: ['claude-sonnet-4-5-20250929', 'claude-opus-4-1-20250805'],
      extendedThinkingEnabled: false,
      fontSize: 16,
      customInstructions: '',
      temperature: 0.7,
      maxTokens: 4096,
      permissionMode: 'auto',
      memoryEnabled: true,
      contentFilterLevel: 'low',
      contentFilterCategories: ['violence', 'hate', 'sexual', 'self-harm', 'illegal'],
      locale: 'en-US',

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

      setLocale: (locale: string) => set({ locale }),

      setPermissionMode: (mode) => set({ permissionMode: mode }),
      setMemoryEnabled: (enabled) => set({ memoryEnabled: enabled }),
      toggleMemoryEnabled: () => set((state) => ({ memoryEnabled: !state.memoryEnabled })),

      setCustomInstructions: (instructions) => set({ customInstructions: instructions }),
      setTemperature: (temp) => set({ temperature: temp }),
      setMaxTokens: (tokens) => set({ maxTokens: tokens }),
      setContentFilterLevel: (level) => set({ contentFilterLevel: level }),
      setContentFilterCategories: (categories) => set({ contentFilterCategories: categories }),

      // Comparison mode actions
      setComparisonMode: (enabled) => set({ comparisonMode: enabled }),
      toggleComparisonMode: () => set((state) => ({ comparisonMode: !state.comparisonMode })),
      setComparisonModels: (models) => set({ comparisonModels: models }),
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
        comparisonMode: state.comparisonMode,
        comparisonModels: state.comparisonModels,
        extendedThinkingEnabled: state.extendedThinkingEnabled,
        fontSize: state.fontSize,
        locale: state.locale,
        customInstructions: state.customInstructions,
        temperature: state.temperature,
        maxTokens: state.maxTokens,
        permissionMode: state.permissionMode,
        memoryEnabled: state.memoryEnabled,
        contentFilterLevel: state.contentFilterLevel,
        contentFilterCategories: state.contentFilterCategories,
      }),
    }
  )
)
