import { useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useUIStore } from '../stores/uiStore'
import { useConversationStore } from '../stores/conversationStore'

interface KeyboardShortcut {
  key: string
  ctrlKey?: boolean
  metaKey?: boolean
  shiftKey?: boolean
  altKey?: boolean
  description: string
  action: (e: KeyboardEvent) => void
}

export function useKeyboardShortcuts() {
  const navigate = useNavigate()
  const {
    setTheme,
    toggleSidebar,
    togglePanel,
    setPanelType,
    setSelectedModel,
    toggleExtendedThinking,
    toggleMemoryEnabled,
    setPermissionMode,
  } = useUIStore()

  const { createConversation } = useConversationStore()

  // Define all keyboard shortcuts
  const shortcuts: KeyboardShortcut[] = [
    // Navigation
    {
      key: 'k',
      ctrlKey: true,
      metaKey: true,
      description: 'Open command palette',
      action: (e) => {
        // Handled by CommandPalette component
      },
    },
    {
      key: 'n',
      ctrlKey: true,
      metaKey: true,
      description: 'New conversation',
      action: () => createConversation(),
    },
    {
      key: 'b',
      ctrlKey: true,
      metaKey: true,
      description: 'Toggle sidebar',
      action: () => toggleSidebar(),
    },
    {
      key: '\\',
      ctrlKey: true,
      metaKey: true,
      description: 'Toggle right panel',
      action: () => togglePanel(),
    },
    {
      key: 't',
      ctrlKey: true,
      metaKey: true,
      description: 'Toggle todos panel',
      action: () => setPanelType('todos'),
    },

    // Theme
    {
      key: 'd',
      ctrlKey: true,
      metaKey: true,
      shiftKey: true,
      description: 'Toggle dark mode',
      action: () => {
        const { theme } = useUIStore.getState()
        setTheme(theme === 'dark' ? 'light' : 'dark')
      },
    },

    // Settings
    {
      key: ',',
      ctrlKey: true,
      metaKey: true,
      description: 'Open settings',
      action: () => navigate('/settings'),
    },

    // Model selection
    {
      key: '1',
      ctrlKey: true,
      metaKey: true,
      description: 'Select Sonnet model',
      action: () => setSelectedModel('claude-sonnet-4-5-20250929'),
    },
    {
      key: '2',
      ctrlKey: true,
      metaKey: true,
      description: 'Select Haiku model',
      action: () => setSelectedModel('claude-haiku-4-5-20251001'),
    },
    {
      key: '3',
      ctrlKey: true,
      metaKey: true,
      description: 'Select Opus model',
      action: () => setSelectedModel('claude-opus-4-1-20250805'),
    },

    // Feature toggles
    {
      key: 'e',
      ctrlKey: true,
      metaKey: true,
      description: 'Toggle extended thinking',
      action: () => toggleExtendedThinking(),
    },
    {
      key: 'm',
      ctrlKey: true,
      metaKey: true,
      description: 'Toggle memory',
      action: () => toggleMemoryEnabled(),
    },
    {
      key: 'p',
      ctrlKey: true,
      metaKey: true,
      description: 'Cycle permission mode',
      action: () => {
        const current = useUIStore.getState().permissionMode
        setPermissionMode(current === 'auto' ? 'manual' : 'auto')
      },
    },

    // Panel shortcuts
    {
      key: 'a',
      ctrlKey: true,
      metaKey: true,
      description: 'Show artifacts panel',
      action: () => setPanelType('artifacts'),
    },
    {
      key: 'f',
      ctrlKey: true,
      metaKey: true,
      description: 'Show files panel',
      action: () => setPanelType('files'),
    },
    {
      key: 'r',
      ctrlKey: true,
      metaKey: true,
      description: 'Show memory panel',
      action: () => setPanelType('memory'),
    },

    // Help
    {
      key: '/',
      ctrlKey: true,
      metaKey: true,
      description: 'Show keyboard shortcuts',
      action: () => {
        // Could open a modal with all shortcuts
        console.table(
          shortcuts.map((s) => ({
            shortcut: `${s.metaKey ? '⌘' : ''}${s.ctrlKey ? 'Ctrl+' : ''}${s.shiftKey ? 'Shift+' : ''}${s.altKey ? 'Alt+' : ''}${s.key}`,
            description: s.description,
          }))
        )
      },
    },
  ]

  // Handle keyboard events
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ignore if user is typing in an input
      const target = e.target as HTMLElement
      if (
        target.tagName === 'INPUT' ||
        target.tagName === 'TEXTAREA' ||
        target.contentEditable === 'true' ||
        target.getAttribute('contenteditable') === 'true'
      ) {
        return
      }

      // Find matching shortcut
      const matchingShortcut = shortcuts.find((shortcut) => {
        return (
          shortcut.key.toLowerCase() === e.key.toLowerCase() &&
          (shortcut.ctrlKey === undefined || shortcut.ctrlKey === e.ctrlKey) &&
          (shortcut.metaKey === undefined || shortcut.metaKey === e.metaKey) &&
          (shortcut.shiftKey === undefined || shortcut.shiftKey === e.shiftKey) &&
          (shortcut.altKey === undefined || shortcut.altKey === e.altKey)
        )
      })

      if (matchingShortcut) {
        e.preventDefault()
        matchingShortcut.action(e)
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [shortcuts])

  return shortcuts
}

// Hook to show available shortcuts
export function useKeyboardShortcutsHelp() {
  const shortcuts = useKeyboardShortcuts()

  const formatShortcut = (shortcut: KeyboardShortcut): string => {
    const parts = []
    if (shortcut.metaKey) parts.push('⌘')
    if (shortcut.ctrlKey) parts.push('Ctrl')
    if (shortcut.shiftKey) parts.push('Shift')
    if (shortcut.altKey) parts.push('Alt')
    parts.push(shortcut.key.toUpperCase())
    return parts.join('+')
  }

  return {
    shortcuts,
    formatShortcut,
  }
}
