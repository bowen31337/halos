import { useState, useEffect } from 'react'
import { useUIStore } from '../stores/uiStore'
import { MemoryModal } from './MemoryModal'
import { api } from '../services/api'
import { PWAStatusIndicator } from './PWAInstallPrompt'

type SettingsTab = 'general' | 'appearance' | 'privacy' | 'advanced' | 'api' | 'data'

interface SettingsModalProps {
  onClose: () => void
}

export function SettingsModal({ onClose }: SettingsModalProps) {
  const {
    theme,
    setTheme,
    highContrast,
    setHighContrast,
    colorBlindMode,
    setColorBlindMode,
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
    contentFilterLevel,
    setContentFilterLevel,
    contentFilterCategories,
    setContentFilterCategories,
  } = useUIStore()

  const [activeTab, setActiveTab] = useState<SettingsTab>('appearance')
  const [memoryModalOpen, setMemoryModalOpen] = useState(false)

  // Data & Account tab state
  const [exporting, setExporting] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [deleteConfirmText, setDeleteConfirmText] = useState('')

  // Save settings to backend
  const saveSettings = async (settings: any) => {
    try {
      await api.updateSettings(settings)
    } catch (error) {
      console.error('Failed to save settings:', error)
    }
  }

  // General Tab
  const renderGeneralTab = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-3">Model</h3>
        <p className="text-xs text-[var(--text-secondary)] mb-2">
          Select the AI model for your conversations
        </p>
        <div className="flex items-center gap-3">
          <select
            className="flex-1 p-2 rounded-lg border border-[var(--border-primary)] bg-[var(--bg-primary)] text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--primary)]"
            value={useUIStore.getState().selectedModel}
            onChange={(e) => {
              useUIStore.getState().setSelectedModel(e.target.value)
              saveSettings({ selected_model: e.target.value })
            }}
          >
            <option value="claude-sonnet-4-5-20250929">Claude Sonnet 4.5</option>
            <option value="claude-haiku-4-5-20251001">Claude Haiku 4.5</option>
            <option value="claude-opus-4-1-20250805">Claude Opus 4.1</option>
          </select>
        </div>
      </div>

      <div>
        <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-3">Extended Thinking</h3>
        <button
          onClick={() => {
            toggleExtendedThinking()
            saveSettings({ extended_thinking_enabled: !extendedThinkingEnabled })
          }}
          className={`w-full flex items-center justify-between px-4 py-3 rounded-lg border transition-colors ${
            extendedThinkingEnabled
              ? 'border-[var(--primary)] bg-[var(--surface-elevated)]'
              : 'border-[var(--border-primary)] hover:bg-[var(--surface-elevated)]'
          }`}
        >
          <div>
            <div className="font-medium text-[var(--text-primary)]">Extended Thinking Mode</div>
            <div className="text-xs text-[var(--text-secondary)]">Enable deeper reasoning for complex tasks</div>
          </div>
          <div className={`w-11 h-6 rounded-full transition-colors ${
            extendedThinkingEnabled ? 'bg-[var(--primary)]' : 'bg-[var(--border-primary)]'
          }`}>
            <div className={`w-5 h-5 bg-white rounded-full transition-transform ${
              extendedThinkingEnabled ? 'translate-x-6 mt-0.5' : 'translate-x-1 mt-0.5'
            }`} />
          </div>
        </button>
      </div>

      <div>
        <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-3">Permission Mode</h3>
        <div className="space-y-2">
          {(['auto', 'manual'] as const).map((mode) => (
            <button
              key={mode}
              onClick={() => {
                setPermissionMode(mode)
                saveSettings({ permission_mode: mode })
              }}
              className={`w-full flex items-center justify-between px-4 py-3 rounded-lg border transition-colors ${
                permissionMode === mode
                  ? 'border-[var(--primary)] bg-[var(--surface-elevated)]'
                  : 'border-[var(--border-primary)] hover:bg-[var(--surface-elevated)]'
              }`}
            >
              <div className="font-medium text-[var(--text-primary)]">
                {mode === 'auto' ? 'Auto Approval' : 'Manual Approval'}
              </div>
              {permissionMode === mode && (
                <svg className="w-5 h-5 text-[var(--primary)]" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
              )}
            </button>
          ))}
        </div>
      </div>

      <div>
        <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-3">Memory</h3>
        <div className="flex items-center justify-between px-4 py-3 rounded-lg border border-[var(--border-primary)]">
          <div>
            <div className="font-medium text-[var(--text-primary)]">Enable Memory</div>
            <div className="text-xs text-[var(--text-secondary)]">Allow AI to remember information across conversations</div>
          </div>
          <button
            onClick={() => {
              toggleMemoryEnabled()
              saveSettings({ memory_enabled: !memoryEnabled })
            }}
            className={`w-11 h-6 rounded-full transition-colors ${
              memoryEnabled ? 'bg-[var(--primary)]' : 'bg-[var(--border-primary)]'
            }`}
          >
            <div className={`w-5 h-5 bg-white rounded-full transition-transform ${
              memoryEnabled ? 'translate-x-6 mt-0.5' : 'translate-x-1 mt-0.5'
            }`} />
          </button>
        </div>
        <button
          onClick={() => setMemoryModalOpen(true)}
          className="mt-2 w-full px-4 py-2 bg-[var(--surface-elevated)] hover:bg-[var(--bg-primary)] rounded-lg text-sm text-[var(--text-primary)] transition-colors"
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
              onClick={() => {
                setTheme(t)
                saveSettings({ theme: t })
              }}
              className={`w-full flex items-center justify-between px-4 py-3 rounded-lg border transition-colors ${
                theme === t
                  ? 'border-[var(--primary)] bg-[var(--surface-elevated)]'
                  : 'border-[var(--border-primary)] hover:bg-[var(--surface-elevated)]'
              }`}
            >
              <div className="font-medium text-[var(--text-primary)]">
                {t.charAt(0).toUpperCase() + t.slice(1)}
              </div>
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
        <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-3">High Contrast Mode</h3>
        <button
          onClick={() => {
            setHighContrast(!highContrast)
            saveSettings({ high_contrast: !highContrast })
          }}
          className={`w-full flex items-center justify-between px-4 py-3 rounded-lg border transition-colors ${
            highContrast
              ? 'border-[var(--primary)] bg-[var(--surface-elevated)]'
              : 'border-[var(--border-primary)] hover:bg-[var(--surface-elevated)]'
          }`}
        >
          <div>
            <div className="font-medium text-[var(--text-primary)]">High Contrast Mode</div>
            <div className="text-xs text-[var(--text-secondary)]">Enhanced visibility for better readability</div>
          </div>
          <div className={`w-11 h-6 rounded-full transition-colors ${
            highContrast ? 'bg-[var(--primary)]' : 'bg-[var(--border-primary)]'
          }`}>
            <div className={`w-5 h-5 bg-white rounded-full transition-transform ${
              highContrast ? 'translate-x-6 mt-0.5' : 'translate-x-1 mt-0.5'
            }`} />
          </div>
        </button>
      </div>

      <div>
        <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-3">Color Blind Mode</h3>
        <p className="text-xs text-[var(--text-secondary)] mb-3">
          Select a color vision deficiency mode to adjust the UI for better distinguishability
        </p>
        <div className="space-y-2">
          {([
            { id: 'none', label: 'None', description: 'Standard color palette' },
            { id: 'deuteranopia', label: 'Deuteranopia', description: 'Green-blind (most common)' },
            { id: 'protanopia', label: 'Protanopia', description: 'Red-blind' },
            { id: 'tritanopia', label: 'Tritanopia', description: 'Blue-blind (rare)' },
            { id: 'achromatopsia', label: 'Achromatopsia', description: 'Complete color blindness (grayscale)' },
          ] as const).map((mode) => (
            <button
              key={mode.id}
              onClick={async () => {
                setColorBlindMode(mode.id)
                await saveSettings({ color_blind_mode: mode.id })
              }}
              className={`w-full flex items-center justify-between px-4 py-3 rounded-lg border transition-colors ${
                colorBlindMode === mode.id
                  ? 'border-[var(--primary)] bg-[var(--surface-elevated)]'
                  : 'border-[var(--border-primary)] hover:bg-[var(--surface-elevated)]'
              }`}
            >
              <div>
                <div className="font-medium text-[var(--text-primary)]">{mode.label}</div>
                <div className="text-xs text-[var(--text-secondary)]">{mode.description}</div>
              </div>
              {colorBlindMode === mode.id && (
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

      <div>
        <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-3">PWA Installation</h3>
        <PWAStatusIndicator />
        <p className="text-xs text-[var(--text-secondary)] mt-2">
          Install the app for offline access and native-like experience
        </p>
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
                max="2"
                step="0.1"
                value={temperature}
                className="flex-1 h-2 bg-[var(--border-primary)] rounded-lg appearance-none cursor-pointer"
                onChange={async (e) => {
                  const temp = parseFloat(e.target.value)
                  setTemperature(temp)
                  await saveSettings({ temperature: temp })
                }}
              />
              <span className="text-sm text-[var(--text-secondary)] w-12 text-right">{temperature}</span>
            </div>
            <p className="text-xs text-[var(--text-secondary)] mt-1">
              Higher values make responses more creative, lower values more focused
            </p>
          </div>

          <div>
            <label className="block text-sm text-[var(--text-secondary)] mb-2">Max Tokens</label>
            <div className="flex items-center gap-3">
              <input
                type="range"
                min="1024"
                max="8192"
                step="1024"
                value={maxTokens}
                className="flex-1 h-2 bg-[var(--border-primary)] rounded-lg appearance-none cursor-pointer"
                onChange={async (e) => {
                  const tokens = parseInt(e.target.value)
                  setMaxTokens(tokens)
                  await saveSettings({ max_tokens: tokens })
                }}
              />
              <span className="text-sm text-[var(--text-secondary)] w-16 text-right">{maxTokens}</span>
            </div>
            <p className="text-xs text-[var(--text-secondary)] mt-1">
              Maximum number of tokens to generate in responses
            </p>
          </div>
        </div>
      </div>
    </div>
  )

  // Privacy & Safety Tab
  const renderPrivacyTab = () => {
    const filterLevels = [
      { value: 'off' as const, label: 'Off', description: 'No content filtering' },
      { value: 'low' as const, label: 'Low', description: 'Basic filtering for explicit content' },
      { value: 'medium' as const, label: 'Medium', description: 'Standard filtering with additional safety measures' },
      { value: 'high' as const, label: 'High', description: 'Strict filtering for maximum safety' },
    ]

    const categories = [
      { id: 'violence', label: 'Violence & Gore', description: 'Violent content and graphic imagery' },
      { id: 'hate', label: 'Hate Speech', description: 'Discriminatory or hateful language' },
      { id: 'sexual', label: 'Sexual Content', description: 'Explicit sexual material' },
      { id: 'self-harm', label: 'Self-Harm', description: 'Content promoting self-harm or suicide' },
      { id: 'illegal', label: 'Illegal Activities', description: 'Content about illegal acts' },
    ]

    return (
      <div className="space-y-6">
        <div>
          <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-3">Content Filtering Level</h3>
          <p className="text-xs text-[var(--text-secondary)] mb-3">
            Choose the level of content filtering for AI responses
          </p>
          <div className="space-y-2">
            {filterLevels.map((level) => (
              <button
                key={level.value}
                onClick={() => {
                  setContentFilterLevel(level.value)
                  saveSettings({ content_filter_level: level.value })
                }}
                className={`w-full flex items-center justify-between px-4 py-3 rounded-lg border transition-colors ${
                  contentFilterLevel === level.value
                    ? 'border-[var(--primary)] bg-[var(--surface-elevated)]'
                    : 'border-[var(--border-primary)] hover:bg-[var(--surface-elevated)]'
                }`}
              >
                <div className="text-left">
                  <div className="font-medium text-[var(--text-primary)]">{level.label}</div>
                  <div className="text-xs text-[var(--text-secondary)]">{level.description}</div>
                </div>
                {contentFilterLevel === level.value && (
                  <svg className="w-5 h-5 text-[var(--primary)]" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                )}
              </button>
            ))}
          </div>
        </div>

        <div>
          <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-3">Filtered Categories</h3>
          <p className="text-xs text-[var(--text-secondary)] mb-3">
            Select which content categories should be filtered
          </p>
          <div className="space-y-2">
            {categories.map((category) => (
              <button
                key={category.id}
                onClick={() => {
                  const newCategories = contentFilterCategories.includes(category.id)
                    ? contentFilterCategories.filter((c) => c !== category.id)
                    : [...contentFilterCategories, category.id]
                  setContentFilterCategories(newCategories)
                  saveSettings({ content_filter_categories: newCategories })
                }}
                className={`w-full flex items-center justify-between px-4 py-3 rounded-lg border transition-colors ${
                  contentFilterCategories.includes(category.id)
                    ? 'border-[var(--primary)] bg-[var(--surface-elevated)]'
                    : 'border-[var(--border-primary)] hover:bg-[var(--surface-elevated)]'
                }`}
              >
                <div className="text-left">
                  <div className="font-medium text-[var(--text-primary)]">{category.label}</div>
                  <div className="text-xs text-[var(--text-secondary)]">{category.description}</div>
                </div>
                {contentFilterCategories.includes(category.id) && (
                  <svg className="w-5 h-5 text-[var(--primary)]" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                )}
              </button>
            ))}
          </div>
        </div>

        <div className="p-4 rounded-lg bg-[var(--surface-elevated)] border border-[var(--border-primary)]">
          <div className="flex items-start gap-3">
            <svg className="w-5 h-5 text-[var(--primary)] mt-0.5" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
            </svg>
            <div className="flex-1">
              <div className="text-sm font-medium text-[var(--text-primary)]">About Content Filtering</div>
              <div className="text-xs text-[var(--text-secondary)] mt-1">
                Content filtering helps prevent inappropriate responses. Higher levels may filter more content but could also limit legitimate responses. Your preferences are saved locally and synchronized with your account.
              </div>
            </div>
          </div>
        </div>
      </div>
    )
  }

  // Data & Account Tab
  const renderDataTab = () => {
    const handleExportAll = async () => {
      setExporting(true)
      try {
        const blob = await api.exportAllUserData()
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `user_data_export_${new Date().toISOString().split('T')[0]}.json`
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)
        URL.revokeObjectURL(url)
      } catch (error) {
        console.error('Export failed:', error)
        alert(`Export failed: ${error instanceof Error ? error.message : 'Unknown error'}`)
      } finally {
        setExporting(false)
      }
    }

    const handleDeleteAccount = async () => {
      if (deleteConfirmText !== 'DELETE_ACCOUNT') {
        alert('Please type DELETE_ACCOUNT exactly to confirm account deletion.')
        return
      }

      if (!confirm('WARNING: This will permanently delete ALL your data including conversations, messages, memories, prompts, artifacts, and projects. This action CANNOT be undone!\n\nAre you absolutely sure you want to delete your account?')) {
        return
      }

      setDeleting(true)
      try {
        const result = await api.deleteAccount('DELETE_ACCOUNT')
        alert(`Account deleted successfully.\n\nDeleted items:\n${Object.entries(result.deleted_items).map(([k, v]) => `  - ${k}: ${v}`).join('\n')}\n\nTotal: ${result.total_deleted} items`)
        // Redirect to home page
        window.location.href = '/'
      } catch (error) {
        console.error('Account deletion failed:', error)
        alert(`Deletion failed: ${error instanceof Error ? error.message : 'Unknown error'}`)
      } finally {
        setDeleting(false)
      }
    }

    return (
      <div className="space-y-6">
        {/* Data Export Section */}
        <div>
          <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-3">Data Export</h3>
          <p className="text-xs text-[var(--text-secondary)] mb-3">
            Export all your data including conversations, messages, memories, prompts, artifacts, and settings.
            This is useful for backups or data portability.
          </p>
          <button
            onClick={handleExportAll}
            disabled={exporting}
            className="w-full px-4 py-2 bg-[var(--primary)] hover:bg-[var(--primary-hover)] text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {exporting ? 'Exporting...' : 'Export All Data (JSON)'}
          </button>
        </div>

        {/* Account Deletion Section */}
        <div className="pt-6 border-t border-[var(--border-primary)]">
          <h3 className="text-sm font-semibold text-[var(--text-danger)] mb-3">Danger Zone</h3>
          <p className="text-xs text-[var(--text-secondary)] mb-3">
            Delete your account and all associated data. This action is permanent and cannot be undone.
          </p>

          <div className="space-y-3">
            <div className="p-3 rounded-lg bg-[var(--surface-elevated)] border border-[var(--border-primary)]">
              <label className="block text-xs text-[var(--text-secondary)] mb-2">
                Type <code className="bg-[var(--bg-primary)] px-1 py-0.5 rounded text-[var(--text-primary)]">DELETE_ACCOUNT</code> to confirm
              </label>
              <input
                type="text"
                value={deleteConfirmText}
                onChange={(e) => setDeleteConfirmText(e.target.value)}
                placeholder="DELETE_ACCOUNT"
                className="w-full px-3 py-2 rounded border border-[var(--border-primary)] bg-[var(--bg-primary)] text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--danger)]"
              />
            </div>

            <button
              onClick={handleDeleteAccount}
              disabled={deleting || deleteConfirmText !== 'DELETE_ACCOUNT'}
              className="w-full px-4 py-2 bg-[var(--danger)] hover:bg-[var(--danger-hover)] text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {deleting ? 'Deleting...' : 'Delete Account Permanently'}
            </button>
          </div>
        </div>

        {/* Info Box */}
        <div className="p-4 rounded-lg bg-[var(--surface-elevated)] border border-[var(--border-primary)]">
          <div className="flex items-start gap-3">
            <svg className="w-5 h-5 text-[var(--text-secondary)] mt-0.5" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
            </svg>
            <div className="flex-1 text-xs text-[var(--text-secondary)]">
              <strong className="text-[var(--text-primary)]">About Data Export & Account Deletion</strong>
              <ul className="mt-2 space-y-1 list-disc list-inside">
                <li>Exports include all conversations, messages, memories, prompts, artifacts, checkpoints, and projects</li>
                <li>Account deletion is permanent and removes all data from our servers</li>
                <li>Conversations are soft-deleted (can be recovered by admins if needed)</li>
                <li>All other data is permanently deleted</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    )
  }

  // API Tab
  const renderAPITab = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-3">API Configuration</h3>
        <p className="text-xs text-[var(--text-secondary)] mb-3">
          Configure your API settings for external integrations
        </p>
        <button
          onClick={() => {
            // Navigate to API key management
            window.location.href = '/settings/api-key'
          }}
          className="w-full px-4 py-2 bg-[var(--primary)] hover:bg-[var(--primary-hover)] text-white rounded-lg transition-colors"
        >
          Manage API Keys
        </button>
      </div>
    </div>
  )

  return (
    <div className="fixed inset-0 z-[9997] flex items-center justify-center p-4" role="dialog" aria-modal="true">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/50 backdrop-blur-sm"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Modal */}
      <div className="relative w-full max-w-4xl max-h-[90vh] overflow-hidden rounded-xl bg-[var(--bg-primary)] border border-[var(--border-primary)] shadow-2xl flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-[var(--border-primary)]">
          <h2 className="text-lg font-semibold text-[var(--text-primary)]">Settings</h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-[var(--surface-elevated)] rounded-lg transition-colors"
            aria-label="Close settings"
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
            { id: 'privacy' as SettingsTab, label: 'Privacy & Safety' },
            { id: 'advanced' as SettingsTab, label: 'Advanced' },
            { id: 'api' as SettingsTab, label: 'API' },
            { id: 'data' as SettingsTab, label: 'Data & Account' },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-6 py-3 text-sm font-medium transition-colors border-b-2 ${
                activeTab === tab.id
                  ? 'border-[var(--primary)] text-[var(--primary)]'
                  : 'border-transparent text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--surface-elevated)]'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {activeTab === 'general' && renderGeneralTab()}
          {activeTab === 'appearance' && renderAppearanceTab()}
          {activeTab === 'privacy' && renderPrivacyTab()}
          {activeTab === 'advanced' && renderAdvancedTab()}
          {activeTab === 'api' && renderAPITab()}
          {activeTab === 'data' && renderDataTab()}
        </div>
      </div>

      {/* Memory Modal */}
      {memoryModalOpen && <MemoryModal onClose={() => setMemoryModalOpen(false)} />}
    </div>
  )
}
