import { useState } from 'react'
import { useUIStore } from '../stores/uiStore'

type SettingsTab = 'general' | 'appearance' | 'advanced'

interface SettingsModalProps {
  onClose: () => void
}

export function SettingsModal({ onClose }: SettingsModalProps) {
  const {
    theme,
    setTheme,
    extendedThinkingEnabled,
    toggleExtendedThinking,
  } = useUIStore()

  const [activeTab, setActiveTab] = useState<SettingsTab>('general')

  // Close on backdrop click
  const handleBackdropClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (e.target === e.currentTarget) {
      onClose()
    }
  }

  // General Tab
  const renderGeneralTab = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-3">Extended Thinking</h3>
        <div className="flex items-center justify-between">
          <span className="text-sm text-[var(--text-secondary)]">
            Enable extended thinking mode for complex problems
          </span>
          <button
            onClick={toggleExtendedThinking}
            className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
              extendedThinkingEnabled ? 'bg-[var(--primary)]' : 'bg-[var(--border-primary)]'
            }`}
          >
            <span
              className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                extendedThinkingEnabled ? 'translate-x-6' : 'translate-x-1'
              }`}
            />
          </button>
        </div>
      </div>
    </div>
  )

  // Appearance Tab
  const renderAppearanceTab = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-3">Theme</h3>
        <div className="space-y-2">
          {(['light', 'dark', 'system'] as const).map((t) => (
            <button
              key={t}
              onClick={() => setTheme(t)}
              className={`w-full flex items-center justify-between px-4 py-3 rounded-lg border transition-colors ${
                theme === t
                  ? 'border-[var(--primary)] bg-[var(--surface-elevated)]'
                  : 'border-[var(--border-primary)] hover:bg-[var(--surface-elevated)]'
              }`}
            >
              <span className="capitalize text-[var(--text-primary)]">{t}</span>
              {theme === t && (
                <svg className="w-5 h-5 text-[var(--primary)]" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
              )}
            </button>
          ))}
        </div>
      </div>

      <div>
        <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-3">Font Size</h3>
        <div className="flex items-center gap-3">
          <span className="text-xs text-[var(--text-secondary)]">Small</span>
          <input
            type="range"
            min="12"
            max="20"
            defaultValue="16"
            className="flex-1 h-2 bg-[var(--border-primary)] rounded-lg appearance-none cursor-pointer"
            onChange={(e) => {
              const size = e.target.value
              document.documentElement.style.setProperty('--base-font-size', `${size}px`)
            }}
          />
          <span className="text-sm text-[var(--text-secondary)]">Large</span>
        </div>
      </div>
    </div>
  )

  // Advanced Tab
  const renderAdvancedTab = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-3">Custom Instructions</h3>
        <textarea
          placeholder="Enter custom instructions that will be sent with every message..."
          className="w-full min-h-[100px] p-3 rounded-lg border border-[var(--border-primary)] bg-[var(--bg-primary)] text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--primary)]"
          defaultValue=""
        />
        <p className="text-xs text-[var(--text-secondary)] mt-2">
          These instructions will affect how the AI responds to your messages.
        </p>
      </div>

      <div>
        <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-3">Model Parameters</h3>
        <div className="space-y-4">
          <div>
            <label className="block text-sm text-[var(--text-secondary)] mb-2">Temperature</label>
            <div className="flex items-center gap-3">
              <input
                type="range"
                min="0"
                max="1"
                step="0.1"
                defaultValue="0.7"
                className="flex-1 h-2 bg-[var(--border-primary)] rounded-lg appearance-none cursor-pointer"
              />
              <span className="text-sm text-[var(--text-primary)] w-8">0.7</span>
            </div>
          </div>

          <div>
            <label className="block text-sm text-[var(--text-secondary)] mb-2">Max Tokens</label>
            <input
              type="number"
              defaultValue="4096"
              min="1"
              max="8192"
              className="w-full p-2 rounded-lg border border-[var(--border-primary)] bg-[var(--bg-primary)] text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--primary)]"
            />
          </div>
        </div>
      </div>
    </div>
  )

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm"
      onClick={handleBackdropClick}
    >
      <div className="w-full max-w-2xl max-h-[80vh] overflow-y-auto bg-[var(--bg-primary)] border border-[var(--border-primary)] rounded-xl shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-[var(--border-primary)]">
          <h2 className="text-lg font-semibold text-[var(--text-primary)]">Settings</h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-[var(--surface-elevated)] rounded-lg transition-colors"
            title="Close"
          >
            <svg className="w-5 h-5 text-[var(--text-secondary)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-[var(--border-primary)]">
          {[
            { id: 'general' as SettingsTab, label: 'General' },
            { id: 'appearance' as SettingsTab, label: 'Appearance' },
            { id: 'advanced' as SettingsTab, label: 'Advanced' },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex-1 px-4 py-3 text-sm font-medium transition-colors ${
                activeTab === tab.id
                  ? 'text-[var(--primary)] border-b-2 border-[var(--primary)]'
                  : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--surface-elevated)]'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Content */}
        <div className="px-6 py-6">
          {activeTab === 'general' && renderGeneralTab()}
          {activeTab === 'appearance' && renderAppearanceTab()}
          {activeTab === 'advanced' && renderAdvancedTab()}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-[var(--border-primary)] flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-[var(--primary)] hover:bg-[var(--primary-hover)] text-white rounded-lg transition-colors"
          >
            Done
          </button>
        </div>
      </div>
    </div>
  )
}
