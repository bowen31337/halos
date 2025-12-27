import { useEffect, useState } from 'react'
import { useBranchingStore } from '../stores/branchingStore'
import { useConversationStore } from '../stores/conversationStore'

interface BranchSelectorProps {
  conversationId: string
}

export function BranchSelector({ conversationId }: BranchSelectorProps) {
  const { branches, branchPath, loadBranches, loadBranchTree, switchBranch, isBranching } = useBranchingStore()
  const { currentConversationId, setCurrentConversation, loadMessages } = useConversationStore()
  const [showDropdown, setShowDropdown] = useState(false)

  useEffect(() => {
    if (conversationId) {
      loadBranches(conversationId)
      loadBranchTree(conversationId)
    }
  }, [conversationId, loadBranches, loadBranchTree])

  const handleSwitchBranch = async (targetConversationId: string) => {
    if (targetConversationId === currentConversationId) {
      setShowDropdown(false)
      return
    }

    try {
      await switchBranch(currentConversationId!, targetConversationId)
      setCurrentConversation(targetConversationId)
      await loadMessages(targetConversationId)
      await loadBranchPath(targetConversationId)
      setShowDropdown(false)
    } catch (err) {
      console.error('Failed to switch branch:', err)
    }
  }

  // Don't show if no branches
  if (branches.length === 0) {
    return null
  }

  const currentBranch = branches.find(b => b.id === currentConversationId)

  return (
    <div className="relative">
      {/* Branch indicator button */}
      <button
        onClick={() => setShowDropdown(!showDropdown)}
        className="flex items-center gap-2 px-3 py-1.5 bg-[var(--bg-secondary)] hover:bg-[var(--border)] rounded-lg text-xs font-medium transition-colors"
        title="Switch branches"
      >
        <span>🌳</span>
        <span>
          {branchPath.length > 1 ? `Branch ${branchPath.length}` : 'Main'}
        </span>
        {isBranching && <span className="animate-spin">⏳</span>}
      </button>

      {/* Dropdown menu */}
      {showDropdown && (
        <>
          <div
            className="fixed inset-0 z-40"
            onClick={() => setShowDropdown(false)}
          />
          <div className="absolute top-full mt-2 right-0 min-w-[250px] bg-[var(--surface-elevated)] border border-[var(--border)] rounded-lg shadow-xl z-50 overflow-hidden">
            <div className="px-3 py-2 text-xs font-semibold text-[var(--text-secondary)] border-b border-[var(--border)]">
              Branches ({branches.length})
            </div>
            <div className="max-h-[300px] overflow-y-auto">
              {branches.map((branch) => (
                <button
                  key={branch.id}
                  onClick={() => handleSwitchBranch(branch.id)}
                  className={`w-full text-left px-3 py-2 text-sm hover:bg-[var(--bg-secondary)] transition-colors flex items-center justify-between ${
                    branch.id === currentConversationId ? 'bg-[var(--bg-secondary)] font-medium' : ''
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <div
                      className="w-2 h-2 rounded-full"
                      style={{ backgroundColor: branch.branchColor || '#ff6b6b' }}
                    />
                    <span className="truncate max-w-[150px]">
                      {branch.branchName || branch.title}
                    </span>
                  </div>
                  {branch.id === currentConversationId && (
                    <span className="text-xs text-[var(--text-secondary)]">Current</span>
                  )}
                </button>
              ))}
            </div>
            {/* Branch path visualization */}
            {branchPath.length > 1 && (
              <div className="px-3 py-2 border-t border-[var(--border)] bg-[var(--bg-primary)]">
                <div className="text-[10px] text-[var(--text-secondary)] mb-1">Branch Path:</div>
                <div className="flex items-center gap-1 text-[10px]">
                  {branchPath.map((node, idx) => (
                    <div key={node.id} className="flex items-center gap-1">
                      <span
                        className="w-1.5 h-1.5 rounded-full"
                        style={{ backgroundColor: node.branchColor || '#ff6b6b' }}
                      />
                      {idx < branchPath.length - 1 && (
                        <span className="text-[var(--text-secondary)]">→</span>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  )
}
