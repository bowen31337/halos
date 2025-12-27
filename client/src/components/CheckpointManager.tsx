/**
 * CheckpointManager Component
 * Provides UI for creating, viewing, and restoring conversation checkpoints
 */

import React, { useEffect, useState } from 'react'
import { useCheckpointStore, type Checkpoint } from '../stores/checkpointStore'
import { useConversationStore } from '../stores/conversationStore'

interface CheckpointManagerProps {
  onClose: () => void
}

export const CheckpointManager: React.FC<CheckpointManagerProps> = ({ onClose }) => {
  const {
    checkpoints,
    currentCheckpoint,
    isLoading,
    isCreating,
    isRestoring,
    error,
    loadCheckpoints,
    createCheckpoint,
    restoreCheckpoint,
    deleteCheckpoint,
    setCurrentCheckpoint,
    clearError,
  } = useCheckpointStore()

  const { currentConversation } = useConversationStore()

  const [showCreateModal, setShowCreateModal] = useState(false)
  const [checkpointName, setCheckpointName] = useState('')
  const [checkpointNotes, setCheckpointNotes] = useState('')
  const [showRestoreConfirm, setShowRestoreConfirm] = useState(false)
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)
  const [selectedCheckpoint, setSelectedCheckpoint] = useState<Checkpoint | null>(null)

  // Load checkpoints when component mounts
  useEffect(() => {
    if (currentConversation?.id) {
      loadCheckpoints(currentConversation.id)
    }
  }, [currentConversation?.id, loadCheckpoints])

  // Auto-clear error after 5 seconds
  useEffect(() => {
    if (error) {
      const timer = setTimeout(() => clearError(), 5000)
      return () => clearTimeout(timer)
    }
  }, [error, clearError])

  const handleCreateCheckpoint = async () => {
    if (!currentConversation?.id) return

    try {
      await createCheckpoint(
        currentConversation.id,
        checkpointName || undefined,
        checkpointNotes || undefined
      )
      setShowCreateModal(false)
      setCheckpointName('')
      setCheckpointNotes('')
    } catch (err) {
      // Error is handled in store
    }
  }

  const handleRestoreCheckpoint = async (checkpoint: Checkpoint) => {
    setSelectedCheckpoint(checkpoint)
    setShowRestoreConfirm(true)
  }

  const confirmRestore = async () => {
    if (!selectedCheckpoint) return

    try {
      await restoreCheckpoint(selectedCheckpoint.id)
      setShowRestoreConfirm(false)
      setSelectedCheckpoint(null)
      // Close modal after successful restore
      setTimeout(() => onClose(), 1000)
    } catch (err) {
      // Error is handled in store
    }
  }

  const handleDeleteCheckpoint = async (checkpoint: Checkpoint) => {
    setSelectedCheckpoint(checkpoint)
    setShowDeleteConfirm(true)
  }

  const confirmDelete = async () => {
    if (!selectedCheckpoint) return

    try {
      await deleteCheckpoint(selectedCheckpoint.id)
      setShowDeleteConfirm(false)
      setSelectedCheckpoint(null)
    } catch (err) {
      // Error is handled in store
    }
  }

  const formatTimestamp = (isoString: string) => {
    const date = new Date(isoString)
    return date.toLocaleString()
  }

  const getMessageCount = (checkpoint: Checkpoint) => {
    return checkpoint.state_snapshot.messages.length
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-gray-800 rounded-lg shadow-2xl w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-700">
          <h2 className="text-xl font-semibold text-white">Conversation Checkpoints</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white transition-colors"
          >
            ✕
          </button>
        </div>

        {/* Error Banner */}
        {error && (
          <div className="bg-red-900/50 border-l-4 border-red-500 p-3 mx-4 mt-2">
            <p className="text-red-200 text-sm">{error}</p>
          </div>
        )}

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4">
          {/* Create Button */}
          <div className="mb-4">
            <button
              onClick={() => setShowCreateModal(true)}
              disabled={isCreating || !currentConversation}
              className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed text-white px-4 py-2 rounded flex items-center gap-2 transition-colors"
            >
              {isCreating ? (
                <>
                  <span className="animate-spin">⟳</span>
                  Creating...
                </>
              ) : (
                <>
                  <span>+</span>
                  Create New Checkpoint
                </>
              )}
            </button>
          </div>

          {/* Checkpoints List */}
          {isLoading ? (
            <div className="flex justify-center py-8">
              <div className="animate-spin h-8 w-8 border-4 border-blue-500 border-t-transparent rounded-full"></div>
            </div>
          ) : checkpoints.length === 0 ? (
            <div className="text-center py-8 text-gray-400">
              <p>No checkpoints yet.</p>
              <p className="text-sm mt-2">Create a checkpoint to save your conversation state.</p>
            </div>
          ) : (
            <div className="space-y-3">
              {checkpoints.map((checkpoint) => (
                <div
                  key={checkpoint.id}
                  className="bg-gray-700/50 rounded-lg p-4 border border-gray-600 hover:border-gray-500 transition-colors"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <h3 className="font-medium text-white">{checkpoint.name}</h3>
                        <span className="text-xs bg-gray-600 px-2 py-0.5 rounded text-gray-300">
                          {getMessageCount(checkpoint)} messages
                        </span>
                      </div>
                      {checkpoint.notes && (
                        <p className="text-sm text-gray-400 mb-2">{checkpoint.notes}</p>
                      )}
                      <p className="text-xs text-gray-500">
                        Created: {formatTimestamp(checkpoint.created_at)}
                      </p>
                    </div>

                    <div className="flex gap-2">
                      <button
                        onClick={() => handleRestoreCheckpoint(checkpoint)}
                        disabled={isRestoring}
                        className="bg-green-600 hover:bg-green-700 disabled:opacity-50 text-white px-3 py-1.5 rounded text-sm transition-colors"
                        title="Restore to this checkpoint"
                      >
                        ↺ Restore
                      </button>
                      <button
                        onClick={() => handleDeleteCheckpoint(checkpoint)}
                        className="bg-red-600 hover:bg-red-700 text-white px-3 py-1.5 rounded text-sm transition-colors"
                        title="Delete checkpoint"
                      >
                        🗑
                      </button>
                    </div>
                  </div>

                  {/* Message Preview */}
                  {checkpoint.state_snapshot.messages.length > 0 && (
                    <div className="mt-3 pt-3 border-t border-gray-600">
                      <details className="text-sm">
                        <summary className="text-gray-400 cursor-pointer hover:text-gray-300">
                          View message preview
                        </summary>
                        <div className="mt-2 space-y-2 max-h-40 overflow-y-auto">
                          {checkpoint.state_snapshot.messages.slice(0, 3).map((msg) => (
                            <div key={msg.id} className="text-xs">
                              <span className={`font-semibold ${
                                msg.role === 'user' ? 'text-blue-400' : 'text-green-400'
                              }`}>
                                {msg.role === 'user' ? 'You' : 'Assistant'}:
                              </span>
                              <span className="text-gray-300 ml-1">
                                {msg.content.substring(0, 80)}
                                {msg.content.length > 80 ? '...' : ''}
                              </span>
                            </div>
                          ))}
                          {checkpoint.state_snapshot.messages.length > 3 && (
                            <div className="text-xs text-gray-500">
                              +{checkpoint.state_snapshot.messages.length - 3} more messages
                            </div>
                          )}
                        </div>
                      </details>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Create Modal */}
        {showCreateModal && (
          <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50">
            <div className="bg-gray-800 rounded-lg p-6 w-full max-w-md">
              <h3 className="text-lg font-semibold text-white mb-4">Create Checkpoint</h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm text-gray-300 mb-1">Name (optional)</label>
                  <input
                    type="text"
                    value={checkpointName}
                    onChange={(e) => setCheckpointName(e.target.value)}
                    placeholder="e.g., Before refactoring"
                    className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm text-gray-300 mb-1">Notes (optional)</label>
                  <textarea
                    value={checkpointNotes}
                    onChange={(e) => setCheckpointNotes(e.target.value)}
                    placeholder="Why are you saving this checkpoint?"
                    rows={3}
                    className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                  />
                </div>
                <div className="flex gap-2 justify-end">
                  <button
                    onClick={() => setShowCreateModal(false)}
                    className="px-4 py-2 rounded bg-gray-700 hover:bg-gray-600 text-white transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleCreateCheckpoint}
                    disabled={isCreating}
                    className="px-4 py-2 rounded bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white transition-colors"
                  >
                    {isCreating ? 'Creating...' : 'Create'}
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Restore Confirmation Modal */}
        {showRestoreConfirm && selectedCheckpoint && (
          <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50">
            <div className="bg-gray-800 rounded-lg p-6 w-full max-w-md">
              <h3 className="text-lg font-semibold text-white mb-2">Confirm Restore</h3>
              <p className="text-gray-300 mb-4">
                This will restore the conversation to the state saved in "
                <span className="font-semibold">{selectedCheckpoint.name}</span>
                ".
              </p>
              <p className="text-sm text-gray-400 mb-4">
                All messages after this checkpoint will be deleted. This action cannot be undone.
              </p>
              <div className="flex gap-2 justify-end">
                <button
                  onClick={() => setShowRestoreConfirm(false)}
                  className="px-4 py-2 rounded bg-gray-700 hover:bg-gray-600 text-white transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={confirmRestore}
                  disabled={isRestoring}
                  className="px-4 py-2 rounded bg-green-600 hover:bg-green-700 disabled:opacity-50 text-white transition-colors"
                >
                  {isRestoring ? 'Restoring...' : 'Restore'}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Delete Confirmation Modal */}
        {showDeleteConfirm && selectedCheckpoint && (
          <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50">
            <div className="bg-gray-800 rounded-lg p-6 w-full max-w-md">
              <h3 className="text-lg font-semibold text-white mb-2">Confirm Delete</h3>
              <p className="text-gray-300 mb-4">
                Delete checkpoint "
                <span className="font-semibold">{selectedCheckpoint.name}</span>
                "?
              </p>
              <p className="text-sm text-gray-400 mb-4">
                This action cannot be undone.
              </p>
              <div className="flex gap-2 justify-end">
                <button
                  onClick={() => setShowDeleteConfirm(false)}
                  className="px-4 py-2 rounded bg-gray-700 hover:bg-gray-600 text-white transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={confirmDelete}
                  className="px-4 py-2 rounded bg-red-600 hover:bg-red-700 text-white transition-colors"
                >
                  Delete
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
