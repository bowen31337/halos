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
    <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4 backdrop-blur-sm animate-fade-in">
      <div className="bg-[var(--bg-primary)] border-2 border-[var(--warning)] rounded-xl w-full max-w-2xl max-h-[85vh] flex flex-col shadow-2xl modal-transition transform scale-100"
           style={{ boxShadow: '0 20px 50px rgba(245, 158, 11, 0.2)' }}>
        {/* Header - Attention grabbing with warning accent */}
        <div className="px-5 py-4 border-b-2 border-[var(--warning)] bg-gradient-to-r from-[var(--warning)]/10 to-transparent flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-2xl animate-pulse">⚠️</span>
            <div>
              <span className="text-base font-bold text-[var(--text-primary)] tracking-wide">APPROVAL REQUIRED</span>
              <div className="text-xs text-[var(--text-secondary)] mt-0.5">Human-in-the-Loop Intervention</div>
            </div>
          </div>
          <span className="text-xs font-semibold px-3 py-1 bg-[var(--warning)] text-white rounded-full shadow-sm"
                style={{ letterSpacing: '0.05em' }}>
            HITL
          </span>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-5 space-y-4 bg-[var(--bg-primary)]/95">
          {/* Reason - Highlighted */}
          <div className="bg-[var(--warning)]/10 border border-[var(--warning)]/30 rounded-lg p-4 shadow-sm"
               style={{ borderLeft: '4px solid var(--warning)' }}>
            <div className="flex items-center gap-2 text-xs font-bold text-[var(--warning)] mb-2 uppercase tracking-wider">
              <span className="w-2 h-2 bg-[var(--warning)] rounded-full animate-pulse"></span>
              Reason for Approval
            </div>
            <div className="text-sm text-[var(--text-primary)] leading-relaxed font-medium">
              {reason}
            </div>
          </div>

          {/* Tool Info */}
          <div className="flex items-center justify-between bg-[var(--surface-secondary)] p-3 rounded-lg border border-[var(--border)]">
            <div>
              <div className="text-xs font-semibold text-[var(--text-secondary)] mb-1">Tool Name</div>
              <div className="text-sm font-mono font-semibold text-[var(--text-primary)] bg-[var(--bg-primary)] px-3 py-1 rounded border border-[var(--border)] inline-block"
                   style={{ borderLeft: '3px solid var(--info)' }}>
                {tool}
              </div>
            </div>
            <div className="text-xs text-[var(--text-secondary)] px-2 py-1 bg-[var(--bg-secondary)] rounded">
              Requires explicit confirmation
            </div>
          </div>

          {/* Tabs */}
          <div className="flex border-b border-[var(--border)] gap-1">
            <button
              onClick={() => setActiveTab('view')}
              className={`px-5 py-2.5 text-sm font-medium transition-all-smooth rounded-t-lg ${
                activeTab === 'view'
                  ? 'bg-[var(--bg-primary)] text-[var(--primary)] border-2 border-b-0 border-[var(--border)] border-t-[var(--primary)] -mb-px'
                  : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--surface-secondary)]'
              }`}
            >
              View Input
            </button>
            <button
              onClick={() => setActiveTab('edit')}
              className={`px-5 py-2.5 text-sm font-medium transition-all-smooth rounded-t-lg ${
                activeTab === 'edit'
                  ? 'bg-[var(--bg-primary)] text-[var(--primary)] border-2 border-b-0 border-[var(--border)] border-t-[var(--primary)] -mb-px'
                  : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--surface-secondary)]'
              }`}
            >
              Edit Input
            </button>
          </div>

          {/* Tab Content */}
          {activeTab === 'view' ? (
            <div className="space-y-2 animate-fade-in">
              <div className="flex items-center gap-2 text-xs font-bold text-[var(--text-secondary)] uppercase tracking-wider">
                <span className="w-1.5 h-1.5 bg-[var(--info)] rounded-full"></span>
                Tool Input Parameters
              </div>
              <pre className="text-xs font-mono bg-[var(--bg-secondary)] p-4 rounded-lg overflow-x-auto text-[var(--text-primary)] border border-[var(--border)] shadow-inner"
                   style={{ borderRadius: '0.5rem' }}>
                {JSON.stringify(input, null, 2)}
              </pre>
            </div>
          ) : (
            <div className="space-y-3 animate-fade-in">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-xs font-bold text-[var(--text-secondary)] uppercase tracking-wider">
                  <span className="w-1.5 h-1.5 bg-[var(--primary)] rounded-full"></span>
                  Edit Tool Input
                </div>
                <button
                  onClick={formatJson}
                  className="text-xs px-3 py-1.5 bg-[var(--surface-elevated)] hover:bg-[var(--border)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] rounded transition-colors-smooth font-medium border border-[var(--border)]"
                  title="Format JSON"
                >
                  ✨ Format JSON
                </button>
              </div>
              <textarea
                ref={textareaRef}
                value={editedInput}
                onChange={(e) => setEditedInput(e.target.value)}
                className="w-full h-52 p-4 font-mono text-xs bg-[var(--bg-secondary)] border-2 border-[var(--border)] rounded-lg resize-y focus:outline-none focus:border-[var(--primary)] focus:ring-2 focus:ring-[var(--primary)]/20 transition-all-smooth"
                spellCheck={false}
              />
              <div className="text-xs text-[var(--text-secondary)] bg-[var(--surface-secondary)] p-2 rounded border border-[var(--border)]/50"
                   style={{ borderLeft: '3px solid var(--info)' }}>
                Edit the JSON above and click <strong>Save & Edit</strong> to apply changes before approval.
              </div>
            </div>
          )}

          {/* Error Message */}
          {error && (
            <div className="animate-fade-in text-sm font-medium text-[var(--error)] bg-[var(--error)]/10 p-3 rounded-lg border border-[var(--error)]/30 flex items-center gap-2"
                 style={{ borderLeft: '4px solid var(--error)' }}>
              <span>❌</span>
              <span>{error}</span>
            </div>
          )}
        </div>

        {/* Footer - Action Buttons with enhanced styling */}
        <div className="px-5 py-4 border-t border-[var(--border)] flex gap-3 justify-end bg-[var(--surface-secondary)] rounded-b-xl">
          {/* Reject Button */}
          <button
            onClick={handleReject}
            disabled={isProcessing}
            className={`px-5 py-2.5 text-sm font-bold rounded-lg transition-all-smooth flex items-center gap-2
              ${isProcessing ? 'opacity-50 cursor-not-allowed' : 'hover:scale-105 active:scale-95'}
              bg-[var(--error)]/10 text-[var(--error)] hover:bg-[var(--error)]/20 border-2 border-[var(--error)]/20 hover:border-[var(--error)]/40`}
          >
            <span>🚫</span>
            <span>{isProcessing ? 'Rejecting...' : 'Reject'}</span>
          </button>

          <div className="flex-1" />

          {activeTab === 'edit' ? (
            <button
              onClick={handleEdit}
              disabled={isProcessing}
              className={`px-6 py-2.5 text-sm font-bold rounded-lg transition-all-smooth flex items-center gap-2
                ${isProcessing ? 'opacity-50 cursor-not-allowed' : 'hover:scale-105 active:scale-95'}
                bg-[var(--primary)] text-white hover:bg-[var(--primary-hover)] shadow-lg shadow-[var(--primary)]/20`}
            >
              <span>💾</span>
              <span>{isProcessing ? 'Saving...' : 'Save & Edit'}</span>
            </button>
          ) : (
            <button
              onClick={handleApprove}
              disabled={isProcessing}
              className={`px-6 py-2.5 text-sm font-bold rounded-lg transition-all-smooth flex items-center gap-2
                ${isProcessing ? 'opacity-50 cursor-not-allowed' : 'hover:scale-105 active:scale-95'}
                bg-[var(--success)] text-white hover:bg-[var(--success)]/90 shadow-lg shadow-[var(--success)]/20`}
            >
              <span>✓</span>
              <span>{isProcessing ? 'Approving...' : 'Approve'}</span>
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
