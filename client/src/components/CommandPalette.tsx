import { useState, useEffect, useCallback, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { useUIStore } from '../stores/uiStore'
import { useConversationStore } from '../stores/conversationStore'

interface Command {
  id: string
  label: string
  description?: string
  icon?: string
  category: string
  shortcut?: string
  action: () => void
}

export function CommandPalette() {
  const navigate = useNavigate()
  const [isOpen, setIsOpen] = useState(false)
  const [query, setQuery] = useState('')
  const [selectedIndex, setSelectedIndex] = useState(0)

  const { setTheme, toggleSidebar, togglePanel, setPanelType, setSelectedModel } = useUIStore()
  const { createConversation, conversations } = useConversationStore()

  // Define all available commands
  const commands = useMemo<Command[]>(() => [
    // Conversation Actions
    {
      id: 'new-chat',
      label: 'New Chat',
      description: 'Start a new conversation',
      icon: '💬',
      category: 'Conversation',
      shortcut: '⌘N',
      action: () => createConversation(),
    },
    {
      id: 'toggle-sidebar',
      label: 'Toggle Sidebar',
      description: 'Show or hide the conversation sidebar',
      icon: '◧',
      category: 'View',
      shortcut: '⌘B',
      action: () => toggleSidebar(),
    },
    {
      id: 'toggle-panel',
      label: 'Toggle Right Panel',
      description: 'Show or hide the artifacts/files panel',
      icon: '◨',
      category: 'View',
      shortcut: '⌘\\',
      action: () => togglePanel(),
    },

    // Panel Management
    {
      id: 'show-artifacts',
      label: 'Show Artifacts Panel',
      description: 'Display code artifacts and previews',
      icon: '📦',
      category: 'View',
      action: () => setPanelType('artifacts'),
    },
    {
      id: 'show-files',
      label: 'Show Files Panel',
      description: 'Display agent workspace files',
      icon: '📁',
      category: 'View',
      action: () => setPanelType('files'),
    },
    {
      id: 'show-todos',
      label: 'Show Todos Panel',
      description: 'Display task planning progress',
      icon: '📋',
      category: 'View',
      action: () => setPanelType('todos'),
    },
    {
      id: 'show-memory',
      label: 'Show Memory Panel',
      description: 'Display long-term memory',
      icon: '🧠',
      category: 'View',
      action: () => setPanelType('memory'),
    },

    // Theme Settings
    {
      id: 'theme-light',
      label: 'Switch to Light Theme',
      description: 'Use light color scheme',
      icon: '☀️',
      category: 'Settings',
      action: () => setTheme('light'),
    },
    {
      id: 'theme-dark',
      label: 'Switch to Dark Theme',
      description: 'Use dark color scheme',
      icon: '🌙',
      category: 'Settings',
      action: () => setTheme('dark'),
    },
    {
      id: 'theme-system',
      label: 'Use System Theme',
      description: 'Follow system preference',
      icon: '💻',
      category: 'Settings',
      action: () => setTheme('system'),
    },

    // Model Selection
    {
      id: 'model-sonnet',
      label: 'Use Claude Sonnet 4.5',
      description: 'Balanced performance and speed',
      icon: '⚡',
      category: 'Model',
      action: () => setSelectedModel('claude-sonnet-4-5-20250929'),
    },
    {
      id: 'model-haiku',
      label: 'Use Claude Haiku 4.5',
      description: 'Fast and efficient',
      icon: '🚀',
      category: 'Model',
      action: () => setSelectedModel('claude-haiku-4-5-20251001'),
    },
    {
      id: 'model-opus',
      label: 'Use Claude Opus 4.1',
      description: 'Most capable model',
      icon: '🧠',
      category: 'Model',
      action: () => setSelectedModel('claude-opus-4-1-20250805'),
    },

    // Navigation
    {
      id: 'go-home',
      label: 'Go to Home',
      description: 'Navigate to home page',
      icon: '🏠',
      category: 'Navigation',
      action: () => navigate('/'),
    },
    {
      id: 'go-settings',
      label: 'Open Settings',
      description: 'Configure application settings',
      icon: '⚙️',
      category: 'Settings',
      shortcut: '⌘,',
      action: () => navigate('/settings'),
    },
  ], [
    createConversation,
    toggleSidebar,
    togglePanel,
    setPanelType,
    setTheme,
    setSelectedModel,
    navigate,
  ])

  // Filter commands based on query
  const filteredCommands = useMemo(() => {
    if (!query) return commands

    const lowerQuery = query.toLowerCase()
    return commands.filter((cmd) => {
      const matchLabel = cmd.label.toLowerCase().includes(lowerQuery)
      const matchDesc = cmd.description?.toLowerCase().includes(lowerQuery)
      const matchCategory = cmd.category.toLowerCase().includes(lowerQuery)
      return matchLabel || matchDesc || matchCategory
    })
  }, [commands, query])

  // Group commands by category
  const groupedCommands = useMemo(() => {
    const groups: Record<string, Command[]> = {}
    filteredCommands.forEach((cmd) => {
      if (!groups[cmd.category]) {
        groups[cmd.category] = []
      }
      groups[cmd.category].push(cmd)
    })
    return groups
  }, [filteredCommands])

  // Keyboard shortcut to open palette (Cmd/Ctrl + K)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Cmd/Ctrl + K to open
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault()
        setIsOpen((prev) => !prev)
      }

      // Escape to close
      if (e.key === 'Escape' && isOpen) {
        setIsOpen(false)
        setQuery('')
        setSelectedIndex(0)
      }

      // Handle navigation within palette
      if (isOpen) {
        if (e.key === 'ArrowDown') {
          e.preventDefault()
          setSelectedIndex((prev) => Math.min(prev + 1, filteredCommands.length - 1))
        } else if (e.key === 'ArrowUp') {
          e.preventDefault()
          setSelectedIndex((prev) => Math.max(prev - 1, 0))
        } else if (e.key === 'Enter' && filteredCommands.length > 0) {
          e.preventDefault()
          filteredCommands[selectedIndex].action()
          setIsOpen(false)
          setQuery('')
          setSelectedIndex(0)
        }
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [isOpen, filteredCommands, selectedIndex])

  // Reset selected index when query changes
  useEffect(() => {
    setSelectedIndex(0)
  }, [query])

  // Don't render if not open
  if (!isOpen) {
    return null
  }

  // Get the actual command at the selected index (accounting for grouping)
  const allCommands = Object.values(groupedCommands).flat()
  const selectedCommand = allCommands[selectedIndex] || null

  return (
    <div className="fixed inset-0 z-[100] flex items-start justify-center pt-24">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/50 backdrop-blur-sm"
        onClick={() => setIsOpen(false)}
        aria-hidden="true"
      />

      {/* Palette */}
      <div className="relative w-full max-w-2xl mx-4 bg-[var(--bg-primary)] border border-[var(--border-primary)] rounded-lg shadow-2xl overflow-hidden">
        {/* Search Input */}
        <div className="flex items-center gap-3 px-4 py-3 border-b border-[var(--border-primary)]">
          <span className="text-2xl">🔍</span>
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Type a command or search..."
            className="flex-1 bg-transparent border-none outline-none text-[var(--text-primary)] placeholder:text-[var(--text-secondary)] text-lg"
            autoFocus
            aria-label="Search commands"
          />
          {query && (
            <button
              onClick={() => setQuery('')}
              className="text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors"
              aria-label="Clear search"
            >
              ✕
            </button>
          )}
          <kbd className="px-2 py-1 text-xs bg-[var(--surface)] text-[var(--text-secondary)] rounded border border-[var(--border-primary)]">
            ESC
          </kbd>
        </div>

        {/* Commands List */}
        <div className="max-h-96 overflow-y-auto">
          {filteredCommands.length === 0 ? (
            <div className="py-12 text-center text-[var(--text-secondary)]">
              <div className="text-4xl mb-3">🔍</div>
              <p className="text-lg font-medium">No commands found</p>
              <p className="text-sm mt-1">Try a different search term</p>
            </div>
          ) : (
            <div className="py-2">
              {Object.entries(groupedCommands).map(([category, cmds]) => (
                <div key={category}>
                  {/* Category Header */}
                  <div className="px-4 py-2 text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wide">
                    {category}
                  </div>

                  {/* Commands in this category */}
                  {cmds.map((cmd) => {
                    const isSelected = selectedCommand?.id === cmd.id
                    return (
                      <button
                        key={cmd.id}
                        onClick={() => {
                          cmd.action()
                          setIsOpen(false)
                          setQuery('')
                          setSelectedIndex(0)
                        }}
                        className={`w-full flex items-center gap-3 px-4 py-3 text-left transition-colors ${
                          isSelected
                            ? 'bg-[var(--primary)]/10 text-[var(--primary)]'
                            : 'hover:bg-[var(--surface)] text-[var(--text-primary)]'
                        }`}
                      >
                        {/* Icon */}
                        <span className="text-2xl w-8 text-center">{cmd.icon || '•'}</span>

                        {/* Label and Description */}
                        <div className="flex-1 min-w-0">
                          <div className="font-medium">{cmd.label}</div>
                          {cmd.description && (
                            <div className={`text-sm truncate ${isSelected ? 'text-[var(--primary)]/70' : 'text-[var(--text-secondary)]'}`}>
                              {cmd.description}
                            </div>
                          )}
                        </div>

                        {/* Shortcut */}
                        {cmd.shortcut && (
                          <kbd className="px-2 py-1 text-xs bg-[var(--surface)] text-[var(--text-secondary)] rounded border border-[var(--border-primary)] whitespace-nowrap">
                            {cmd.shortcut}
                          </kbd>
                        )}
                      </button>
                    )
                  })}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-4 py-2 border-t border-[var(--border-primary)] bg-[var(--surface)] flex items-center justify-between text-xs text-[var(--text-secondary)]">
          <div className="flex items-center gap-4">
            <span className="flex items-center gap-1">
              <kbd>↑↓</kbd> Navigate
            </span>
            <span className="flex items-center gap-1">
              <kbd>↵</kbd> Select
            </span>
            <span className="flex items-center gap-1">
              <kbd>ESC</kbd> Close
            </span>
          </div>
          <div>
            {filteredCommands.length} command{filteredCommands.length !== 1 ? 's' : ''}
          </div>
        </div>
      </div>
    </div>
  )
}
