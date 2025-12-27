import { useState, useEffect } from 'react'
import { useTagStore } from '../stores/tagStore'
import type { Tag } from '../stores/conversationStore'

interface TagManagerProps {
  conversationId?: string
  conversationTags?: Tag[]
  onTagsUpdated?: (tags: Tag[]) => void
  mode?: 'manage' | 'select'
}

const PRESET_COLORS = [
  '#3b82f6', // Blue
  '#ef4444', // Red
  '#10b981', // Green
  '#f59e0b', // Amber
  '#8b5cf6', // Purple
  '#ec4899', // Pink
  '#06b6d4', // Cyan
  '#6366f1', // Indigo
]

export function TagManager({ conversationId, conversationTags, onTagsUpdated, mode = 'manage' }: TagManagerProps) {
  const {
    tags,
    isLoading,
    loadTags,
    createTag,
    deleteTag,
    updateConversationTags,
    selectedTags,
    setSelectedTags,
    clearSelectedTags,
  } = useTagStore()

  const [showCreateForm, setShowCreateForm] = useState(false)
  const [newTagName, setNewTagName] = useState('')
  const [newTagColor, setNewTagColor] = useState(PRESET_COLORS[0])
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadTags()
  }, [loadTags])

  // Initialize selected tags from conversation
  useEffect(() => {
    if (conversationTags && mode === 'select') {
      setSelectedTags(conversationTags.map((t) => t.id))
    }
  }, [conversationTags, mode, setSelectedTags])

  const handleCreateTag = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    if (!newTagName.trim()) {
      setError('Tag name is required')
      return
    }

    try {
      const tag = await createTag(newTagName.trim(), newTagColor)
      setNewTagName('')
      setShowCreateForm(false)

      // If in select mode and conversationId exists, add to conversation
      if (mode === 'select' && conversationId) {
        const newSelected = [...selectedTags, tag.id]
        setSelectedTags(newSelected)
        await updateConversationTags(conversationId, newSelected)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create tag')
    }
  }

  const handleDeleteTag = async (tagId: string) => {
    if (!confirm('Delete this tag? It will be removed from all conversations.')) return

    try {
      await deleteTag(tagId)
      // Also remove from selected if in select mode
      if (mode === 'select') {
        const newSelected = selectedTags.filter((id) => id !== tagId)
        setSelectedTags(newSelected)
        if (conversationId) {
          await updateConversationTags(conversationId, newSelected)
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete tag')
    }
  }

  const handleToggleTag = async (tagId: string) => {
    if (!conversationId || mode !== 'select') return

    const newSelected = selectedTags.includes(tagId)
      ? selectedTags.filter((id) => id !== tagId)
      : [...selectedTags, tagId]

    setSelectedTags(newSelected)
    await updateConversationTags(conversationId, newSelected)
  }

  const availableTags = tags.filter((tag) => !conversationTags?.some((ct) => ct.id === tag.id))

  if (isLoading && tags.length === 0) {
    return <div className="p-4 text-sm text-gray-500">Loading tags...</div>
  }

  return (
    <div className="p-4 space-y-4">
      {error && (
        <div className="bg-red-500/10 border border-red-500/30 text-red-500 px-3 py-2 rounded text-sm">
          {error}
        </div>
      )}

      {/* Existing Tags */}
      <div>
        <div className="text-xs font-semibold text-gray-500 uppercase mb-2">
          {mode === 'select' ? 'Select Tags' : 'All Tags'}
        </div>
        <div className="flex flex-wrap gap-2">
          {tags.length === 0 ? (
            <div className="text-sm text-gray-500">No tags yet</div>
          ) : (
            tags.map((tag) => {
              const isSelected = mode === 'select' ? selectedTags.includes(tag.id) : false
              const isConversationTag = conversationTags?.some((ct) => ct.id === tag.id)

              return (
                <div
                  key={tag.id}
                  className={`inline-flex items-center gap-1 px-2 py-1 rounded text-sm border ${
                    isSelected || isConversationTag
                      ? 'border-transparent text-white'
                      : 'border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300'
                  }`}
                  style={{
                    backgroundColor: isSelected || isConversationTag ? tag.color : 'transparent',
                  }}
                >
                  {mode === 'select' ? (
                    <button
                      onClick={() => handleToggleTag(tag.id)}
                      className="flex items-center gap-1"
                    >
                      <span>{tag.name}</span>
                    </button>
                  ) : (
                    <>
                      <span
                        className="w-2 h-2 rounded-full"
                        style={{ backgroundColor: tag.color }}
                      />
                      <span>{tag.name}</span>
                      <button
                        onClick={() => handleDeleteTag(tag.id)}
                        className="ml-1 text-xs hover:text-red-500"
                        title="Delete tag"
                      >
                        ×
                      </button>
                    </>
                  )}
                </div>
              )
            })
          )}
        </div>
      </div>

      {/* Create Tag Form */}
      {mode === 'manage' && (
        <div className="border-t pt-4">
          {showCreateForm ? (
            <form onSubmit={handleCreateTag} className="space-y-3">
              <input
                type="text"
                value={newTagName}
                onChange={(e) => setNewTagName(e.target.value)}
                placeholder="Tag name"
                className="w-full px-3 py-2 bg-[var(--bg-primary)] border border-[var(--border)] rounded text-sm"
                autoFocus
              />
              <div className="flex gap-2 flex-wrap">
                {PRESET_COLORS.map((color) => (
                  <button
                    key={color}
                    type="button"
                    onClick={() => setNewTagColor(color)}
                    className={`w-6 h-6 rounded-full border-2 ${
                      newTagColor === color ? 'border-white ring-2 ring-blue-500' : 'border-transparent'
                    }`}
                    style={{ backgroundColor: color }}
                    title={color}
                  />
                ))}
              </div>
              <div className="flex gap-2">
                <button
                  type="submit"
                  className="px-3 py-1.5 bg-blue-500 hover:bg-blue-600 text-white rounded text-sm"
                >
                  Create Tag
                </button>
                <button
                  type="button"
                  onClick={() => setShowCreateForm(false)}
                  className="px-3 py-1.5 bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 rounded text-sm"
                >
                  Cancel
                </button>
              </div>
            </form>
          ) : (
            <button
              onClick={() => setShowCreateForm(true)}
              className="w-full px-3 py-2 bg-[var(--bg-primary)] hover:bg-[var(--bg-secondary)] border border-[var(--border)] rounded text-sm"
            >
              + Create New Tag
            </button>
          )}
        </div>
      )}

      {/* Conversation Tags (for select mode) */}
      {mode === 'select' && conversationTags && conversationTags.length > 0 && (
        <div className="border-t pt-4">
          <div className="text-xs font-semibold text-gray-500 uppercase mb-2">
            Current Tags
          </div>
          <div className="flex flex-wrap gap-2">
            {conversationTags.map((tag) => (
              <div
                key={tag.id}
                className="inline-flex items-center gap-1 px-2 py-1 rounded text-sm text-white"
                style={{ backgroundColor: tag.color }}
              >
                <span>{tag.name}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
