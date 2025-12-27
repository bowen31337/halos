import { useConversationStore, type Conversation } from '../stores/conversationStore'
import { useUIStore } from '../stores/uiStore'
import { useNavigate, useParams } from 'react-router-dom'
import { useState, useEffect } from 'react'

export function Sidebar() {
  const {
    conversations,
    currentConversationId,
    setCurrentConversation,
    loadConversations,
    createConversation,
    removeConversation,
    updateConversationTitle,
    updateConversation,
    archiveConversation,
    unarchiveConversation,
  } = useConversationStore()

  const { setSidebarOpen } = useUIStore()
  const navigate = useNavigate()
  const { conversationId } = useParams()
  const [isCreating, setIsCreating] = useState(false)
  const [deletingId, setDeletingId] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [duplicatingId, setDuplicatingId] = useState<string | null>(null)
  const [archivingId, setArchivingId] = useState<string | null>(null)
  const [showArchived, setShowArchived] = useState(false)

  const handleArchive = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation()
    setArchivingId(id)
    try {
      await archiveConversation(id)
      // If archiving the current conversation, navigate away
      if (currentConversationId === id) {
        setCurrentConversation(null)
        navigate('/')
      }
    } catch (error) {
      console.error('Failed to archive conversation:', error)
    } finally {
      setArchivingId(null)
    }
  }

  const handleUnarchive = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation()
    setArchivingId(id)
    try {
      await unarchiveConversation(id)
    } catch (error) {
      console.error('Failed to unarchive conversation:', error)
    } finally {
      setArchivingId(null)
    }
  }

  // Sync URL param with store
  useEffect(() => {
    if (conversationId) {
      setCurrentConversation(conversationId)
    }
  }, [conversationId, setCurrentConversation])

  // Load conversations from API on mount
  useEffect(() => {
    loadConversations()
  }, [loadConversations])

  const handleNewConversation = async () => {
    setIsCreating(true)
    try {
      const newConv = await createConversation('New Conversation')
      setCurrentConversation(newConv.id)
      navigate(`/c/${newConv.id}`)
    } catch (error) {
      console.error('Failed to create conversation:', error)
    } finally {
      setIsCreating(false)
    }
  }

  const handleSelectConversation = (conv: Conversation) => {
    setCurrentConversation(conv.id)
    navigate(`/c/${conv.id}`)
    // Close sidebar on mobile
    if (window.innerWidth < 768) {
      setSidebarOpen(false)
    }
  }

  const handleDelete = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation()
    if (!confirm('Delete this conversation?')) return

    setDeletingId(id)
    try {
      await removeConversation(id)
      if (currentConversationId === id) {
        setCurrentConversation(null)
        navigate('/')
      }
    } catch (error) {
      console.error('Failed to delete conversation:', error)
    } finally {
      setDeletingId(null)
    }
  }

  const handleRename = async (id: string, newTitle: string) => {
    if (!newTitle.trim()) return

    try {
      await updateConversationTitle(id, newTitle)
    } catch (error) {
      console.error('Failed to rename conversation:', error)
    }
  }

  const handlePin = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation()
    try {
      const conv = conversations.find(c => c.id === id)
      if (conv) {
        await updateConversation(id, { isPinned: !conv.isPinned })
      }
    } catch (error) {
      console.error('Failed to pin conversation:', error)
    }
  }

  const handleDuplicate = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation()
    setDuplicatingId(id)
    try {
      const response = await fetch(`/api/conversations/${id}/duplicate`, {
        method: 'POST',
      })
      if (response.ok) {
        const apiDuplicate = await response.json()
        // Transform API response to frontend format
        const duplicate = {
          id: apiDuplicate.id,
          title: apiDuplicate.title,
          model: apiDuplicate.model,
          projectId: apiDuplicate.project_id,
          isArchived: apiDuplicate.is_archived,
          isPinned: apiDuplicate.is_pinned,
          messageCount: apiDuplicate.message_count,
          createdAt: apiDuplicate.created_at,
          updatedAt: apiDuplicate.updated_at,
        }
        // Add to local state
        const { addConversation } = useConversationStore.getState()
        addConversation(duplicate)
      }
    } catch (error) {
      console.error('Failed to duplicate conversation:', error)
    } finally {
      setDuplicatingId(null)
    }
  }

  // Group conversations by date
  const groupByDate = (conversations: Conversation[]) => {
    const now = new Date()
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
    const yesterday = new Date(today)
    yesterday.setDate(yesterday.getDate() - 1)

    const groups: { [key: string]: Conversation[] } = {
      Today: [],
      Yesterday: [],
      Previous: [],
    }

    conversations.forEach((conv) => {
      const convDate = new Date(conv.createdAt)
      const convDay = new Date(convDate.getFullYear(), convDate.getMonth(), convDate.getDate())

      if (convDay.getTime() === today.getTime()) {
        groups.Today.push(conv)
      } else if (convDay.getTime() === yesterday.getTime()) {
        groups.Yesterday.push(conv)
      } else {
        groups.Previous.push(conv)
      }
    })

    return groups
  }

  // Filter conversations by search query and archive status
  const filteredConversations = conversations.filter(conv => {
    // Filter by archive status
    if (showArchived && !conv.isArchived) return false
    if (!showArchived && conv.isArchived) return false

    // Filter by search query
    if (!searchQuery.trim()) return true
    const query = searchQuery.toLowerCase()
    return conv.title.toLowerCase().includes(query)
  })

  // Sort pinned conversations first
  const sortedConversations = [...filteredConversations].sort((a, b) => {
    if (a.isPinned && !b.isPinned) return -1
    if (!a.isPinned && b.isPinned) return 1
    return 0
  })

  const grouped = groupByDate(sortedConversations)

  return (
    <div className="flex flex-col h-full bg-[var(--bg-secondary)] border-r border-[var(--border)]">
      {/* Header */}
      <div className="p-4 border-b border-[var(--border)] space-y-3">
        <button
          onClick={handleNewConversation}
          disabled={isCreating}
          className="w-full px-4 py-3 bg-[var(--primary)] hover:bg-[var(--primary-hover)] active:bg-[var(--primary-active)] text-white rounded-lg font-medium transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
        >
          <span>+</span>
          <span>{isCreating ? 'Creating...' : 'New Chat'}</span>
        </button>

        {/* Search input */}
        <div className="relative">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search conversations..."
            className="w-full px-3 py-2 pl-9 bg-[var(--bg-primary)] border border-[var(--border)] rounded-lg text-sm text-[var(--text-primary)] placeholder-[var(--text-secondary)] focus:outline-none focus:ring-2 focus:ring-[var(--primary)]"
          />
          <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--text-secondary)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
        </div>

        {/* Archive toggle */}
        <div className="flex items-center gap-2 text-xs text-[var(--text-secondary)]">
          <button
            onClick={() => setShowArchived(!showArchived)}
            className={`flex items-center gap-2 px-3 py-2 rounded-lg ${
              showArchived
                ? 'bg-[var(--primary)] text-white'
                : 'bg-[var(--bg-primary)] hover:bg-[var(--bg-secondary)]'
            }`}
          >
            <span>📦</span>
            <span>{showArchived ? 'Hide' : 'Show'} Archived</span>
          </button>
        </div>
      </div>

      {/* Conversation List */}
      <div className="flex-1 overflow-y-auto p-2 space-y-1">
        {conversations.length === 0 ? (
          <div className="text-center p-8 text-[var(--text-secondary)] text-sm">
            No conversations yet
          </div>
        ) : (
          <>
            {grouped.Today.length > 0 && (
              <div className="px-2 py-1 text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wider">
                Today
              </div>
            )}
            {grouped.Today.map((conv) => (
              <ConversationItem
                key={conv.id}
                conv={conv}
                isSelected={currentConversationId === conv.id}
                onSelect={() => handleSelectConversation(conv)}
                onDelete={(e) => handleDelete(e, conv.id)}
                onRename={(newTitle) => handleRename(conv.id, newTitle)}
                onPin={(e) => handlePin(e, conv.id)}
                onDuplicate={(e) => handleDuplicate(e, conv.id)}
                onArchive={(e) => handleArchive(e, conv.id)}
                onUnarchive={(e) => handleUnarchive(e, conv.id)}
                isDeleting={deletingId === conv.id}
                isDuplicating={duplicatingId === conv.id}
                isArchiving={archivingId === conv.id}
              />
            ))}

            {grouped.Yesterday.length > 0 && (
              <div className="px-2 py-1 mt-2 text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wider">
                Yesterday
              </div>
            )}
            {grouped.Yesterday.map((conv) => (
              <ConversationItem
                key={conv.id}
                conv={conv}
                isSelected={currentConversationId === conv.id}
                onSelect={() => handleSelectConversation(conv)}
                onDelete={(e) => handleDelete(e, conv.id)}
                onRename={(newTitle) => handleRename(conv.id, newTitle)}
                onPin={(e) => handlePin(e, conv.id)}
                onDuplicate={(e) => handleDuplicate(e, conv.id)}
                onArchive={(e) => handleArchive(e, conv.id)}
                onUnarchive={(e) => handleUnarchive(e, conv.id)}
                isDeleting={deletingId === conv.id}
                isDuplicating={duplicatingId === conv.id}
                isArchiving={archivingId === conv.id}
              />
            ))}

            {grouped.Previous.length > 0 && (
              <div className="px-2 py-1 mt-2 text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wider">
                Previous
              </div>
            )}
            {grouped.Previous.map((conv) => (
              <ConversationItem
                key={conv.id}
                conv={conv}
                isSelected={currentConversationId === conv.id}
                onSelect={() => handleSelectConversation(conv)}
                onDelete={(e) => handleDelete(e, conv.id)}
                onRename={(newTitle) => handleRename(conv.id, newTitle)}
                onPin={(e) => handlePin(e, conv.id)}
                onDuplicate={(e) => handleDuplicate(e, conv.id)}
                onArchive={(e) => handleArchive(e, conv.id)}
                onUnarchive={(e) => handleUnarchive(e, conv.id)}
                isDeleting={deletingId === conv.id}
                isDuplicating={duplicatingId === conv.id}
                isArchiving={archivingId === conv.id}
              />
            ))}
          </>
        )}
      </div>

      {/* Footer */}
      <div className="p-3 border-t border-[var(--border)] text-xs text-[var(--text-secondary)] flex justify-between items-center">
        <span>{conversations.length} conversations</span>
        <button
          onClick={() => setSidebarOpen(false)}
          className="md:hidden px-2 py-1 bg-[var(--bg-primary)] rounded hover:bg-[var(--border)]"
        >
          Close
        </button>
      </div>
    </div>
  )
}

