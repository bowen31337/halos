import { useState, useEffect } from 'react'
import { useUIStore } from '../stores/uiStore'
import { MemoryModal } from './MemoryModal'
import { api } from '../services/api'

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
    fontSize,
    setFontSize,
    customInstructions,
    setCustomInstructions,
    systemPromptOverride,
    setSystemPromptOverride,
    temperature,
    setTemperature,
    maxTokens,
    setMaxTokens,
    permissionMode,
    setPermissionMode,
    memoryEnabled,
    toggleMemoryEnabled,
  } = useUIStore()

  const [activeTab, setActiveTab] = useState<SettingsTab>('general')
  const [tempValue, setTempValue] = useState(temperature)
  const [tokensValue, setTokensValue] = useState(maxTokens)
  const [isSaving, setIsSaving] = useState(false)
  const [showMemoryModal, setShowMemoryModal] = useState(false)

  // Load settings from backend on mount
  useEffect(() => {
    const loadSettings = async () => {
      try {
        const settings = await api.getSettings()
        if (settings) {
          // Set local state based on API response
          if (settings.theme) setTheme(settings.theme)
          if (settings.font_size) setFontSize(settings.font_size)
          if (settings.custom_instructions) setCustomInstructions(settings.custom_instructions)
          if (settings.system_prompt_override) setSystemPromptOverride(settings.system_prompt_override)
          if (settings.temperature !== undefined) setTempValue(settings.temperature)
          if (settings.max_tokens !== undefined) setTokensValue(settings.max_tokens)
          if (settings.extended_thinking_enabled !== undefined && settings.extended_thinking_enabled !== extendedThinkingEnabled) {
            toggleExtendedThinking()
          }
          if (settings.memory_enabled !== undefined && settings.memory_enabled !== memoryEnabled) {
            toggleMemoryEnabled()
          }
        }
      } catch (error) {
        console.error('Failed to load settings:', error)
      }
    }

    loadSettings()
  }, [setTheme, setFontSize, setCustomInstructions, setSystemPromptOverride, setTemperature, setMaxTokens, toggleExtendedThinking, extendedThinkingEnabled, memoryEnabled, toggleMemoryEnabled])

  const saveSettings = async (updates: any) => {
    try {
      setIsSaving(true)
      await api.updateSettings(updates)
      setIsSaving(false)
    } catch (error) {
      console.error('Failed to save settings:', error)
      setIsSaving(false)
    }
  }

  // General Tab
  const renderGeneralTab = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-3">Models</h3>
        <div className="space-y-2">
          {(['claude-haiku-4-5-20251001', 'claude-sonnet-4-5-20250929', 'claude-opus-4-1-20250805'] as const).map((model) => (
            <button
              key={model}
              onClick={async () => {
                await saveSettings({ model })
              }}
              className={`w-full flex items-center justify-between px-4 py-3 rounded-lg border transition-colors ${
                model === 'claude-sonnet-4-5-20250929'
                  ? 'border-[var(--primary)] bg-[var(--surface-elevated)]'
                  : 'border-[var(--border-primary)] hover:bg-[var(--surface-elevated)]'
              }`}
            >
              <div>
                <div className="font-medium text-[var(--text-primary)] capitalize">
                  {model.replace('claude-', '').replace('-', ' ')}
                </div>
                <div className="text-xs text-[var(--text-secondary)]">
                  {model === 'claude-haiku-4-5-20251001' && 'Fast, efficient'}
                  {model === 'claude-sonnet-4-5-20250929' && 'Balanced, default'}
                  {model === 'claude-opus-4-1-20250805' && 'Most capable'}
                </div>
              </div>
              {model === 'claude-sonnet-4-5-20250929' && (
                <svg className="w-5 h-5 text-[var(--primary)]" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
              )}
            </button>
          ))}
        </div>
      </div>

      <div>
        <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-3">Extended Thinking</h3>
        <div className="flex items-center justify-between">
          <span className="text-sm text-[var(--text-secondary)]">
            Enable extended thinking for complex problem solving
          </span>
          <button
            onClick={async () => {
              toggleExtendedThinking()
              await saveSettings({ extended_thinking_enabled: !extendedThinkingEnabled })
            }}
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
        <p className="text-xs text-[var(--text-secondary)] mt-2">
          Extended thinking mode allows the AI to think longer and use tools for complex tasks.
        </p>
      </div>

      <div>
        <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-3">Permission Mode</h3>
        <div className="space-y-2">
          {[
            { id: 'default', label: 'Default', description: 'Prompts for permission when first using each tool' },
            { id: 'acceptEdits', label: 'Accept Edits', description: 'Auto-accepts all file editing permissions' },
            { id: 'plan', label: 'Plan', description: 'Analyze only, no modifications' },
            { id: 'bypassPermissions', label: 'Bypass', description: 'Skips all permission prompts' },
          ].map((mode) => (
            <button
              key={mode.id}
              onClick={async () => {
                setPermissionMode(mode.id as any)
                await saveSettings({ permission_mode: mode.id })
              }}
              className={`w-full flex items-center justify-between px-4 py-3 rounded-lg border transition-colors ${
                permissionMode === mode.id
                  ? 'border-[var(--primary)] bg-[var(--surface-elevated)]'
                  : 'border-[var(--border-primary)] hover:bg-[var(--surface-elevated)]'
              }`}
            >
              <div>
                <div className="font-medium text-[var(--text-primary)]">{mode.label}</div>
                <div className="text-xs text-[var(--text-secondary)]">{mode.description}</div>
              </div>
              {permissionMode === mode.id && (
                <svg className="w-5 h-5 text-[var(--primary)]" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
              )}
            </button>
          ))}
        </div>
        <p className="text-xs text-[var(--text-secondary)] mt-2">
          Controls how the AI handles sensitive operations like file writes and code execution.
        </p>
      </div>

      <div>
        <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-3">Human-in-the-Loop</h3>
        <div className="space-y-2">
          <button
            onClick={async () => {
              setPermissionMode('default')
              await saveSettings({ permission_mode: 'default' })
            }}
            className={`w-full flex items-center justify-between px-4 py-3 rounded-lg border transition-colors ${
              permissionMode === 'default'
                ? 'border-[var(--primary)] bg-[var(--surface-elevated)]'
                : 'border-[var(--border-primary)] hover:bg-[var(--surface-elevated)]'
            }`}
          >
            <div>
              <div className="font-medium text-[var(--text-primary)]">Manual</div>
              <div className="text-xs text-[var(--text-secondary)]">
                Prompts for approval before sensitive operations
              </div>
            </div>
            {permissionMode === 'default' && (
              <svg className="w-5 h-5 text-[var(--primary)]" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
              </svg>
            )}
          </button>
        </div>
        <p className="text-xs text-[var(--text-secondary)] mt-2">
          Manual mode triggers Human-in-the-Loop approval dialogs for sensitive operations like file writes.
        </p>
      </div>

      <div>
        <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-3">Long-term Memory</h3>
        <div className="flex items-center justify-between">
          <span className="text-sm text-[var(--text-secondary)]">
            Enable AI to remember information across conversations
          </span>
          <button
            onClick={async () => {
              toggleMemoryEnabled()
              await saveSettings({ memory_enabled: !memoryEnabled })
            }}
            className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
              memoryEnabled ? 'bg-[var(--primary)]' : 'bg-[var(--border-primary)]'
            }`}
          >
            <span
              className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                memoryEnabled ? 'translate-x-6' : 'translate-x-1'
              }`}
            />
          </button>
        </div>
        <p className="text-xs text-[var(--text-secondary)] mt-2">
          When enabled, the AI can store and retrieve information about your preferences across all conversations.
        </p>
      </div>

      <div className="flex justify-end pt-6 border-t border-[var(--border-primary)]">
        <button
          onClick={() => setShowMemoryModal(true)}
          className="px-4 py-2 bg-[var(--primary)] text-white rounded-lg hover:opacity-90 transition-opacity"
        >
          Manage Memories
        </button>
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
              onClick={async () => {
                setTheme(t)
                await saveSettings({ theme: t })
              }}
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
            value={fontSize}
            className="flex-1 h-2 bg-[var(--border-primary)] rounded-lg appearance-none cursor-pointer"
            onChange={async (e) => {
              const size = parseInt(e.target.value)
              setFontSize(size)
              await saveSettings({ font_size: size })
            }}
          />
          <span className="text-sm text-[var(--text-secondary)]">{fontSize}px</span>
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
          value={customInstructions}
          onChange={(e) => setCustomInstructions(e.target.value)}
          onBlur={async (e) => {
            await api.updateCustomInstructions(e.target.value)
          }}
        />
        <p className="text-xs text-[var(--text-secondary)] mt-2">
          These instructions will affect how the AI responds to your messages.
        </p>
      </div>

      <div>
        <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-3">System Prompt Override</h3>
        <textarea
          placeholder="Override the AI's system prompt (leave empty to use default)..."
          className="w-full min-h-[120px] p-3 rounded-lg border border-[var(--border-primary)] bg-[var(--bg-primary)] text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--primary)]"
          value={systemPromptOverride}
          onChange={(e) => setSystemPromptOverride(e.target.value)}
          onBlur={async (e) => {
            await api.updateSystemPrompt(e.target.value)
          }}
        />
        <p className="text-xs text-[var(--text-secondary)] mt-2">
          This will completely replace the AI's default system prompt. Use with caution.
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
                value={tempValue}
                onChange={(e) => {
                  const val = parseFloat(e.target.value)
                  setTempValue(val)
                  setTemperature(val)
                }}
                onMouseUp={async () => {
                  await saveSettings({ temperature: tempValue })
                }}
                className="flex-1 h-2 bg-[var(--border-primary)] rounded-lg appearance-none cursor-pointer"
              />
              <span className="text-sm text-[var(--text-primary)] w-12 text-right">{tempValue.toFixed(1)}</span>
            </div>
            <p className="text-xs text-[var(--text-secondary)] mt-1">
              Lower (0.0) = more focused, Higher (1.0) = more creative
            </p>
          </div>

          <div>
            <label className="block text-sm text-[var(--text-secondary)] mb-2">Max Tokens</label>
            <div className="flex items-center gap-3">
              <input
                type="number"
                value={tokensValue}
                onChange={(e) => {
                  const val = parseInt(e.target.value) || 1
                  setTokensValue(val)
                  setMaxTokens(val)
                }}
                onBlur={async (e) => {
                  await saveSettings({ max_tokens: parseInt(e.target.value) || 1 })
                }}
                min="1"
                max="8192"
                className="flex-1 p-2 rounded-lg border border-[var(--border-primary)] bg-[var(--bg-primary)] text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--primary)]"
              />
              <span className="text-xs text-[var(--text-secondary)]">tokens</span>
            </div>
            <p className="text-xs text-[var(--text-secondary)] mt-1">
              Limits the maximum length of AI responses
            </p>
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
            { id: 'general', label: 'General' },
            { id: 'appearance', label: 'Appearance' },
            { id: 'advanced', label: 'Advanced' },
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

      {/* Memory Modal */}
      {showMemoryModal && (
        <MemoryModal onClose={() => setShowMemoryModal(false)} />
      )}
    </div>
  )

  function handleBackdropClick(e: React.MouseEvent) {
    if (e.target === e.currentTarget) {
      onClose()
    }
  }
}