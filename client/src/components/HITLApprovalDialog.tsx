import { useState, useEffect, useRef } from 'react'
import { api } from '../services/api'
import { useConversationStore } from '../stores/conversationStore'

interface HITLApprovalDialogProps {
  threadId: string
  tool: string
  input: any
  reason: string
  onApproved: () => void
  onRejected: () => void
  onEdited: (editedInput: any) => void
}

export function HITLApprovalDialog({
  threadId,
  tool,
  input,
  reason,
  onApproved,
  onRejected,
  onEdited
}: HITLApprovalDialogProps) {
  const [activeTab, setActiveTab] = useState<'view' | 'edit'>('view')
  const [editedInput, setEditedInput] = useState(JSON.stringify(input, null, 2))
  const [isProcessing, setIsProcessing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  // Auto-focus textarea when switching to edit mode
  useEffect(() => {
    if (activeTab === 'edit' && textareaRef.current) {
      textareaRef.current.focus()
    }
  }, [activeTab])

  const handleApprove = async () => {
    setIsProcessing(true)
    setError(null)
    try {
      await api.handleInterrupt(threadId, 'approve')
      onApproved()
    } catch (err) {
      setError('Failed to approve. Please try again.')
      console.error(err)
    } finally {
      setIsProcessing(false)
    }
  }

  const handleReject = async () => {
    setIsProcessing(true)
    setError(null)
    try {
      await api.handleInterrupt(threadId, 'reject')
      onRejected()
    } catch (err) {
      setError('Failed to reject. Please try again.')
      console.error(err)
    } finally {
      setIsProcessing(false)
    }
  }

  const handleEdit = async () => {
    setIsProcessing(true)
    setError(null)
    try {
      const parsedInput = JSON.parse(editedInput)
      await api.handleInterrupt(threadId, 'edit', parsedInput)
      onEdited(parsedInput)
    } catch (err) {
      setError('Invalid JSON format. Please check your input.')
      console.error(err)
    } finally {
      setIsProcessing(false)
    }
  }

  const formatJson = () => {
    try {
      const parsed = JSON.parse(editedInput)
      setEditedInput(JSON.stringify(parsed, null, 2))
      setError(null)
    } catch (err) {
      setError('Invalid JSON format')
    }
  }

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <div className="bg-[var(--bg-primary)] border border-[var(--border)] rounded-lg w-full max-w-2xl max-h-[80vh] flex flex-col shadow-2xl">
        {/* Header */}
        <div className="px-4 py-3 border-b border-[var(--border)] flex items-center justify-between bg-[var(--surface-secondary)]">
          <div className="flex items-center gap-2">
            <span className="text-lg">⚠️</span>
            <span className="text-sm font-semibold text-[var(--text-primary)]">Approval Required</span>
          </div>
          <span className="text-xs text-[var(--text-secondary)] px-2 py-1 bg-[var(--bg-secondary)] rounded">
            Human-in-the-Loop
          </span>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {/* Reason */}
          <div className="bg-[var(--bg-secondary)] p-3 rounded border border-[var(--border)]">
            <div className="text-xs font-semibold text-[var(--text-secondary)] mb-1">Reason:</div>
            <div className="text-sm text-[var(--text-primary)]">{reason}</div>
          </div>

          {/* Tool Info */}
          <div>
            <div className="text-xs font-semibold text-[var(--text-secondary)] mb-1">Tool:</div>
            <div className="text-sm font-mono bg-[var(--bg-secondary)] px-2 py-1 rounded inline-block text-[var(--text-primary)]">
              {tool}
            </div>
          </div>

          {/* Tabs */}
          <div className="flex border-b border-[var(--border)]">
            <button
              onClick={() => setActiveTab('view')}
              className={`px-4 py-2 text-sm transition-colors ${
                activeTab === 'view'
                  ? 'border-b-2 border-[var(--primary)] text-[var(--primary)] font-medium'
                  : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
              }`}
            >
              View Input
            </button>
            <button
              onClick={() => setActiveTab('edit')}
              className={`px-4 py-2 text-sm transition-colors ${
                activeTab === 'edit'
                  ? 'border-b-2 border-[var(--primary)] text-[var(--primary)] font-medium'
                  : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
              }`}
            >
              Edit Input (Feature #59)
            </button>
          </div>

          {/* Tab Content */}
          {activeTab === 'view' ? (
            <div className="space-y-2">
              <div className="text-xs font-semibold text-[var(--text-secondary)]">Input:</div>
              <pre className="text-xs font-mono bg-[var(--bg-secondary)] p-3 rounded overflow-x-auto text-[var(--text-primary)] border border-[var(--border)]">
                {JSON.stringify(input, null, 2)}
              </pre>
            </div>
          ) : (
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <div className="text-xs font-semibold text-[var(--text-secondary)]">Edit Input:</div>
                <button
                  onClick={formatJson}
                  className="text-xs px-2 py-1 bg-[var(--bg-secondary)] hover:bg-[var(--border)] rounded transition-colors"
                  title="Format JSON"
                >
                  Format JSON
                </button>
              </div>
              <textarea
                ref={textareaRef}
                value={editedInput}
                onChange={(e) => setEditedInput(e.target.value)}
                className="w-full h-48 p-3 font-mono text-xs bg-[var(--bg-secondary)] border border-[var(--border)] rounded resize-y focus:outline-none focus:border-[var(--primary)]"
                spellCheck={false}
              />
              <div className="text-xs text-[var(--text-secondary)]">
                Edit the tool input JSON and click "Save & Edit" to apply changes.
              </div>
            </div>
          )}

          {/* Error Message */}
          {error && (
            <div className="text-sm text-[var(--error)] bg-[var(--bg-secondary)] p-2 rounded border border-[var(--error)]/20">
              {error}
            </div>
          )}
        </div>

        {/* Footer - Action Buttons */}
        <div className="px-4 py-3 border-t border-[var(--border)] flex gap-2 justify-end bg-[var(--surface-secondary)]">
          {/* Reject Button (Feature #60) */}
          <button
            onClick={handleReject}
            disabled={isProcessing}
            className="px-4 py-2 text-sm font-medium bg-[var(--error)]/10 text-[var(--error)] hover:bg-[var(--error)]/20 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Reject
          </button>

          <div className="flex-1" />

          {activeTab === 'edit' ? (
            <button
              onClick={handleEdit}
              disabled={isProcessing}
              className="px-4 py-2 text-sm font-medium bg-[var(--primary)] text-white hover:bg-[var(--primary)]/90 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isProcessing ? 'Saving...' : 'Save & Edit'}
            </button>
          ) : (
            <>
              <button
                onClick={handleApprove}
                disabled={isProcessing}
                className="px-4 py-2 text-sm font-medium bg-[var(--success)] text-white hover:bg-[var(--success)]/90 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isProcessing ? 'Approving...' : 'Approve'}
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