interface ConversationItemProps {
  conv: Conversation
  isSelected: boolean
  onSelect: () => void
  onDelete: (e: React.MouseEvent) => void
  onRename: (newTitle: string) => Promise<void>
  onPin: (e: React.MouseEvent) => void
  onDuplicate: (e: React.MouseEvent) => void
  onArchive: (e: React.MouseEvent) => void
  onUnarchive: (e: React.MouseEvent) => void
  isDeleting: boolean
  isDuplicating: boolean
  isArchiving: boolean
}

function ConversationItem({
  conv,
  isSelected,
  onSelect,
  onDelete,
  onRename,
  onPin,
  onDuplicate,
  onArchive,
  onUnarchive,
  isDeleting,
  isDuplicating,
  isArchiving,
}: ConversationItemProps) {
  const [showActions, setShowActions] = useState(false)
  const [isEditing, setIsEditing] = useState(false)
  const [editTitle, setEditTitle] = useState(conv.title)

  const handleStartEdit = (e: React.MouseEvent) => {
    e.stopPropagation()
    setIsEditing(true)
    setEditTitle(conv.title)
  }

  const handleSubmitEdit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (editTitle.trim() && editTitle !== conv.title) {
      await onRename(editTitle)
    }
    setIsEditing(false)
  }

  const handleCancelEdit = () => {
    setIsEditing(false)
    setEditTitle(conv.title)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSubmitEdit(e)
    } else if (e.key === 'Escape') {
      handleCancelEdit()
    }
  }

  return (
    <div
      className={`group relative flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer transition-colors ${
        isSelected
          ? 'bg-[var(--primary)] text-white'
          : 'hover:bg-[var(--bg-primary)] text-[var(--text-primary)]'
      } ${isDeleting ? 'opacity-50' : ''}`}
      onClick={!isEditing ? onSelect : undefined}
      onMouseEnter={() => setShowActions(true)}
      onMouseLeave={() => {
        setShowActions(false)
        if (isEditing) {
          handleCancelEdit()
        }
      }}
    >
      {isEditing ? (
        <form
          onSubmit={handleSubmitEdit}
          className="flex-1 flex items-center gap-2"
          onClick={(e) => e.stopPropagation()}
        >
          <input
            type="text"
            value={editTitle}
            onChange={(e) => setEditTitle(e.target.value)}
            onKeyDown={handleKeyDown}
            onBlur={handleSubmitEdit}
            className={`flex-1 px-2 py-1 text-sm rounded ${
              isSelected
                ? 'bg-white/20 text-white placeholder-white/70'
                : 'bg-[var(--bg-primary)] text-[var(--text-primary)]'
            }`}
            autoFocus
            onFocus={(e) => e.target.select()}
          />
          <button
            type="button"
            onClick={handleCancelEdit}
            className={`p-1 rounded text-xs ${
              isSelected ? 'hover:bg-white/20' : 'hover:bg-[var(--bg-secondary)]'
            }`}
          >
            ✕
          </button>
        </form>
      ) : (
        <>
          <span className="flex-1 truncate text-sm">
            {conv.title || 'Untitled'}
          </span>

          {/* Actions - show on hover or when selected */}
          {(showActions || isSelected) && !isDeleting && !isDuplicating && !isArchiving && (
            <div className="flex gap-1">
              <button
                onClick={handleStartEdit}
                title="Rename"
                className={`p-1 rounded hover:bg-[var(--bg-secondary)] ${
                  isSelected ? 'hover:bg-white/20' : ''
                }`}
              >
                ✏️
              </button>
              <button
                onClick={onPin}
                title={conv.isPinned ? 'Unpin' : 'Pin'}
                className={`p-1 rounded hover:bg-[var(--bg-secondary)] ${
                  isSelected ? 'hover:bg-white/20' : ''
                }`}
              >
                {conv.isPinned ? '📌' : '📍'}
              </button>
              <button
                onClick={onDuplicate}
                title="Duplicate"
                className={`p-1 rounded hover:bg-[var(--bg-secondary)] ${
                  isSelected ? 'hover:bg-white/20' : ''
                }`}
              >
                📋
              </button>
              {conv.isArchived ? (
                <button
                  onClick={onUnarchive}
                  title="Unarchive"
                  className={`p-1 rounded hover:bg-[var(--bg-secondary)] ${
                    isSelected ? 'hover:bg-white/20' : ''
                  }`}
                >
                  📥
                </button>
              ) : (
                <button
                  onClick={onArchive}
                  title="Archive"
                  className={`p-1 rounded hover:bg-[var(--bg-secondary)] ${
                    isSelected ? 'hover:bg-white/20' : ''
                  }`}
                >
                  📦
                </button>
              )}
              <button
                onClick={onDelete}
                title="Delete"
                className={`p-1 rounded hover:bg-[var(--bg-secondary)] ${
                  isSelected ? 'hover:bg-white/20' : ''
                }`}
              >
                🗑️
              </button>
            </div>
          )}

          {isDeleting && (
            <span className="text-xs">Deleting...</span>
          )}

          {isDuplicating && (
            <span className="text-xs">Duplicating...</span>
          )}

          {isArchiving && (
            <span className="text-xs">Archiving...</span>
          )}
        </>
      )}
    </div>
  )
}
