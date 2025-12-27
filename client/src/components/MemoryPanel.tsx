import { useState, useEffect } from 'react'
import { api } from '../services/api'

export interface Memory {
  id: string
  user_id: string
  content: string
  category: 'fact' | 'preference' | 'context'
  source_conversation_id: string | null
  is_active: boolean
  metadata: any
  created_at: string
  updated_at: string
}

interface MemoryPanelProps {
  onClose?: () => void
}

export function MemoryPanel({ onClose }: MemoryPanelProps) {
  const [memories, setMemories] = useState<Memory[]>([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [categoryFilter, setCategoryFilter] = useState<string>('all')
  const [showInactive, setShowInactive] = useState(false)
  const [editingMemory, setEditingMemory] = useState<Memory | null>(null)
  const [editContent, setEditContent] = useState('')

  // Load memories on mount
  useEffect(() => {
    loadMemories()
  }, [categoryFilter, showInactive])

  const loadMemories = async () => {
    try {
      setLoading(true)
      const category = categoryFilter === 'all' ? undefined : categoryFilter
      const data = await api.listMemories(category, !showInactive)
      setMemories(data)
    } catch (error) {
      console.error('Failed to load memories:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      loadMemories()
      return
    }

    try {
      setLoading(true)
      const results = await api.searchMemories(searchQuery)
      setMemories(results)
    } catch (error) {
      console.error('Search failed:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (memoryId: string) => {
    if (!confirm('Are you sure you want to delete this memory?')) return

    try {
      await api.deleteMemory(memoryId)
      setMemories(memories.filter((m) => m.id !== memoryId))
    } catch (error) {
      console.error('Failed to delete memory:', error)
      alert('Failed to delete memory')
    }
  }

  const handleToggleActive = async (memory: Memory) => {
    try {
      const updated = await api.updateMemory(memory.id, {
        is_active: !memory.is_active,
      })
      setMemories(memories.map((m) => (m.id === memory.id ? { ...m, ...updated } : m)))
    } catch (error) {
      console.error('Failed to update memory:', error)
      alert('Failed to update memory')
    }
  }

  const handleEdit = (memory: Memory) => {
    setEditingMemory(memory)
    setEditContent(memory.content)
  }

  const handleSaveEdit = async () => {
    if (!editingMemory) return

    try {
      const updated = await api.updateMemory(editingMemory.id, {
        content: editContent,
      })
      setMemories(memories.map((m) => (m.id === editingMemory.id ? { ...m, ...updated } : m)))
      setEditingMemory(null)
      setEditContent('')
    } catch (error) {
      console.error('Failed to update memory:', error)
      alert('Failed to update memory')
    }
  }

  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'fact':
        return 'bg-blue-500/20 text-blue-400'
      case 'preference':
        return 'bg-purple-500/20 text-purple-400'
      case 'context':
        return 'bg-green-500/20 text-green-400'
      default:
        return 'bg-gray-500/20 text-gray-400'
    }
  }

  const filteredMemories = memories

  return (
    <div className="h-full flex flex-col bg-[var(--background)] border-l border-[var(--border)]">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-[var(--border)]">
        <div className="flex items-center gap-2">
          <span className="text-xl">🧠</span>
          <h2 className="text-lg font-semibold text-[var(--text-primary)]">Memory Management</h2>
        </div>
        {onClose && (
          <button
            onClick={onClose}
            className="p-1 hover:bg-[var(--surface-hover)] rounded text-[var(--text-secondary)]"
          >
            ✕
          </button>
        )}
      </div>

      {/* Search and Filters */}
      <div className="p-4 border-b border-[var(--border)] space-y-3">
        <div className="flex gap-2">
          <input
            type="text"
            placeholder="Search memories..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
            className="flex-1 px-3 py-2 bg-[var(--surface)] border border-[var(--border)] rounded-lg text-[var(--text-primary)] placeholder:text-[var(--text-secondary)] focus:outline-none focus:ring-2 focus:ring-[var(--primary)]"
          />
          <button
            onClick={handleSearch}
            className="px-4 py-2 bg-[var(--primary)] text-white rounded-lg hover:opacity-90"
          >
            🔍
          </button>
        </div>

        <div className="flex gap-2">
          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            className="flex-1 px-3 py-2 bg-[var(--surface)] border border-[var(--border)] rounded-lg text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--primary)]"
          >
            <option value="all">All Categories</option>
            <option value="fact">Facts</option>
            <option value="preference">Preferences</option>
            <option value="context">Context</option>
          </select>

          <label className="flex items-center gap-2 px-3 py-2 bg-[var(--surface)] border border-[var(--border)] rounded-lg cursor-pointer">
            <input
              type="checkbox"
              checked={showInactive}
              onChange={(e) => setShowInactive(e.target.checked)}
              className="w-4 h-4"
            />
            <span className="text-sm text-[var(--text-secondary)]">Show inactive</span>
          </label>
        </div>
      </div>

      {/* Memory List */}
      <div className="flex-1 overflow-y-auto">
        {loading ? (
          <div className="flex flex-col items-center justify-center h-full text-[var(--text-secondary)]">
            <div className="loading-spinner primary mb-2"></div>
            <span>Loading memories...</span>
          </div>
        ) : filteredMemories.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-[var(--text-secondary)] space-y-2">
            <span className="text-4xl">🧠</span>
            <p>No memories found</p>
            <p className="text-sm">Memories will be automatically stored when you tell the AI to remember something</p>
          </div>
        ) : (
          <div className="divide-y divide-[var(--border)]">
            {filteredMemories.map((memory) => (
              <div
                key={memory.id}
                className={`p-4 hover:bg-[var(--surface-hover)] transition-colors ${
                  !memory.is_active ? 'opacity-60' : ''
                }`}
              >
                {editingMemory?.id === memory.id ? (
                  // Edit mode
                  <div className="space-y-2">
                    <textarea
                      value={editContent}
                      onChange={(e) => setEditContent(e.target.value)}
                      className="w-full px-3 py-2 bg-[var(--surface)] border border-[var(--border)] rounded-lg text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--primary)]"
                      rows={3}
                    />
                    <div className="flex gap-2">
                      <button
                        onClick={handleSaveEdit}
                        className="px-3 py-1 bg-[var(--primary)] text-white rounded hover:opacity-90"
                      >
                        Save
                      </button>
                      <button
                        onClick={() => {
                          setEditingMemory(null)
                          setEditContent('')
                        }}
                        className="px-3 py-1 bg-[var(--surface)] text-[var(--text-primary)] rounded hover:bg-[var(--surface-hover)]"
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                ) : (
                  // View mode
                  <div className="space-y-2">
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <span
                            className={`px-2 py-0.5 rounded text-xs font-medium ${getCategoryColor(
                              memory.category
                            )}`}
                          >
                            {memory.category}
                          </span>
                          {!memory.is_active && (
                            <span className="px-2 py-0.5 rounded text-xs bg-gray-500/20 text-gray-400">
                              Inactive
                            </span>
                          )}
                        </div>
                        <p className="text-[var(--text-primary)]">{memory.content}</p>
                        <p className="text-xs text-[var(--text-secondary)] mt-1">
                          {new Date(memory.created_at).toLocaleDateString()}
                        </p>
                      </div>
                      <div className="flex items-center gap-1">
                        <button
                          onClick={() => handleEdit(memory)}
                          className="p-1.5 hover:bg-[var(--surface)] rounded text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
                          title="Edit"
                        >
                          ✏️
                        </button>
                        <button
                          onClick={() => handleToggleActive(memory)}
                          className="p-1.5 hover:bg-[var(--surface)] rounded text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
                          title={memory.is_active ? 'Deactivate' : 'Activate'}
                        >
                          {memory.is_active ? '👁️' : '👁️‍🗨️'}
                        </button>
                        <button
                          onClick={() => handleDelete(memory.id)}
                          className="p-1.5 hover:bg-red-500/20 rounded text-[var(--text-secondary)] hover:text-red-400"
                          title="Delete"
                        >
                          🗑️
                        </button>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Footer with stats */}
      <div className="p-3 border-t border-[var(--border)] text-xs text-[var(--text-secondary)]">
        {filteredMemories.length} {filteredMemories.length === 1 ? 'memory' : 'memories'}
        {searchQuery && ` matching "${searchQuery}"`}
      </div>
    </div>
  )
}
