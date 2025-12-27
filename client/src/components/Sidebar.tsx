import { useConversationStore, type Conversation } from '../stores/conversationStore'
import { useUIStore } from '../stores/uiStore'
import { useProjectStore } from '../stores/projectStore'
import { useNavigate, useParams } from 'react-router-dom'
import { useState, useEffect } from 'react'
import { api } from '../services/api'
import { ProjectSelector } from './ProjectSelector'
import type { Project } from '../stores/projectStore'

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
  const { projects, fetchProjects } = useProjectStore()
  const navigate = useNavigate()
  const { conversationId } = useParams()
  const [isCreating, setIsCreating] = useState(false)
  const [deletingId, setDeletingId] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [duplicatingId, setDuplicatingId] = useState<string | null>(null)
  const [archivingId, setArchivingId] = useState<string | null>(null)
  const [exportingId, setExportingId] = useState<string | null>(null)
  const [movingId, setMovingId] = useState<string | null>(null)
  const [showArchived, setShowArchived] = useState(false)
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null)
  const [showMoveModal, setShowMoveModal] = useState<string | null>(null)

  const handleArchive = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation()
    setArchivingId(id)
    try {
      await archiveConversation(id)
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

  useEffect(() => {
    if (conversationId) {
      setCurrentConversation(conversationId)
    }
  }, [conversationId, setCurrentConversation])

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
        const { addConversation } = useConversationStore.getState()
        addConversation(duplicate)
      }
    } catch (error) {
      console.error('Failed to duplicate conversation:', error)
    } finally {
      setDuplicatingId(null)
    }
  }

  const handleExport = async (e: React.MouseEvent, id: string, format: 'json' | 'markdown') => {
    e.stopPropagation()
    setExportingId(id)
    try {
      const blob = await api.exportConversation(id, format)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      const conv = conversations.find(c => c.id === id)
      const filename = `${conv?.title.replace(/[^a-z0-9]/gi, '_') || 'conversation'}_export.${format}`
      a.download = filename
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    } catch (error) {
      console.error('Failed to export conversation:', error)
    } finally {
      setExportingId(null)
    }
  }

  const handleMove = async (e: React.MouseEvent, id: string, projectId: string | null) => {
    e.stopPropagation()
    setMovingId(id)
    try {
      const updated = await api.moveConversation(id, projectId)
      updateConversation(id, { projectId: updated.project_id })
      if (currentConversationId === id) {
        const currentConv = conversations.find(c => c.id === id)
        if (currentConv) {
          const newProjectId = updated.project_id
          const shouldNavigateAway = selectedProjectId !== null && selectedProjectId !== newProjectId
          if (shouldNavigateAway) {
            setCurrentConversation(null)
            navigate('/')
          }
        }
      }
    } catch (error) {
      console.error('Failed to move conversation:', error)
    } finally {
      setMovingId(null)
      setShowMoveModal(null)
    }
  }

  useEffect(() => {
    fetchProjects()
  }, [fetchProjects])

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

  const filteredConversations = conversations.filter(conv => {
    if (showArchived && !conv.isArchived) return false
    if (!showArchived && conv.isArchived) return false
    if (selectedProjectId && conv.projectId !== selectedProjectId) return false
    if (!searchQuery.trim()) return true
    const query = searchQuery.toLowerCase()
    return conv.title.toLowerCase().includes(query)
  })

  const sortedConversations = [...filteredConversations].sort((a, b) => {
    if (a.isPinned && !b.isPinned) return -1
    if (!a.isPinned && b.isPinned) return 1
    return 0
  })

  const grouped = groupByDate(sortedConversations)

  return (
    <div className="flex flex-col h-full bg-[var(--bg-secondary)] border-r border-[var(--border)]">
      <div className="p-4 border-b border-[var(--border)] space-y-3">
        <button
          onClick={handleNewConversation}
          disabled={isCreating}
          className="w-full px-4 py-3 bg-[var(--primary)] hover:bg-[var(--primary-hover)] active:bg-[var(--primary-active)] text-white rounded-lg font-medium transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
        >
          <span>+</span>
          <span>{isCreating ? 'Creating...' : 'New Chat'}</span>
        </button>

        <ProjectSelector
          selectedProjectId={selectedProjectId}
          onProjectChange={setSelectedProjectId}
        />

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
                onExport={(e, format) => handleExport(e, conv.id, format)}
                onMove={() => setShowMoveModal(conv.id)}
                isDeleting={deletingId === conv.id}
                isDuplicating={duplicatingId === conv.id}
                isArchiving={archivingId === conv.id}
                isExporting={exportingId === conv.id}
                isMoving={movingId === conv.id}
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
                onExport={(e, format) => handleExport(e, conv.id, format)}
                onMove={() => setShowMoveModal(conv.id)}
                isDeleting={deletingId === conv.id}
                isDuplicating={duplicatingId === conv.id}
                isArchiving={archivingId === conv.id}
                isExporting={exportingId === conv.id}
                isMoving={movingId === conv.id}
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
                onExport={(e, format) => handleExport(e, conv.id, format)}
                onMove={() => setShowMoveModal(conv.id)}
                isDeleting={deletingId === conv.id}
                isDuplicating={duplicatingId === conv.id}
                isArchiving={archivingId === conv.id}
                isExporting={exportingId === conv.id}
                isMoving={movingId === conv.id}
              />
            ))}
          </>
        )}
      </div>

      {showMoveModal && (
        <MoveModal
          conversationId={showMoveModal}
          projects={projects}
          currentProjectId={conversations.find(c => c.id === showMoveModal)?.projectId || null}
          onMove={handleMove}
          onClose={() => setShowMoveModal(null)}
        />
      )}

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
  onExport: (e: React.MouseEvent, format: 'json' | 'markdown') => void
  onMove: () => void
  isDeleting: boolean
  isDuplicating: boolean
  isArchiving: boolean
  isExporting: boolean
  isMoving: boolean
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
  onExport,
  onMove,
  isDeleting,
  isDuplicating,
  isArchiving,
  isExporting,
  isMoving,
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

          {(showActions || isSelected) && !isDeleting && !isDuplicating && !isArchiving && !isExporting && !isMoving && (
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
                onClick={(e) => onExport(e, 'json')}
                title="Export as JSON"
                className={`p-1 rounded hover:bg-[var(--bg-secondary)] ${
                  isSelected ? 'hover:bg-white/20' : ''
                }`}
              >
                📄
              </button>
              <button
                onClick={(e) => onExport(e, 'markdown')}
                title="Export as Markdown"
                className={`p-1 rounded hover:bg-[var(--bg-secondary)] ${
                  isSelected ? 'hover:bg-white/20' : ''
                }`}
              >
                📝
              </button>
              <button
                onClick={onMove}
                title="Move to Project"
                className={`p-1 rounded hover:bg-[var(--bg-secondary)] ${
                  isSelected ? 'hover:bg-white/20' : ''
                }`}
              >
                📁
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

          {isDeleting && <span className="text-xs">Deleting...</span>}
          {isDuplicating && <span className="text-xs">Duplicating...</span>}
          {isArchiving && <span className="text-xs">Archiving...</span>}
          {isExporting && <span className="text-xs">Exporting...</span>}
          {isMoving && <span className="text-xs">Moving...</span>}
        </>
      )}
    </div>
  )
}

