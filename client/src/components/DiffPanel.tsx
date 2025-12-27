import { useState, useEffect } from 'react'
import { useChatStore, type FileDiff } from '../stores/chatStore'

interface DiffLine {
  text: string
  type: 'added' | 'removed' | 'unchanged'
  oldLineNum?: number
  newLineNum?: number
}

export function DiffPanel() {
  const { fileDiffs, clearFileDiffs } = useChatStore()
  const [selectedDiff, setSelectedDiff] = useState<FileDiff | null>(null)
  const [diffLines, setDiffLines] = useState<DiffLine[]>([])

  // Auto-select first diff when panel opens
  useEffect(() => {
    if (fileDiffs.length > 0 && !selectedDiff) {
      setSelectedDiff(fileDiffs[fileDiffs.length - 1])
    }
  }, [fileDiffs])

  // Generate diff lines when a diff is selected
  useEffect(() => {
    if (!selectedDiff) {
      setDiffLines([])
      return
    }

    const oldLines = selectedDiff.oldContent.split('\n')
    const newLines = selectedDiff.newContent.split('\n')
    const lines: DiffLine[] = []

    // Simple diff algorithm
    let oldIdx = 0
    let newIdx = 0

    while (oldIdx < oldLines.length || newIdx < newLines.length) {
      if (oldIdx < oldLines.length && newIdx < newLines.length && oldLines[oldIdx] === newLines[newIdx]) {
        // Unchanged line
        lines.push({
          text: oldLines[oldIdx],
          type: 'unchanged',
          oldLineNum: oldIdx + 1,
          newLineNum: newIdx + 1
        })
        oldIdx++
        newIdx++
      } else if (newIdx < newLines.length && (oldIdx >= oldLines.length || !oldLines.slice(oldIdx).includes(newLines[newIdx]))) {
        // Added line
        lines.push({
          text: newLines[newIdx],
          type: 'added',
          newLineNum: newIdx + 1
        })
        newIdx++
      } else if (oldIdx < oldLines.length && (newIdx >= newLines.length || !newLines.slice(newIdx).includes(oldLines[oldIdx]))) {
        // Removed line
        lines.push({
          text: oldLines[oldIdx],
          type: 'removed',
          oldLineNum: oldIdx + 1
        })
        oldIdx++
      } else {
        // Fallback: just show both
        if (oldIdx < oldLines.length) {
          lines.push({
            text: oldLines[oldIdx],
            type: 'removed',
            oldLineNum: oldIdx + 1
          })
          oldIdx++
        }
        if (newIdx < newLines.length) {
          lines.push({
            text: newLines[newIdx],
            type: 'added',
            newLineNum: newIdx + 1
          })
          newIdx++
        }
      }
    }

    setDiffLines(lines)
  }, [selectedDiff])

  const getChangeTypeLabel = (type: string) => {
    switch (type) {
      case 'added': return 'New File'
      case 'modified': return 'Modified'
      case 'deleted': return 'Deleted'
      default: return type
    }
  }

  const getChangeTypeColor = (type: string) => {
    switch (type) {
      case 'added': return 'text-[var(--success)]'
      case 'modified': return 'text-[var(--warning)]'
      case 'deleted': return 'text-[var(--error)]'
      default: return 'text-[var(--text-secondary)]'
    }
  }

  return (
    <div className="fixed right-0 top-14 bottom-0 w-[600px] bg-[var(--bg-primary)] border-l border-[var(--border)] shadow-xl z-20 flex flex-col">
      {/* Header */}
      <div className="px-4 py-3 border-b border-[var(--border)] flex items-center justify-between">
        <div className="flex items-center gap-2">
          <svg className="w-4 h-4 text-[var(--text-primary)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
          </svg>
          <span className="text-sm font-semibold text-[var(--text-primary)]">File Changes</span>
          {fileDiffs.length > 0 && (
            <span className="text-xs px-2 py-0.5 rounded-full bg-[var(--primary)] text-white">
              {fileDiffs.length}
            </span>
          )}
        </div>
        <button
          onClick={clearFileDiffs}
          className="text-xs px-2 py-1 hover:bg-[var(--surface-elevated)] rounded transition-colors"
          title="Clear all diffs"
        >
          Clear
        </button>
      </div>

      {/* Content */}
      <div className="flex flex-1 overflow-hidden">
        {/* Diff List Sidebar */}
        <div className="w-64 border-r border-[var(--border)] overflow-y-auto">
          {fileDiffs.length === 0 ? (
            <div className="p-4 text-sm text-[var(--text-secondary)] text-center">
              No file changes yet
            </div>
          ) : (
            <div className="divide-y divide-[var(--border)]">
              {fileDiffs.map((diff) => (
                <div
                  key={diff.id}
                  className={`p-3 cursor-pointer hover:bg-[var(--surface-elevated)] transition-colors ${
                    selectedDiff?.id === diff.id ? 'bg-[var(--surface-elevated)] border-l-2 border-[var(--primary)]' : ''
                  }`}
                  onClick={() => setSelectedDiff(diff)}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm font-medium text-[var(--text-primary)] truncate flex-1">
                      {diff.fileName}
                    </span>
                    <span className={`text-xs ${getChangeTypeColor(diff.changeType)}`}>
                      {getChangeTypeLabel(diff.changeType)}
                    </span>
                  </div>
                  <div className="text-xs text-[var(--text-secondary)]">
                    {new Date(diff.timestamp).toLocaleTimeString()}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Diff Viewer */}
        <div className="flex-1 overflow-y-auto">
          {selectedDiff ? (
            <div className="flex flex-col h-full">
              {/* Diff Header */}
              <div className="px-4 py-3 bg-[var(--surface-secondary)] border-b border-[var(--border)]">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-sm font-semibold text-[var(--text-primary)]">
                      {selectedDiff.fileName}
                    </div>
                    <div className="text-xs text-[var(--text-secondary)]">
                      {getChangeTypeLabel(selectedDiff.changeType)} • {new Date(selectedDiff.timestamp).toLocaleString()}
                    </div>
                  </div>
                  <button
                    onClick={() => {
                      // Download the new content
                      const blob = new Blob([selectedDiff.newContent], { type: 'text/plain' })
                      const url = URL.createObjectURL(blob)
                      const a = document.createElement('a')
                      a.href = url
                      a.download = selectedDiff.fileName
                      a.click()
                      URL.revokeObjectURL(url)
                    }}
                    className="p-1.5 hover:bg-[var(--surface-elevated)] rounded transition-colors"
                    title="Download file"
                  >
                    <svg className="w-4 h-4 text-[var(--text-primary)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                    </svg>
                  </button>
                </div>
              </div>

              {/* Diff Content */}
              <div className="flex-1 overflow-auto bg-[var(--bg-secondary)] font-mono text-xs">
                {diffLines.length === 0 ? (
                  <div className="p-4 text-[var(--text-secondary)] text-center">
                    No changes to display
                  </div>
                ) : (
                  <div className="min-w-full">
                    {diffLines.map((line, idx) => (
                      <div
                        key={idx}
                        className={`flex px-4 py-1 whitespace-pre-wrap break-all ${
                          line.type === 'added'
                            ? 'bg-[rgba(34,197,94,0.1)] text-[var(--success)]'
                            : line.type === 'removed'
                            ? 'bg-[rgba(239,68,68,0.1)] text-[var(--error)]'
                            : 'text-[var(--text-primary)]'
                        }`}
                      >
                        <span className="w-12 text-[var(--text-secondary)] opacity-50 select-none mr-4 text-right">
                          {line.oldLineNum || line.newLineNum || ''}
                        </span>
                        <span className="flex-1">{line.text || ' '}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Legend */}
              <div className="px-4 py-2 border-t border-[var(--border)] bg-[var(--surface-secondary)] text-xs flex gap-4">
                <span className="flex items-center gap-1">
                  <span className="w-3 h-3 bg-[rgba(34,197,94,0.3)] rounded-sm"></span>
                  <span>Added</span>
                </span>
                <span className="flex items-center gap-1">
                  <span className="w-3 h-3 bg-[rgba(239,68,68,0.3)] rounded-sm"></span>
                  <span>Removed</span>
                </span>
                <span className="flex items-center gap-1">
                  <span className="w-3 h-3 bg-[var(--bg-secondary)] border border-[var(--border)] rounded-sm"></span>
                  <span>Unchanged</span>
                </span>
              </div>
            </div>
          ) : (
            <div className="flex items-center justify-center h-full text-[var(--text-secondary)] text-sm p-8 text-center">
              Select a file change from the left to view the diff
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
