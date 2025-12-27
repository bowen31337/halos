import { useState, useEffect } from 'react'
import { api } from '../services/api'

interface Prompt {
  id: string
  title: string
  content: string
  category: string
  description: string | null
  tags: string[]
  is_active: boolean
  usage_count: number
  created_at: string
  updated_at: string
}

interface PromptModalProps {
  onClose: () => void
  onUsePrompt: (content: string) => void
}

export function PromptModal({ onClose, onUsePrompt }: PromptModalProps) {
  const [prompts, setPrompts] = useState<Prompt[]>([])
  const [filteredPrompts, setFilteredPrompts] = useState<Prompt[]>([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [categoryFilter, setCategoryFilter] = useState<string>('all')
  const [categories, setCategories] = useState<string[]>([])

  // Create/Edit form state
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [editingPrompt, setEditingPrompt] = useState<Prompt | null>(null)
  const [formTitle, setFormTitle] = useState('')
  const [formContent, setFormContent] = useState('')
  const [formCategory, setFormCategory] = useState('general')
  const [formDescription, setFormDescription] = useState('')
  const [formTags, setFormTags] = useState('')

  // Load prompts and categories on mount
  useEffect(() => {
    loadPrompts()
    loadCategories()
  }, [])

  // Filter prompts based on search and category
  useEffect(() => {
    let filtered = prompts

    if (searchQuery) {
      filtered = filtered.filter(p =>
        p.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        p.content.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (p.description && p.description.toLowerCase().includes(searchQuery.toLowerCase())) ||
        (p.tags && p.tags.some(t => t.toLowerCase().includes(searchQuery.toLowerCase())))
      )
    }

    if (categoryFilter !== 'all') {
      filtered = filtered.filter(p => p.category === categoryFilter)
    }

    setFilteredPrompts(filtered)
  }, [prompts, searchQuery, categoryFilter])

  const loadPrompts = async () => {
    try {
      setLoading(true)
      const data = await api.listPrompts()
      setPrompts(data)
    } catch (error) {
      console.error('Failed to load prompts:', error)
    } finally {
      setLoading(false)
    }
  }

  const loadCategories = async () => {
    try {
      const data = await api.listPromptCategories()
      setCategories(data)
    } catch (error) {
      console.error('Failed to load categories:', error)
    }
  }

  const handleCreatePrompt = async () => {
    if (!formTitle.trim() || !formContent.trim()) return

    try {
      const tagsArray = formTags.split(',').map(t => t.trim()).filter(t => t)
      await api.createPrompt({
        title: formTitle,
        content: formContent,
        category: formCategory,
        description: formDescription || undefined,
        tags: tagsArray.length > 0 ? tagsArray : undefined,
      })
      // Reset form
      setFormTitle('')
      setFormContent('')
      setFormCategory('general')
      setFormDescription('')
      setFormTags('')
      setShowCreateForm(false)
      await loadPrompts()
    } catch (error) {
      console.error('Failed to create prompt:', error)
    }
  }

  const handleEditPrompt = (prompt: Prompt) => {
    setEditingPrompt(prompt)
    setFormTitle(prompt.title)
    setFormContent(prompt.content)
    setFormCategory(prompt.category)
    setFormDescription(prompt.description || '')
    setFormTags(prompt.tags.join(', '))
  }

  const handleSaveEdit = async () => {
    if (!editingPrompt || !formTitle.trim() || !formContent.trim()) return

    try {
      const tagsArray = formTags.split(',').map(t => t.trim()).filter(t => t)
      await api.updatePrompt(editingPrompt.id, {
        title: formTitle,
        content: formContent,
        category: formCategory,
        description: formDescription || undefined,
        tags: tagsArray.length > 0 ? tagsArray : undefined,
      })
      setEditingPrompt(null)
      setFormTitle('')
      setFormContent('')
      setFormCategory('general')
      setFormDescription('')
      setFormTags('')
      await loadPrompts()
    } catch (error) {
      console.error('Failed to update prompt:', error)
    }
  }

  const handleDeletePrompt = async (promptId: string) => {
    if (!confirm('Are you sure you want to delete this prompt?')) return

    try {
      await api.deletePrompt(promptId)
      await loadPrompts()
    } catch (error) {
      console.error('Failed to delete prompt:', error)
    }
  }

  const handleUsePrompt = async (prompt: Prompt) => {
    try {
      // Mark as used
      await api.usePrompt(prompt.id)
      // Pass content to parent
      onUsePrompt(prompt.content)
      onClose()
    } catch (error) {
      console.error('Failed to use prompt:', error)
    }
  }

  const handleToggleActive = async (prompt: Prompt) => {
    try {
      await api.updatePrompt(prompt.id, { is_active: !prompt.is_active })
      await loadPrompts()
    } catch (error) {
      console.error('Failed to toggle prompt:', error)
    }
  }

  const resetForm = () => {
    setFormTitle('')
    setFormContent('')
    setFormCategory('general')
    setFormDescription('')
    setFormTags('')
    setEditingPrompt(null)
    setShowCreateForm(false)
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
      onClick={onClose}
    >
      <div
        className="bg-[var(--bg-primary)] rounded-lg shadow-xl w-full max-w-4xl max-h-[85vh] flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-[var(--border-primary)]">
          <h2 className="text-xl font-semibold text-[var(--text-primary)]">
            Prompt Library
          </h2>
          <div className="flex gap-2">
            {!showCreateForm && !editingPrompt && (
              <button
                onClick={() => setShowCreateForm(true)}
                className="px-4 py-2 bg-[var(--primary)] text-white rounded-lg hover:opacity-90 transition-opacity"
              >
                + New Prompt
              </button>
            )}
            <button
              onClick={onClose}
              className="text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        {/* Create/Edit Form */}
        {(showCreateForm || editingPrompt) && (
          <div className="p-6 border-b border-[var(--border-primary)] bg-[var(--bg-secondary)]">
            <h3 className="text-lg font-medium text-[var(--text-primary)] mb-4">
              {editingPrompt ? 'Edit Prompt' : 'Create New Prompt'}
            </h3>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-[var(--text-primary)] mb-2">
                    Title *
                  </label>
                  <input
                    type="text"
                    value={formTitle}
                    onChange={(e) => setFormTitle(e.target.value)}
                    placeholder="e.g., Email Response Template"
                    className="w-full px-4 py-2 rounded-lg border border-[var(--border-primary)] bg-[var(--bg-primary)] text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--primary)]"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-[var(--text-primary)] mb-2">
                    Category
                  </label>
                  <select
                    value={formCategory}
                    onChange={(e) => setFormCategory(e.target.value)}
                    className="w-full px-4 py-2 rounded-lg border border-[var(--border-primary)] bg-[var(--bg-primary)] text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--primary)]"
                  >
                    <option value="general">General</option>
                    <option value="writing">Writing</option>
                    <option value="coding">Coding</option>
                    <option value="analysis">Analysis</option>
                    <option value="creative">Creative</option>
                    <option value="business">Business</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-[var(--text-primary)] mb-2">
                  Content *
                </label>
                <textarea
                  value={formContent}
                  onChange={(e) => setFormContent(e.target.value)}
                  rows={4}
                  placeholder="Enter the prompt template..."
                  className="w-full px-4 py-2 rounded-lg border border-[var(--border-primary)] bg-[var(--bg-primary)] text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--primary)]"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-[var(--text-primary)] mb-2">
                  Description
                </label>
                <input
                  type="text"
                  value={formDescription}
                  onChange={(e) => setFormDescription(e.target.value)}
                  placeholder="Brief description of when to use this prompt"
                  className="w-full px-4 py-2 rounded-lg border border-[var(--border-primary)] bg-[var(--bg-primary)] text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--primary)]"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-[var(--text-primary)] mb-2">
                  Tags (comma-separated)
                </label>
                <input
                  type="text"
                  value={formTags}
                  onChange={(e) => setFormTags(e.target.value)}
                  placeholder="email, professional, quick"
                  className="w-full px-4 py-2 rounded-lg border border-[var(--border-primary)] bg-[var(--bg-primary)] text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--primary)]"
                />
              </div>

              <div className="flex gap-3">
                <button
                  onClick={editingPrompt ? handleSaveEdit : handleCreatePrompt}
                  className="flex-1 px-4 py-2 rounded-lg bg-[var(--primary)] text-white hover:opacity-90 transition-opacity"
                >
                  {editingPrompt ? 'Save Changes' : 'Create Prompt'}
                </button>
                <button
                  onClick={resetForm}
                  className="px-4 py-2 rounded-lg border border-[var(--border-primary)] text-[var(--text-primary)] hover:bg-[var(--bg-secondary)] transition-colors"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Search and Filters */}
        <div className="p-6 border-b border-[var(--border-primary)] space-y-4">
          <div className="flex gap-4">
            <input
              type="text"
              placeholder="Search prompts by title, content, description, or tags..."
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
              {categories.map(cat => (
                <option key={cat} value={cat}>{cat}</option>
              ))}
            </select>
          </div>

          <div className="flex gap-6 text-sm text-[var(--text-secondary)]">
            <span>Total: {prompts.length}</span>
            <span>Active: {prompts.filter(p => p.is_active).length}</span>
            <span>Filtered: {filteredPrompts.length}</span>
          </div>
        </div>

        {/* Prompt List */}
        <div className="flex-1 overflow-y-auto p-6">
          {loading ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-[var(--text-secondary)]">Loading prompts...</div>
            </div>
          ) : filteredPrompts.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-[var(--text-secondary)]">
              <svg className="w-16 h-16 mb-4 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <p>No prompts found</p>
              <p className="text-sm mt-2">Create a new prompt to get started</p>
            </div>
          ) : (
            <div className="space-y-3">
              {filteredPrompts.map((prompt) => (
                <div
                  key={prompt.id}
                  className={`p-4 rounded-lg border transition-all ${
                    !prompt.is_active
                      ? 'opacity-60 border-[var(--border-primary)] bg-[var(--bg-secondary)]'
                      : 'border-[var(--border-secondary)] bg-[var(--surface-elevated)]'
                  }`}
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="px-2 py-1 rounded text-xs font-medium bg-[var(--primary)]/20 text-[var(--primary)]">
                          {prompt.category}
                        </span>
                        {!prompt.is_active && (
                          <span className="px-2 py-1 rounded text-xs font-medium bg-gray-500/20 text-gray-600">
                            Inactive
                          </span>
                        )}
                        <span className="px-2 py-1 rounded text-xs font-medium bg-[var(--text-secondary)]/20 text-[var(--text-secondary)]">
                          Uses: {prompt.usage_count}
                        </span>
                      </div>
                      <h4 className="text-[var(--text-primary)] font-medium text-lg mb-1">
                        {prompt.title}
                      </h4>
                      {prompt.description && (
                        <p className="text-sm text-[var(--text-secondary)] mb-2">
                          {prompt.description}
                        </p>
                      )}
                      <p className="text-[var(--text-primary)] bg-[var(--bg-secondary)] p-2 rounded text-sm font-mono">
                        {prompt.content.length > 100 ? prompt.content.substring(0, 100) + '...' : prompt.content}
                      </p>
                      {prompt.tags && prompt.tags.length > 0 && (
                        <div className="flex gap-1 mt-2 flex-wrap">
                          {prompt.tags.map(tag => (
                            <span key={tag} className="px-2 py-0.5 rounded text-xs bg-[var(--bg-secondary)] text-[var(--text-secondary)]">
                              #{tag}
                            </span>
                          ))}
                        </div>
                      )}
                      <p className="text-xs text-[var(--text-secondary)] mt-2">
                        Created: {new Date(prompt.created_at).toLocaleDateString()}
                      </p>
                    </div>

                    <div className="flex flex-col gap-2">
                      <button
                        onClick={() => handleUsePrompt(prompt)}
                        className="px-3 py-2 bg-[var(--primary)] text-white rounded-lg hover:opacity-90 transition-opacity text-sm"
                        title="Use this prompt"
                      >
                        Use
                      </button>
                      <button
                        onClick={() => handleToggleActive(prompt)}
                        className={`px-3 py-2 rounded transition-colors text-sm ${
                          prompt.is_active
                            ? 'text-green-600 hover:bg-green-500/20'
                            : 'text-gray-600 hover:bg-gray-500/20'
                        }`}
                        title={prompt.is_active ? 'Deactivate' : 'Activate'}
                      >
                        {prompt.is_active ? 'Active' : 'Inactive'}
                      </button>
                      <button
                        onClick={() => handleEditPrompt(prompt)}
                        className="px-3 py-2 rounded text-blue-600 hover:bg-blue-500/20 transition-colors text-sm"
                        title="Edit"
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => handleDeletePrompt(prompt.id)}
                        className="px-3 py-2 rounded text-red-600 hover:bg-red-500/20 transition-colors text-sm"
                        title="Delete"
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
