import React, { useEffect, useState } from 'react'
import { useMemoryStore, Memory } from '../stores/memoryStore'

interface MemoryManagerProps {
  onClose: () => void
}

export const MemoryManager: React.FC<MemoryManagerProps> = ({ onClose }) => {
  const {
    memories,
    isLoading,
    error,
    memoryEnabled,
    fetchMemories,
    createMemory,
    updateMemory,
    deleteMemory,
    searchMemories,
    toggleMemoryEnabled,
    clearError
  } = useMemoryStore()

  const [newContent, setNewContent] = useState('')
  const [newCategory, setNewCategory] = useState<'fact' | 'preference' | 'context'>('fact')
  const [searchQuery, setSearchQuery] = useState('')
  const [showCreateForm, setShowCreateForm] = useState(false)

  useEffect(() => {
    fetchMemories()
  }, [fetchMemories])

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newContent.trim()) return

    try {
      await createMemory(newContent, newCategory)
      setNewContent('')
      setShowCreateForm(false)
    } catch (error) {
      // Error is handled by store
    }
  }

  const handleDelete = async (id: string) => {
    if (confirm('Are you sure you want to delete this memory?')) {
      try {
        await deleteMemory(id)
      } catch (error) {
        // Error is handled by store
      }
    }
  }

  const handleToggleActive = async (memory: Memory) => {
    try {
      await updateMemory(memory.id, { is_active: !memory.is_active })
    } catch (error) {
      // Error is handled by store
    }
  }

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!searchQuery.trim()) {
      fetchMemories()
      return
    }
    try {
      await searchMemories(searchQuery)
    } catch (error) {
      // Error is handled by store
    }
  }

  const handleToggleMemoryEnabled = async (enabled: boolean) => {
    toggleMemoryEnabled(enabled)
    // Also update backend settings
    try {
      await fetch('/api/settings', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ memory_enabled: enabled })
      })
    } catch (error) {
      console.error('Failed to update memory setting:', error)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={onClose}>
      <div className="bg-[#1e1e1e] rounded-lg w-full max-w-2xl max-h-[80vh] overflow-hidden shadow-xl" onClick={e => e.stopPropagation()}>
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-[#333]">
          <h2 className="text-xl font-semibold text-white">Long-Term Memory</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-white text-2xl">×</button>
        </div>

        {/* Memory Toggle */}
        <div className="p-4 border-b border-[#333] bg-[#252525]">
          <label className="flex items-center justify-between cursor-pointer">
            <span className="text-sm font-medium text-gray-300">
              Memory Enabled
              <span className="ml-2 text-xs text-gray-500 font-normal">
                {memoryEnabled ? 'Active' : 'Disabled'}
              </span>
            </span>
            <div className="relative inline-block w-12 h-6 align-middle select-none">
              <input
                type="checkbox"
                checked={memoryEnabled}
                onChange={(e) => handleToggleMemoryEnabled(e.target.checked)}
                className="peer sr-only"
              />
              <div className={`w-12 h-6 rounded-full transition-colors ${
                memoryEnabled ? 'bg-blue-600' : 'bg-gray-600'
              }`}></div>
              <div className={`absolute left-1 top-1 w-4 h-4 bg-white rounded-full transition-transform ${
                memoryEnabled ? 'translate-x-6' : ''
              }`}></div>
            </div>
          </label>
        </div>

        {/* Error Display */}
        {error && (
          <div className="mx-4 mt-4 p-3 bg-red-900/30 border border-red-700 rounded text-red-200 flex justify-between items-center">
            <span>{error}</span>
            <button onClick={clearError} className="text-red-300 hover:text-red-100">×</button>
          </div>
        )}

        {/* Search */}
        <div className="p-4 border-b border-[#333]">
          <form onSubmit={handleSearch} className="flex gap-2">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search memories..."
              className="flex-1 bg-[#1e1e1e] border border-[#333] rounded px-3 py-2 text-white focus:outline-none focus:border-blue-500"
            />
            <button
              type="submit"
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded text-white transition-colors"
            >
              Search
            </button>
            <button
              type="button"
              onClick={() => { setSearchQuery(''); fetchMemories(); }}
              className="px-4 py-2 bg-[#333] hover:bg-[#444] rounded text-white transition-colors"
            >
              Clear
            </button>
          </form>
        </div>

        {/* Create Form */}
        <div className="p-4 border-b border-[#333]">
          <button
            onClick={() => setShowCreateForm(!showCreateForm)}
            className="w-full mb-3 px-4 py-2 bg-green-600 hover:bg-green-700 rounded text-white transition-colors flex items-center justify-center gap-2"
          >
            <span>{showCreateForm ? '−' : '+'}</span>
            {showCreateForm ? 'Hide Create Form' : 'Create New Memory'}
          </button>

          {showCreateForm && (
            <form onSubmit={handleCreate} className="space-y-3">
              <textarea
                value={newContent}
                onChange={(e) => setNewContent(e.target.value)}
                placeholder="Enter memory content (e.g., 'My favorite color is blue')"
                className="w-full bg-[#1e1e1e] border border-[#333] rounded px-3 py-2 text-white focus:outline-none focus:border-blue-500 min-h-[80px] resize-y"
                required
              />
              <div className="flex gap-2 items-center">
                <select
                  value={newCategory}
                  onChange={(e) => setNewCategory(e.target.value as 'fact' | 'preference' | 'context')}
                  className="bg-[#1e1e1e] border border-[#333] rounded px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                >
                  <option value="fact">Fact</option>
                  <option value="preference">Preference</option>
                  <option value="context">Context</option>
                </select>
                <button
                  type="submit"
                  disabled={isLoading}
                  className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded text-white transition-colors disabled:opacity-50"
                >
                  {isLoading ? 'Saving...' : 'Save Memory'}
                </button>
              </div>
            </form>
          )}
        </div>

        {/* Memories List */}
        <div className="p-4 overflow-y-auto" style={{ maxHeight: '400px' }}>
          {isLoading && memories.length === 0 ? (
            <div className="text-center text-[var(--text-secondary)] py-8">
              <div className="loading-spinner primary mb-2 mx-auto"></div>
              Loading memories...
            </div>
          ) : memories.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 px-4 text-center">
              {/* Empty state illustration */}
              <div className="text-5xl mb-4 opacity-50">🧠</div>

              {/* Empty state text */}
              <h3 className="text-base font-semibold text-[var(--text-primary)] mb-2">
                No memories yet
              </h3>
              <p className="text-sm text-[var(--text-secondary)] mb-4 max-w-xs">
                Memories help the agent remember important information across conversations
              </p>

              {/* Call-to-action hint */}
              <div className="text-xs text-[var(--text-muted)] bg-[var(--bg-secondary)] px-3 py-2 rounded-lg">
                💡 Ask the agent to remember something, or create a memory manually above
              </div>
            </div>
          ) : (
            <div className="space-y-3">
              {memories.map((memory) => (
                <div
                  key={memory.id}
                  className={`p-3 rounded border ${
                    memory.is_active
                      ? 'border-[#333] bg-[#252525]'
                      : 'border-[#333] bg-[#1a1a1a] opacity-60'
                  }`}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <span className={`text-xs px-2 py-0.5 rounded ${
                          memory.category === 'fact' ? 'bg-blue-900/50 text-blue-300' :
                          memory.category === 'preference' ? 'bg-purple-900/50 text-purple-300' :
                          'bg-green-900/50 text-green-300'
                        }`}>
                          {memory.category.toUpperCase()}
                        </span>
                        <span className="text-xs text-gray-500">
                          {new Date(memory.created_at).toLocaleDateString()}
                        </span>
                      </div>
                      <p className="text-gray-200 text-sm">{memory.content}</p>
                    </div>
                    <div className="flex gap-1">
                      <button
                        onClick={() => handleToggleActive(memory)}
                        className={`px-2 py-1 rounded text-xs ${
                          memory.is_active
                            ? 'bg-yellow-700/50 hover:bg-yellow-600 text-yellow-200'
                            : 'bg-green-700/50 hover:bg-green-600 text-green-200'
                        }`}
                        title={memory.is_active ? 'Deactivate' : 'Activate'}
                      >
                        {memory.is_active ? '⏸' : '▶'}
                      </button>
                      <button
                        onClick={() => handleDelete(memory.id)}
                        className="px-2 py-1 rounded text-xs bg-red-700/50 hover:bg-red-600 text-red-200"
                        title="Delete"
                      >
                        🗑
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-[#333] text-xs text-gray-500">
          <p>
            Memories are automatically extracted from conversations and stored in long-term memory.
            Toggle memory off to disable automatic extraction.
          </p>
        </div>
      </div>
    </div>
  )
}
