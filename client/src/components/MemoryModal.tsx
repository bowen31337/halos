import { useState, useEffect } from 'react'
import { api } from '../services/api'

interface Memory {
  id: string
  content: string
  category: 'fact' | 'preference' | 'context'
  is_active: boolean
  created_at: string
  updated_at: string
}

interface MemoryModalProps {
  onClose: () => void
}

export function MemoryModal({ onClose }: MemoryModalProps) {
  const [memories, setMemories] = useState<Memory[]>([])
  const [filteredMemories, setFilteredMemories] = useState<Memory[]>([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [categoryFilter, setCategoryFilter] = useState<string>('all')
  const [editingMemory, setEditingMemory] = useState<Memory | null>(null)
  const [editContent, setEditContent] = useState('')
  const [editCategory, setEditCategory] = useState<Memory['category']>('fact')

  // Load memories on mount
  useEffect(() => {
    loadMemories()
  }, [])

  // Filter memories based on search and category
  useEffect(() => {
    let filtered = memories

    if (searchQuery) {
      filtered = filtered.filter(m =>
        m.content.toLowerCase().includes(searchQuery.toLowerCase())
      )
    }

    if (categoryFilter !== 'all') {
      filtered = filtered.filter(m => m.category === categoryFilter)
    }

    setFilteredMemories(filtered)
  }, [memories, searchQuery, categoryFilter])

  const loadMemories = async () => {
    try {
      setLoading(true)
      const data = await api.listMemories()
      setMemories(data)
    } catch (error) {
      console.error('Failed to load memories:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleCreateMemory = async () => {
    try {
      await api.createMemory({
        content: 'New memory',
        category: 'fact',
      })
      await loadMemories()
    } catch (error) {
      console.error('Failed to create memory:', error)
    }
  }

  const handleEditMemory = (memory: Memory) => {
    setEditingMemory(memory)
    setEditContent(memory.content)
    setEditCategory(memory.category)
  }

  const handleSaveEdit = async () => {
    if (!editingMemory) return

    try {
      await api.updateMemory(editingMemory.id, {
        content: editContent,
        category: editCategory,
      })
      setEditingMemory(null)
      await loadMemories()
    } catch (error) {
      console.error('Failed to update memory:', error)
    }
  }

  const handleDeleteMemory = async (memoryId: string) => {
    if (!confirm('Are you sure you want to delete this memory?')) return

    try {
      await api.deleteMemory(memoryId)
      await loadMemories()
    } catch (error) {
      console.error('Failed to delete memory:', error)
    }
  }

  const handleToggleActive = async (memory: Memory) => {
    try {
      await api.updateMemory(memory.id, {
        is_active: !memory.is_active,
      })
      await loadMemories()
    } catch (error) {
      console.error('Failed to toggle memory:', error)
    }
  }

  const getCategoryColor = (category: Memory['category']) => {
    switch (category) {
      case 'fact':
        return 'bg-blue-500/20 text-blue-600'
      case 'preference':
        return 'bg-green-500/20 text-green-600'
      case 'context':
        return 'bg-purple-500/20 text-purple-600'
      default:
        return 'bg-gray-500/20 text-gray-600'
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
      onClick={onClose}
    >
      <div
        className="bg-[var(--bg-primary)] rounded-lg shadow-xl w-full max-w-4xl max-h-[80vh] flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-[var(--border-primary)]">
          <h2 className="text-xl font-semibold text-[var(--text-primary)]">
            Memory Management
          </h2>
          <button
            onClick={onClose}
            className="text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Search and Filters */}
        <div className="p-6 border-b border-[var(--border-primary)] space-y-4">
          <div className="flex gap-4">
            <input
              type="text"
              placeholder="Search memories..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="flex-1 px-4 py-2 rounded-lg border border-[var(--border-primary)] bg-[var(--bg-secondary)] text-[var(--text-primary)] placeholder-[var(--text-secondary)] focus:outline-none focus:ring-2 focus:ring-[var(--primary)]"
            />
            <select
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
              className="px-4 py-2 rounded-lg border border-[var(--border-primary)] bg-[var(--bg-secondary)] text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--primary)]"
            >
              <option value="all">All Categories</option>
              <option value="fact">Facts</option>
              <option value="preference">Preferences</option>
              <option value="context">Context</option>
            </select>
            <button
              onClick={handleCreateMemory}
              className="px-4 py-2 bg-[var(--primary)] text-white rounded-lg hover:opacity-90 transition-opacity"
            >
              + New Memory
            </button>
          </div>

          {/* Stats */}
          <div className="flex gap-6 text-sm text-[var(--text-secondary)]">
            <span>Total: {memories.length}</span>
            <span>Active: {memories.filter(m => m.is_active).length}</span>
            <span>Filtered: {filteredMemories.length}</span>
          </div>
        </div>

        {/* Memory List */}
        <div className="flex-1 overflow-y-auto p-6">
          {loading ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-[var(--text-secondary)]">Loading memories...</div>
            </div>
          ) : filteredMemories.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-[var(--text-secondary)]">
              <svg className="w-16 h-16 mb-4 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
              <p>No memories found</p>
              <p className="text-sm mt-2">Create a new memory to get started</p>
            </div>
          ) : (
            <div className="space-y-3">
              {filteredMemories.map((memory) => (
                <div
                  key={memory.id}
                  className={`p-4 rounded-lg border transition-all ${
                    !memory.is_active
                      ? 'opacity-60 border-[var(--border-primary)] bg-[var(--bg-secondary)]'
                      : 'border-[var(--border-secondary)] bg-[var(--surface-elevated)]'
                  }`}
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <span className={`px-2 py-1 rounded text-xs font-medium ${getCategoryColor(memory.category)}`}>
                          {memory.category}
                        </span>
                        {!memory.is_active && (
                          <span className="px-2 py-1 rounded text-xs font-medium bg-gray-500/20 text-gray-600">
                            Inactive
                          </span>
                        )}
                      </div>
                      <p className="text-[var(--text-primary)]">{memory.content}</p>
                      <p className="text-xs text-[var(--text-secondary)] mt-2">
                        Created: {new Date(memory.created_at).toLocaleDateString()}
                        {memory.updated_at !== memory.created_at && (
                          <> • Updated: {new Date(memory.updated_at).toLocaleDateString()}</>
                        )}
                      </p>
                    </div>

                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => handleToggleActive(memory)}
                        className={`p-2 rounded transition-colors ${
                          memory.is_active
                            ? 'text-green-600 hover:bg-green-500/20'
                            : 'text-gray-600 hover:bg-gray-500/20'
                        }`}
                        title={memory.is_active ? 'Deactivate' : 'Activate'}
                      >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          {memory.is_active ? (
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                          ) : (
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                          )}
                        </svg>
                      </button>
                      <button
                        onClick={() => handleEditMemory(memory)}
                        className="p-2 rounded text-blue-600 hover:bg-blue-500/20 transition-colors"
                        title="Edit"
                      >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                        </svg>
                      </button>
                      <button
                        onClick={() => handleDeleteMemory(memory.id)}
                        className="p-2 rounded text-red-600 hover:bg-red-500/20 transition-colors"
                        title="Delete"
                      >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                        </svg>
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Edit Modal */}
        {editingMemory && (
          <div className="fixed inset-0 z-60 flex items-center justify-center bg-black/50">
            <div className="bg-[var(--bg-primary)] rounded-lg shadow-xl w-full max-w-md p-6">
              <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-4">
                Edit Memory
              </h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-[var(--text-primary)] mb-2">
                    Category
                  </label>
                  <select
                    value={editCategory}
                    onChange={(e) => setEditCategory(e.target.value as Memory['category'])}
                    className="w-full px-4 py-2 rounded-lg border border-[var(--border-primary)] bg-[var(--bg-secondary)] text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--primary)]"
                  >
                    <option value="fact">Fact</option>
                    <option value="preference">Preference</option>
                    <option value="context">Context</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-[var(--text-primary)] mb-2">
                    Content
                  </label>
                  <textarea
                    value={editContent}
                    onChange={(e) => setEditContent(e.target.value)}
                    rows={4}
                    className="w-full px-4 py-2 rounded-lg border border-[var(--border-primary)] bg-[var(--bg-secondary)] text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--primary)]"
                  />
                </div>
              </div>
              <div className="flex gap-3 mt-6">
                <button
                  onClick={() => setEditingMemory(null)}
                  className="flex-1 px-4 py-2 rounded-lg border border-[var(--border-primary)] text-[var(--text-primary)] hover:bg-[var(--bg-secondary)] transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleSaveEdit}
                  className="flex-1 px-4 py-2 rounded-lg bg-[var(--primary)] text-white hover:opacity-90 transition-opacity"
                >
                  Save
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
