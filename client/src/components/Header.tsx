import { useState } from 'react'
import { useUIStore } from '../stores/uiStore'

const MODELS = [
  { id: 'claude-sonnet-4-5-20250929', name: 'Claude Sonnet 4.5', description: 'Balanced' },
  { id: 'claude-haiku-4-5-20251001', name: 'Claude Haiku 4.5', description: 'Fast' },
  { id: 'claude-opus-4-1-20250805', name: 'Claude Opus 4.1', description: 'Most capable' },
]

export function Header() {
  const { toggleSidebar, selectedModel, setSelectedModel } = useUIStore()
  const [modelDropdownOpen, setModelDropdownOpen] = useState(false)

  const currentModel = MODELS.find(m => m.id === selectedModel) || MODELS[0]

  return (
    <div className="h-14 border-b border-[var(--border-primary)] bg-[var(--surface-secondary)] flex items-center justify-between px-4">
      {/* Left: Toggle sidebar */}
      <div className="flex items-center gap-3">
        <button
          onClick={toggleSidebar}
          className="p-2 hover:bg-[var(--surface-elevated)] rounded-lg transition-colors"
          title="Toggle sidebar"
        >
          <svg className="w-5 h-5 text-[var(--text-primary)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>
      </div>

      {/* Center: Model selector dropdown */}
      <div className="flex items-center gap-2 relative">
        <button
          onClick={() => setModelDropdownOpen(!modelDropdownOpen)}
          className="flex items-center gap-2 px-3 py-1.5 bg-[var(--surface-elevated)] hover:bg-[var(--bg-primary)] rounded-full text-sm transition-colors"
          title="Select model"
        >
          <span className="text-[var(--text-primary)] font-medium">{currentModel.name}</span>
          <span className="text-[var(--text-secondary)] text-xs">{currentModel.description}</span>
          <svg className={`w-4 h-4 text-[var(--text-secondary)] transition-transform ${modelDropdownOpen ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </button>

        {/* Dropdown menu */}
        {modelDropdownOpen && (
          <>
            <div
              className="fixed inset-0 z-10"
              onClick={() => setModelDropdownOpen(false)}
            />
            <div className="absolute top-full left-1/2 -translate-x-1/2 mt-2 w-72 bg-[var(--bg-primary)] border border-[var(--border-primary)] rounded-lg shadow-lg z-20 py-2">
              {MODELS.map((model) => (
                <button
                  key={model.id}
                  onClick={() => {
                    setSelectedModel(model.id)
                    setModelDropdownOpen(false)
                  }}
                  className={`w-full px-4 py-3 text-left hover:bg-[var(--surface-elevated)] transition-colors ${
                    selectedModel === model.id ? 'bg-[var(--surface-elevated)]' : ''
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="font-medium text-[var(--text-primary)]">{model.name}</div>
                      <div className="text-xs text-[var(--text-secondary)]">{model.description}</div>
                    </div>
                    {selectedModel === model.id && (
                      <svg className="w-5 h-5 text-[var(--primary)]" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                      </svg>
                    )}
                  </div>
                </button>
              ))}
            </div>
          </>
        )}
      </div>

      {/* Right: Actions */}
      <div className="flex items-center gap-2">
        <button
          className="p-2 hover:bg-[var(--surface-elevated)] rounded-lg transition-colors"
          title="Settings"
        >
          <svg className="w-5 h-5 text-[var(--text-primary)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
        </button>
      </div>
    </div>
  )
}
