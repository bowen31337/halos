import { useConversationStore, type Conversation } from '../stores/conversationStore'
import { useUIStore } from '../stores/uiStore'
import { useProjectStore } from '../stores/projectStore'
import { useNavigate, useParams } from 'react-router-dom'
import { useState, useEffect } from 'react'
import { api } from '../services/api'
import { ProjectSelector } from './ProjectSelector'
import type { Project } from '../stores/projectStore'
import { useContextMenu, createConversationMenuItems } from './ContextMenu'
import { useToast } from './ToastManager'

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
    markConversationRead,
  } = useConversationStore()

  const {
    setSidebarOpen,
    batchSelectMode,
    setBatchSelectMode,
    selectedConversationIds,
    toggleConversationSelection,
    clearSelection,
    selectAllConversations
  } = useUIStore()
  const { projects, fetchProjects } = useProjectStore()
  const navigate = useNavigate()
  const { conversationId } = useParams()
  const { showSuccess, showError } = useToast()

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
  const [selectedTagIds, setSelectedTagIds] = useState<string[]>([])
  const [availableTags, setAvailableTags] = useState<Tag[]>([])

  // Batch selection state (using UI store for shared state)
  const [batchProgress, setBatchProgress] = useState<{ total: number; completed: number; operation: string } | null>(null)
  const [showBatchMoveModal, setShowBatchMoveModal] = useState(false)

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

  // Load available tags
  useEffect(() => {
    const loadTags = async () => {
      try {
        const response = await fetch('/api/tags')
        if (response.ok) {
          const tags = await response.json()
          setAvailableTags(tags)
        }
      } catch (error) {
        console.error('Failed to load tags:', error)
      }
    }
    loadTags()
  }, [])

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

  const handleTagFilter = (tagId: string) => {
    setSelectedTagIds(prev =>
      prev.includes(tagId)
        ? prev.filter(id => id !== tagId)
        : [...prev, tagId]
    )
  }

  const handleClearTagFilter = () => {
    setSelectedTagIds([])
  }

  const handleSelectConversation = (conv: Conversation) => {
    // If in batch mode, toggle selection instead
    if (batchSelectMode) {
      toggleConversationSelection(conv.id)
      return
    }

    setCurrentConversation(conv.id)
    navigate(`/c/${conv.id}`)
    if (window.innerWidth < 768) {
      setSidebarOpen(false)
    }

    // Mark conversation as read when selected
    const markAsRead = async () => {
      try {
        const response = await fetch(`/api/conversations/${conv.id}/mark-read`, {
          method: 'POST',
        })
        if (response.ok) {
          // Update the conversation in the store
          updateConversation(conv.id, { unreadCount: 0 })
        }
      } catch (error) {
        console.error('Failed to mark conversation as read:', error)
      }
    }
    markAsRead()
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

  // ==================== BATCH OPERATIONS ====================

  const toggleBatchMode = () => {
    setBatchSelectMode(!batchSelectMode)
    clearSelection()
  }

  const selectAllVisible = () => {
    const visibleIds = filteredConversations.map(c => c.id)
    const allSelected = visibleIds.every(id => selectedConversationIds.includes(id))
    if (allSelected) {
      clearSelection()
    } else {
      selectAllConversations(visibleIds)
    }
  }

  const handleBatchExport = async (format: 'json' | 'markdown') => {
    if (selectedConversationIds.length === 0) return

    setBatchProgress({ total: selectedConversationIds.length, completed: 0, operation: 'Exporting' })
    setBatchAction('export')
    try {
      const blob = await api.batchExportConversations(selectedConversationIds, format)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `batch_export_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.${format}`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
      showSuccess('Batch Export Complete', `Successfully exported ${selectedConversationIds.length} conversations`)
    } catch (error) {
      console.error('Batch export failed:', error)
      showError('Batch Export Failed', 'An error occurred during batch export')
    } finally {
      setBatchProgress(null)
      setBatchAction(null)
      setBatchSelectMode(false)
      clearSelection()
    }
  }

  const handleBatchDelete = async () => {
    if (selectedConversationIds.length === 0) return
    if (!confirm(`Delete ${selectedConversationIds.length} conversations? This cannot be undone.`)) return

    setBatchProgress({ total: selectedConversationIds.length, completed: 0, operation: 'Deleting' })
    setBatchAction('delete')
    try {
      const result = await api.batchDeleteConversations(selectedConversationIds)

      // Update store
      for (const id of selectedConversationIds) {
        removeConversation(id)
      }

      // Clear selection if current conversation was deleted
      if (selectedConversationIds.includes(currentConversationId || '')) {
        setCurrentConversation(null)
        navigate('/')
      }

      showSuccess(
        'Batch Delete Complete',
        `Deleted ${result.success_count} conversations${result.failure_count > 0 ? ` (${result.failure_count} failed)` : ''}`
      )
    } catch (error) {
      console.error('Batch delete failed:', error)
      showError('Batch Delete Failed', 'An error occurred during batch delete')
    } finally {
      setBatchProgress(null)
      setBatchAction(null)
      setBatchSelectMode(false)
      clearSelection()
    }
  }

  const handleBatchArchive = async () => {
    if (selectedConversationIds.length === 0) return

    setBatchProgress({ total: selectedConversationIds.length, completed: 0, operation: 'Archiving' })
    setBatchAction('archive')
    try {
      const result = await api.batchArchiveConversations(selectedConversationIds)

      // Update store
      for (const id of selectedConversationIds) {
        archiveConversation(id)
      }

      showSuccess(
        'Batch Archive Complete',
        `Archived ${result.success_count} conversations${result.failure_count > 0 ? ` (${result.failure_count} failed)` : ''}`
      )
    } catch (error) {
      console.error('Batch archive failed:', error)
      showError('Batch Archive Failed', 'An error occurred during batch archive')
    } finally {
      setBatchProgress(null)
      setBatchAction(null)
      setBatchSelectMode(false)
      clearSelection()
    }
  }

  const handleBatchDuplicate = async () => {
    if (selectedConversationIds.length === 0) return

    setBatchProgress({ total: selectedConversationIds.length, completed: 0, operation: 'Duplicating' })
    setBatchAction('duplicate')
    try {
      const result = await api.batchDuplicateConversations(selectedConversationIds)

      // Add duplicates to store
      for (const item of result.results) {
        if (item.new_id) {
          const { addConversation } = useConversationStore.getState()
          addConversation({
            id: item.new_id,
            title: item.title,
            model: 'claude-sonnet-4-5-20250929',
            projectId: null,
            isArchived: false,
            isPinned: false,
            messageCount: 0,
            unreadCount: 0,
            tags: [],
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString(),
          })
        }
      }

      showSuccess(
        'Batch Duplicate Complete',
        `Duplicated ${result.success_count} conversations${result.failure_count > 0 ? ` (${result.failure_count} failed)` : ''}`
      )
    } catch (error) {
      console.error('Batch duplicate failed:', error)
      showError('Batch Duplicate Failed', 'An error occurred during batch duplicate')
    } finally {
      setBatchProgress(null)
      setBatchAction(null)
      setBatchSelectMode(false)
      clearSelection()
    }
  }

  const handleBatchMove = async (projectId: string | null) => {
    if (selectedConversationIds.length === 0) return

    setBatchProgress({ total: selectedConversationIds.length, completed: 0, operation: 'Moving' })
    setBatchAction('move')
    try {
      const result = await api.batchMoveConversations(selectedConversationIds, projectId)

      // Update store
      for (const item of result.results) {
        if (item.conversation_id) {
          updateConversation(item.conversation_id, { projectId })
        }
      }

      showSuccess(
        'Batch Move Complete',
        `Moved ${result.success_count} conversations${result.failure_count > 0 ? ` (${result.failure_count} failed)` : ''}`
      )
    } catch (error) {
      console.error('Batch move failed:', error)
      showError('Batch Move Failed', 'An error occurred during batch move')
    } finally {
      setBatchProgress(null)
      setBatchAction(null)
      setBatchSelectMode(false)
      clearSelection()
      setShowBatchMoveModal(false)
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

    // Filter by tags - must have ALL selected tags
    if (selectedTagIds.length > 0) {
      const convTagIds = conv.tags?.map(tag => tag.id) || []
      const hasAllSelectedTags = selectedTagIds.every(tagId => convTagIds.includes(tagId))
      if (!hasAllSelectedTags) return false
    }

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
    <div className="flex flex-col h-full bg-[var(--bg-secondary)] border-r border-[var(--border)]" role="navigation" aria-label="Conversation sidebar">
      <div className="p-4 border-b border-[var(--border)] space-y-3">
        <button
          aria-label="New conversation"
          tabIndex={0}
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

        {/* Tags filter section */}
        {availableTags.length > 0 && (
          <div className="space-y-2">
            <div className="flex items-center justify-between text-xs text-[var(--text-secondary)]">
              <span>Filter by tags:</span>
              {selectedTagIds.length > 0 && (
                <button
                  onClick={handleClearTagFilter}
                  className="text-[var(--primary)] hover:text-[var(--primary-hover)]"
                >
                  Clear
                </button>
              )}
            </div>
            <div className="flex flex-wrap gap-1 max-h-20 overflow-y-auto">
              {availableTags.map((tag) => (
                <button
                  key={tag.id}
                  onClick={() => handleTagFilter(tag.id)}
                  className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border transition-colors ${
                    selectedTagIds.includes(tag.id)
                      ? `bg-[var(--primary)] text-white border-[var(--primary)]`
                      : `bg-[var(--bg-primary)] text-[var(--text-primary)] border-[var(--border)] hover:bg-[var(--bg-secondary)]`
                  }`}
                  style={selectedTagIds.includes(tag.id) ? {} : { borderColor: tag.color, color: tag.color }}
                >
                  {tag.name}
                  {selectedTagIds.includes(tag.id) && (
                    <span className="ml-1">✓</span>
                  )}
                </button>
              ))}
            </div>
          </div>
        )}

        <div className="flex items-center gap-2 text-xs text-[var(--text-secondary)]">
          <button
          aria-label="New conversation"
          tabIndex={0}
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
          <button
          aria-label="Toggle batch selection mode"
          tabIndex={0}
            onClick={toggleBatchMode}
            className={`flex items-center gap-2 px-3 py-2 rounded-lg ${
              batchSelectMode
                ? 'bg-[var(--primary)] text-white'
                : 'bg-[var(--bg-primary)] hover:bg-[var(--bg-secondary)]'
            }`}
          >
            <span>☑️</span>
            <span>{batchSelectMode ? 'Exit' : 'Batch'} Select</span>
          </button>
        </div>
      </div>

      {/* Batch actions toolbar - shown when items are selected */}
      {batchSelectMode && selectedConversationIds.length > 0 && (
        <div className="px-4 py-3 bg-[var(--surface-elevated)] border-b border-[var(--border)]">
          <div className="flex items-center justify-between mb-3">
            <span className="text-sm font-medium text-[var(--text-primary)]">
              {selectedConversationIds.length} conversation{selectedConversationIds.length !== 1 ? 's' : ''} selected
            </span>
            <button
              aria-label="Clear selection"
              tabIndex={0}
              onClick={clearSelection}
              className="text-xs text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors"
            >
              Clear all
            </button>
          </div>

          {/* Progress indicator */}
          {batchProgress && (
            <div className="mb-3 p-2 bg-[var(--bg-primary)] rounded-lg border border-[var(--border)]">
              <div className="flex items-center justify-between text-xs mb-1">
                <span className="text-[var(--text-secondary)]">
                  {batchProgress.operation}...
                </span>
                <span className="font-medium text-[var(--text-primary)]">
                  {batchProgress.completed} / {batchProgress.total}
                </span>
              </div>
              <div className="w-full bg-[var(--bg-secondary)] rounded-full h-1.5 overflow-hidden">
                <div
                  className="bg-[var(--primary)] h-full transition-all duration-300 ease-out"
                  style={{
                    width: `${(batchProgress.completed / batchProgress.total) * 100}%`
                  }}
                />
              </div>
            </div>
          )}

          {/* Action buttons */}
          <div className="flex flex-wrap gap-2">
            <button
              aria-label="Export selected as JSON"
              tabIndex={0}
              onClick={() => handleBatchExport('json')}
              disabled={!!batchProgress}
              className="flex-1 min-w-[100px] px-3 py-2 bg-[var(--bg-primary)] hover:bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg text-xs font-medium text-[var(--text-primary)] transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-1.5"
            >
              <span>📥</span>
              <span>Export JSON</span>
            </button>
            <button
              aria-label="Export selected as Markdown"
              tabIndex={0}
              onClick={() => handleBatchExport('markdown')}
              disabled={!!batchProgress}
              className="flex-1 min-w-[100px] px-3 py-2 bg-[var(--bg-primary)] hover:bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg text-xs font-medium text-[var(--text-primary)] transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-1.5"
            >
              <span>📄</span>
              <span>Export MD</span>
            </button>
            <button
              aria-label="Archive selected"
              tabIndex={0}
              onClick={handleBatchArchive}
              disabled={!!batchProgress}
              className="flex-1 min-w-[100px] px-3 py-2 bg-[var(--bg-primary)] hover:bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg text-xs font-medium text-[var(--text-primary)] transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-1.5"
            >
              <span>📦</span>
              <span>Archive</span>
            </button>
            <button
              aria-label="Duplicate selected"
              tabIndex={0}
              onClick={handleBatchDuplicate}
              disabled={!!batchProgress}
              className="flex-1 min-w-[100px] px-3 py-2 bg-[var(--bg-primary)] hover:bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg text-xs font-medium text-[var(--text-primary)] transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-1.5"
            >
              <span>📋</span>
              <span>Duplicate</span>
            </button>
            <button
              aria-label="Move selected"
              tabIndex={0}
              onClick={() => setShowBatchMoveModal(true)}
              disabled={!!batchProgress}
              className="flex-1 min-w-[100px] px-3 py-2 bg-[var(--bg-primary)] hover:bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg text-xs font-medium text-[var(--text-primary)] transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-1.5"
            >
              <span>📁</span>
              <span>Move</span>
            </button>
            <button
              aria-label="Delete selected"
              tabIndex={0}
              onClick={handleBatchDelete}
              disabled={!!batchProgress}
              className="flex-1 min-w-[100px] px-3 py-2 bg-red-50 hover:bg-red-100 border border-red-200 rounded-lg text-xs font-medium text-red-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-1.5"
            >
              <span>🗑️</span>
              <span>Delete</span>
            </button>
          </div>
        </div>
      )}

      <div className="flex-1 overflow-y-auto p-2 space-y-1">
        {conversations.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full p-8 text-center">
            {/* Empty state illustration */}
            <div className="text-6xl mb-4 opacity-50">💬</div>

            {/* Empty state text */}
            <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-2">
              No conversations yet
            </h3>
            <p className="text-sm text-[var(--text-secondary)] mb-6 max-w-xs">
              Start a new conversation to begin chatting with Claude
            </p>

            {/* Call-to-action button */}
            <button
          aria-label="New conversation"
          tabIndex={0}
              onClick={handleNewConversation}
              disabled={isCreating}
              className="px-6 py-3 bg-[var(--primary)] hover:bg-[var(--primary-hover)] active:bg-[var(--primary-active)] text-white rounded-lg font-medium transition-colors disabled:opacity-50 flex items-center gap-2 shadow-sm hover:shadow-md"
            >
              <span className="text-lg">+</span>
              <span>{isCreating ? 'Creating...' : 'Start Chatting'}</span>
            </button>
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
                batchSelectMode={batchSelectMode}
                isBatchSelected={selectedConversationIds.includes(conv.id)}
                onBatchToggle={() => toggleConversationSelection(conv.id)}
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
                batchSelectMode={batchSelectMode}
                isBatchSelected={selectedConversationIds.includes(conv.id)}
                onBatchToggle={() => toggleConversationSelection(conv.id)}
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
                batchSelectMode={batchSelectMode}
                isBatchSelected={selectedConversationIds.includes(conv.id)}
                onBatchToggle={() => toggleConversationSelection(conv.id)}
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
          aria-label="New conversation"
          tabIndex={0}
          onClick={() => setSidebarOpen(false)}
          className="lg:hidden px-2 py-1 bg-[var(--bg-primary)] rounded hover:bg-[var(--border)]"
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
  // Batch mode props
  batchSelectMode: boolean
  isBatchSelected: boolean
  onBatchToggle: () => void
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
  batchSelectMode,
  isBatchSelected,
  onBatchToggle,
}: ConversationItemProps) {
  const [showActions, setShowActions] = useState(false)
  const [isEditing, setIsEditing] = useState(false)
  const [editTitle, setEditTitle] = useState(conv.title)
  const { openContextMenu } = useContextMenu()
  const { showSuccess } = useToast()

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

  const handleContextMenu = (e: React.MouseEvent) => {
    if (isEditing) return

    const items = createConversationMenuItems(
      () => handleStartEdit(e),
      () => onArchive(e),
      () => onDelete(e),
      () => {
        onExport(e, 'json')
        showSuccess('Exported', 'Conversation exported as JSON')
      }
    )

    // Add additional items
    items.splice(1, 0, {
      id: 'duplicate',
      label: 'Duplicate',
      icon: (
        <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
        </svg>
      ),
      onClick: () => onDuplicate(e),
    })

    items.splice(2, 0, {
      id: 'pin',
      label: conv.isPinned ? 'Unpin' : 'Pin',
      icon: (
        <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
        </svg>
      ),
      onClick: () => onPin(e),
    })

    items.splice(3, 0, {
      id: 'export-md',
      label: 'Export as Markdown',
      icon: (
        <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
      ),
      onClick: () => {
        onExport(e, 'markdown')
        showSuccess('Exported', 'Conversation exported as Markdown')
      },
    })

    items.splice(4, 0, {
      id: 'move',
      label: 'Move to Project',
      icon: (
        <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
        </svg>
      ),
      onClick: () => onMove(),
    })

    openContextMenu(e, items)
  }

  return (
    <div
      className={`group relative flex items-center gap-2 px-3 py-2 rounded-lg transition-colors ${
        batchSelectMode
          ? 'cursor-pointer hover:bg-[var(--bg-primary)]'
          : `cursor-pointer ${isSelected ? 'bg-[var(--primary)] text-white' : 'hover:bg-[var(--bg-primary)] text-[var(--text-primary)]'}`
      } ${isDeleting ? 'opacity-50' : ''}`}
      onClick={(e) => {
        if (isEditing) return
        if (batchSelectMode) {
          onBatchToggle()
        } else {
          onSelect()
        }
      }}
      onMouseEnter={() => setShowActions(true)}
      onMouseLeave={() => {
        setShowActions(false)
        if (isEditing) {
          handleCancelEdit()
        }
      }}
      onContextMenu={handleContextMenu}
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
          aria-label="New conversation"
          tabIndex={0}
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
          {/* Batch mode checkbox */}
          {batchSelectMode && (
            <div className="mr-2" onClick={(e) => e.stopPropagation()}>
              <input
                type="checkbox"
                checked={isBatchSelected}
                onChange={onBatchToggle}
                className="w-4 h-4 rounded border-[var(--border)] text-[var(--primary)] focus:ring-[var(--primary)] cursor-pointer"
              />
            </div>
          )}

          <span className="flex-1 truncate text-sm">
            {conv.title || 'Untitled'}
          </span>

          {/* Unread message indicator */}
          {conv.unreadCount > 0 && (
            <div className="flex items-center gap-1 ml-2">
              <span className="w-2 h-2 bg-[var(--primary)] rounded-full" />
              <span className="text-xs text-[var(--text-secondary)] min-w-[16px] text-right">
                {conv.unreadCount}
              </span>
            </div>
          )}

          {/* Tags display */}
          {conv.tags && conv.tags.length > 0 && (
            <div className="flex flex-wrap gap-1 ml-2">
              {conv.tags.slice(0, 3).map((tag) => (
                <span
                  key={tag.id}
                  className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium"
                  style={{ backgroundColor: `${tag.color}20`, color: tag.color, borderColor: tag.color }}
                >
                  {tag.name}
                </span>
              ))}
              {conv.tags.length > 3 && (
                <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-[var(--bg-primary)] text-[var(--text-secondary)] border border-[var(--border)]">
                  +{conv.tags.length - 3}
                </span>
              )}
            </div>
          )}

          {/* Regular actions - hidden in batch mode */}
          {!batchSelectMode && (showActions || isSelected) && !isDeleting && !isDuplicating && !isArchiving && !isExporting && !isMoving && (
            <div className="flex gap-1">
              <button
          aria-label="New conversation"
          tabIndex={0}
                onClick={handleStartEdit}
                title="Rename"
                className={`p-1 rounded hover:bg-[var(--bg-secondary)] ${
                  isSelected ? 'hover:bg-white/20' : ''
                }`}
              >
                ✏️
              </button>
              <button
          aria-label="New conversation"
          tabIndex={0}
                onClick={onPin}
                title={conv.isPinned ? 'Unpin' : 'Pin'}
                className={`p-1 rounded hover:bg-[var(--bg-secondary)] ${
                  isSelected ? 'hover:bg-white/20' : ''
                }`}
              >
                {conv.isPinned ? '📌' : '📍'}
              </button>
              <button
          aria-label="New conversation"
          tabIndex={0}
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
          aria-label="New conversation"
          tabIndex={0}
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
          aria-label="New conversation"
          tabIndex={0}
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
          aria-label="New conversation"
          tabIndex={0}
                onClick={(e) => onExport(e, 'json')}
                title="Export as JSON"
                className={`p-1 rounded hover:bg-[var(--bg-secondary)] ${
                  isSelected ? 'hover:bg-white/20' : ''
                }`}
              >
                📄
              </button>
              <button
          aria-label="New conversation"
          tabIndex={0}
                onClick={(e) => onExport(e, 'markdown')}
                title="Export as Markdown"
                className={`p-1 rounded hover:bg-[var(--bg-secondary)] ${
                  isSelected ? 'hover:bg-white/20' : ''
                }`}
              >
                📝
              </button>
              <button
          aria-label="New conversation"
          tabIndex={0}
                onClick={onMove}
                title="Move to Project"
                className={`p-1 rounded hover:bg-[var(--bg-secondary)] ${
                  isSelected ? 'hover:bg-white/20' : ''
                }`}
              >
                📁
              </button>
              <button
          aria-label="New conversation"
          tabIndex={0}
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
          aria-label="New conversation"
          tabIndex={0}
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
          aria-label="New conversation"
          tabIndex={0}
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
          aria-label="New conversation"
          tabIndex={0}
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
          aria-label="New conversation"
          tabIndex={0}
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