interface MoveModalProps {
  conversationId: string
  projects: Project[]
  currentProjectId: string | null
  onMove: (e: React.MouseEvent, id: string, projectId: string | null) => void
  onClose: () => void
}

function MoveModal({ conversationId, projects, currentProjectId, onMove, onClose }: MoveModalProps) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-[var(--bg-primary)] rounded-xl shadow-2xl w-full max-w-md mx-4 overflow-hidden">
        <div className="px-6 py-4 border-b border-[var(--border)] flex items-center justify-between">
          <h2 className="text-xl font-semibold text-[var(--text-primary)]">
            Move Conversation
          </h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-[var(--surface-elevated)] rounded-lg transition-colors"
          >
            <svg className="w-5 h-5 text-[var(--text-secondary)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="p-6 space-y-4 max-h-[60vh] overflow-y-auto">
          <p className="text-sm text-[var(--text-secondary)]">
            Select a project to move this conversation to:
          </p>

          <button
            onClick={(e) => onMove(e, conversationId, null)}
            className={`w-full px-4 py-3 text-left rounded-lg border transition-colors ${
              currentProjectId === null
                ? 'border-[var(--primary)] bg-[var(--surface-elevated)]'
                : 'border-[var(--border)] hover:border-[var(--primary)]'
            }`}
          >
            <div className="flex items-center gap-3">
              <span className="text-lg">📋</span>
              <div className="flex-1">
                <div className="font-medium">All Conversations</div>
                <div className="text-xs text-[var(--text-secondary)]">No project filter</div>
              </div>
              {currentProjectId === null && (
                <span className="text-xs text-[var(--primary)] font-medium">Current</span>
              )}
            </div>
          </button>

          {projects.length === 0 ? (
            <div className="px-3 py-4 text-sm text-[var(--text-secondary)] text-center">
              No projects available. Create a project first.
            </div>
          ) : (
            projects.map((project) => (
              <button
                key={project.id}
                onClick={(e) => onMove(e, conversationId, project.id)}
                className={`w-full px-4 py-3 text-left rounded-lg border transition-colors ${
                  currentProjectId === project.id
                    ? 'border-[var(--primary)] bg-[var(--surface-elevated)]'
                    : 'border-[var(--border)] hover:border-[var(--primary)]'
                }`}
              >
                <div className="flex items-center gap-3">
                  <span className="text-lg" style={{ color: project.color }}>
                    {project.icon || '📁'}
                  </span>
                  <div className="flex-1">
                    <div className="font-medium">{project.name}</div>
                    {project.description && (
                      <div className="text-xs text-[var(--text-secondary)]">{project.description}</div>
                    )}
                  </div>
                  {currentProjectId === project.id && (
                    <span className="text-xs text-[var(--primary)] font-medium">Current</span>
                  )}
                </div>
              </button>
            ))
          )}
        </div>

        <div className="px-6 py-4 border-t border-[var(--border)] flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-[var(--text-primary)] hover:bg-[var(--surface-elevated)] rounded-lg transition-colors"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  )
}
