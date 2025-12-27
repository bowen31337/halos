import { useConversationStore, type Conversation } from '../stores/conversationStore'
import { useUIStore } from '../stores/uiStore'
import { useNavigate, useParams } from 'react-router-dom'
import { useState, useEffect } from 'react'

export function Sidebar() {
  const {
    conversations,
    currentConversationId,
    setCurrentConversation,
    addConversation,
    deleteConversation,
    setConversations,
  } = useConversationStore()

  const { sidebarOpen, setSidebarOpen } = useUIStore()
  const navigate = useNavigate()
  const { conversationId } = useParams()
  const [isCreating, setIsCreating] = useState(false)
  const [deletingId, setDeletingId] = useState<string | null>(null)

  // Sync URL param with store
  useEffect(() => {
    if (conversationId) {
      setCurrentConversation(conversationId)
    }
  }, [conversationId, setCurrentConversation])

  // Load conversations from API on mount
  useEffect(() => {
    loadConversations()
  }, [])

  const loadConversations = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/conversations')
      if (response.ok) {
        const data = await response.json()
        setConversations(data)
      }
    } catch (error) {
      console.error('Failed to load conversations:', error)
    }
  }

  const handleNewConversation = async () => {
    setIsCreating(true)
    try {
      const response = await fetch('http://localhost:8000/api/conversations', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: 'New Conversation' }),
      })
      if (response.ok) {
        const newConv = await response.json()
        addConversation(newConv)
        setCurrentConversation(newConv.id)
        navigate(`/c/${newConv.id}`)
      }
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
      const response = await fetch(`http://localhost:8000/api/conversations/${id}`, {
        method: 'DELETE',
      })
      if (response.ok) {
        deleteConversation(id)
        if (currentConversationId === id) {
          setCurrentConversation(null)
          navigate('/')
        }
      }
    } catch (error) {
      console.error('Failed to delete conversation:', error)
    } finally {
      setDeletingId(null)
    }
  }

  const handleRename = async (id: string, currentTitle: string) => {
    const newTitle = prompt('Rename conversation:', currentTitle)
    if (!newTitle || newTitle === currentTitle) return

    try {
      const response = await fetch(`http://localhost:8000/api/conversations/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: newTitle }),
      })
      if (response.ok) {
        const updated = await response.json()
        // Update in store - need to add updateConversation method
        setConversations(conversations.map(c => c.id === id ? { ...c, title: newTitle } : c))
      }
    } catch (error) {
      console.error('Failed to rename conversation:', error)
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

  const grouped = groupByDate(conversations)

  return (
    <div className="flex flex-col h-full bg-[var(--bg-secondary)] border-r border-[var(--border)]">
      {/* Header */}
      <div className="p-4 border-b border-[var(--border)]">
        <button
          onClick={handleNewConversation}
          disabled={isCreating}
          className="w-full px-4 py-3 bg-[var(--primary)] hover:bg-[var(--primary-hover)] active:bg-[var(--primary-active)] text-white rounded-lg font-medium transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
        >
          <span>+</span>
          <span>{isCreating ? 'Creating...' : 'New Chat'}</span>
        </button>
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
                onRename={() => handleRename(conv.id, conv.title)}
                isDeleting={deletingId === conv.id}
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
                onRename={() => handleRename(conv.id, conv.title)}
                isDeleting={deletingId === conv.id}
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
                onRename={() => handleRename(conv.id, conv.title)}
                isDeleting={deletingId === conv.id}
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
  onRename: () => void
  isDeleting: boolean
}

function ConversationItem({
  conv,
  isSelected,
  onSelect,
  onDelete,
  onRename,
  isDeleting,
}: ConversationItemProps) {
  const [showActions, setShowActions] = useState(false)

  return (
    <div
      className={`group relative flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer transition-colors ${
        isSelected
          ? 'bg-[var(--primary)] text-white'
          : 'hover:bg-[var(--bg-primary)] text-[var(--text-primary)]'
      } ${isDeleting ? 'opacity-50' : ''}`}
      onClick={onSelect}
      onMouseEnter={() => setShowActions(true)}
      onMouseLeave={() => setShowActions(false)}
    >
      <span className="flex-1 truncate text-sm">
        {conv.title || 'Untitled'}
      </span>

      {/* Actions - show on hover or when selected */}
      {(showActions || isSelected) && !isDeleting && (
        <div className="flex gap-1">
          <button
            onClick={(e) => {
              e.stopPropagation()
              onRename()
            }}
            title="Rename"
            className={`p-1 rounded hover:bg-[var(--bg-secondary)] ${
              isSelected ? 'hover:bg-white/20' : ''
            }`}
          >
            ✏️
          </button>
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
    </div>
  )
}
