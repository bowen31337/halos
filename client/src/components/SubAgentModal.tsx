import { useState, useEffect } from 'react'
import { api } from '../services/api'

interface SubAgent {
  id: string
  user_id: string
  name: string
  description?: string
  system_prompt: string
  model: string
  tools: string[]
  is_builtin: boolean
  is_active: boolean
  created_at: string
  updated_at: string
}

interface SubAgentModalProps {
  onClose: () => void
}

type Tab = 'library' | 'create'

export function SubAgentModal({ onClose }: SubAgentModalProps) {
  const [activeTab, setActiveTab] = useState<Tab>('library')
  const [subagents, setSubagents] = useState<SubAgent[]>([])
  const [loading, setLoading] = useState(true)

  // Create form state
  const [newName, setNewName] = useState('')
  const [newDescription, setNewDescription] = useState('')
  const [newSystemPrompt, setNewSystemPrompt] = useState('')
  const [newModel, setNewModel] = useState('claude-sonnet-4-5-20250929')
  const [newTools, setNewTools] = useState<string[]>([])
  const [isCreating, setIsCreating] = useState(false)

  // Available tools
  const availableTools = ['search', 'read_file', 'write_file', 'edit_file', 'glob', 'grep', 'execute']

  useEffect(() => {
    loadSubagents()
  }, [])

  const loadSubagents = async () => {
    setLoading(true)
    try {
      const data = await api.getSubagents(true)
      setSubagents(data)
    } catch (error) {
      console.error('Failed to load subagents:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleCreateSubagent = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsCreating(true)
    try {
      await api.createSubagent({
        name: newName,
        description: newDescription,
        system_prompt: newSystemPrompt,
        model: newModel,
        tools: newTools,
      })
      // Reset form and switch to library
      setNewName('')
      setNewDescription('')
      setNewSystemPrompt('')
      setNewModel('claude-sonnet-4-5-20250929')
      setNewTools([])
      setActiveTab('library')
      loadSubagents()
    } catch (error) {
      console.error('Failed to create subagent:', error)
      alert('Failed to create subagent. Please check the form and try again.')
    } finally {
      setIsCreating(false)
    }
  }

  const toggleTool = (tool: string) => {
    setNewTools(prev =>
      prev.includes(tool) ? prev.filter(t => t !== tool) : [...prev, tool]
    )
  }

  const handleBackdropClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (e.target === e.currentTarget) {
      onClose()
    }
  }

  const renderLibraryTab = () => {
    if (loading) {
      return (
        <div className="flex items-center justify-center py-12">
          <div className="loading-spinner primary"></div>
        </div>
      )
    }

    // Group by builtin vs custom
    const builtinAgents = subagents.filter(a => a.is_builtin)
    const customAgents = subagents.filter(a => !a.is_builtin)

    return (
      <div className="space-y-6">
        {/* Built-in SubAgents */}
        <div>
          <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-3">Built-in SubAgents</h3>
          <div className="grid grid-cols-1 gap-3">
            {builtinAgents.map(agent => (
              <div
                key={agent.id}
                className="border border-[var(--border-primary)] rounded-lg p-4 bg-[var(--bg-secondary)]"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <h4 className="font-medium text-[var(--text-primary)]">{agent.name}</h4>
                      <span className="px-2 py-0.5 text-xs rounded-full bg-[var(--surface-elevated)] text-[var(--text-secondary)]">
                        Built-in
                      </span>
                    </div>
                    <p className="text-sm text-[var(--text-secondary)] mt-1">{agent.description}</p>
                    <div className="mt-2 flex flex-wrap gap-1">
                      {agent.tools.map(tool => (
                        <span
                          key={tool}
                          className="px-2 py-0.5 text-xs rounded bg-[var(--primary)]/10 text-[var(--primary)]"
                        >
                          {tool}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Custom SubAgents */}
        {customAgents.length > 0 && (
          <div>
            <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-3">Custom SubAgents</h3>
            <div className="grid grid-cols-1 gap-3">
              {customAgents.map(agent => (
                <div
                  key={agent.id}
                  className="border border-[var(--border-primary)] rounded-lg p-4 bg-[var(--bg-secondary)]"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <h4 className="font-medium text-[var(--text-primary)]">{agent.name}</h4>
                      <p className="text-sm text-[var(--text-secondary)] mt-1">{agent.description}</p>
                      <div className="mt-2 flex flex-wrap gap-1">
                        {agent.tools.map(tool => (
                          <span
                            key={tool}
                            className="px-2 py-0.5 text-xs rounded bg-[var(--surface-elevated)] text-[var(--text-secondary)]"
                          >
                            {tool}
                          </span>
                        ))}
                      </div>
                    </div>
                    <span className={`px-2 py-1 text-xs rounded-full ${
                      agent.is_active
                        ? 'bg-green-500/10 text-green-500'
                        : 'bg-gray-500/10 text-gray-500'
                    }`}>
                      {agent.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {customAgents.length === 0 && builtinAgents.length === 0 && (
          <div className="text-center py-12 text-[var(--text-secondary)]">
            No subagents available
          </div>
        )}
      </div>
    )
  }

  const renderCreateTab = () => (
    <form onSubmit={handleCreateSubagent} className="space-y-6">
      {/* Name */}
      <div>
        <label className="block text-sm font-medium text-[var(--text-primary)] mb-2">
          Name *
        </label>
        <input
          type="text"
          value={newName}
          onChange={e => setNewName(e.target.value)}
          placeholder="e.g., my-research-agent"
          required
          className="w-full px-3 py-2 border border-[var(--border-primary)] rounded-md bg-[var(--bg-primary)] text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--primary)]"
        />
        <p className="text-xs text-[var(--text-secondary)] mt-1">
          Use hyphens instead of spaces (e.g., my-agent not my agent)
        </p>
      </div>

      {/* Description */}
      <div>
        <label className="block text-sm font-medium text-[var(--text-primary)] mb-2">
          Description
        </label>
        <textarea
          value={newDescription}
          onChange={e => setNewDescription(e.target.value)}
          placeholder="What does this sub-agent do?"
          rows={2}
          className="w-full px-3 py-2 border border-[var(--border-primary)] rounded-md bg-[var(--bg-primary)] text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--primary)]"
        />
      </div>

      {/* System Prompt */}
      <div>
        <label className="block text-sm font-medium text-[var(--text-primary)] mb-2">
          System Prompt *
        </label>
        <textarea
          value={newSystemPrompt}
          onChange={e => setNewSystemPrompt(e.target.value)}
          placeholder="You are a specialized agent that..."
          required
          rows={4}
          className="w-full px-3 py-2 border border-[var(--border-primary)] rounded-md bg-[var(--bg-primary)] text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--primary)]"
        />
      </div>

      {/* Model */}
      <div>
        <label className="block text-sm font-medium text-[var(--text-primary)] mb-2">
          Model
        </label>
        <select
          value={newModel}
          onChange={e => setNewModel(e.target.value)}
          className="w-full px-3 py-2 border border-[var(--border-primary)] rounded-md bg-[var(--bg-primary)] text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--primary)]"
        >
          <option value="claude-sonnet-4-5-20250929">Claude Sonnet 4.5</option>
          <option value="claude-opus-4-20250514">Claude Opus 4</option>
          <option value="claude-haiku-3-5-20241022">Claude Haiku 3.5</option>
        </select>
      </div>

      {/* Tools */}
      <div>
        <label className="block text-sm font-medium text-[var(--text-primary)] mb-2">
          Tools
        </label>
        <div className="grid grid-cols-2 gap-2">
          {availableTools.map(tool => (
            <label
              key={tool}
              className={`flex items-center gap-2 px-3 py-2 rounded-md border cursor-pointer transition-colors ${
                newTools.includes(tool)
                  ? 'border-[var(--primary)] bg-[var(--primary)]/10'
                  : 'border-[var(--border-primary)] hover:border-[var(--primary)]/50'
              }`}
            >
              <input
                type="checkbox"
                checked={newTools.includes(tool)}
                onChange={() => toggleTool(tool)}
                className="rounded"
              />
              <span className="text-sm text-[var(--text-primary)]">{tool}</span>
            </label>
          ))}
        </div>
      </div>

      {/* Submit */}
      <div className="flex justify-end gap-3 pt-4 border-t border-[var(--border-primary)]">
        <button
          type="button"
          onClick={() => setActiveTab('library')}
          className="px-4 py-2 rounded-md border border-[var(--border-primary)] hover:bg-[var(--bg-secondary)] transition-colors"
        >
          Cancel
        </button>
        <button
          type="submit"
          disabled={isCreating}
          className="px-4 py-2 rounded-md bg-[var(--primary)] text-white hover:bg-[var(--primary-hover)] disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {isCreating ? 'Creating...' : 'Create SubAgent'}
        </button>
      </div>
    </form>
  )

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm animate-in fade-in duration-200"
      onClick={handleBackdropClick}
    >
      <div className="w-full max-w-4xl max-h-[90vh] overflow-hidden rounded-xl border border-[var(--border-primary)] bg-[var(--bg-primary)] shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-[var(--border-primary)] px-6 py-4">
          <h2 className="text-lg font-semibold text-[var(--text-primary)]">SubAgent Library</h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-[var(--bg-secondary)] rounded-md transition-colors"
            aria-label="Close"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-[var(--border-primary)]">
          <button
            onClick={() => setActiveTab('library')}
            className={`px-6 py-3 text-sm font-medium transition-colors ${
              activeTab === 'library'
                ? 'text-[var(--primary)] border-b-2 border-[var(--primary)]'
                : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
            }`}
          >
            Library
          </button>
          <button
            onClick={() => setActiveTab('create')}
            className={`px-6 py-3 text-sm font-medium transition-colors ${
              activeTab === 'create'
                ? 'text-[var(--primary)] border-b-2 border-[var(--primary)]'
                : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
            }`}
          >
            Create Custom
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-140px)]">
          {activeTab === 'library' ? renderLibraryTab() : renderCreateTab()}
        </div>
      </div>
    </div>
  )
}
