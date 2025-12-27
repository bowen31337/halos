import { useEffect, useState } from 'react'
import { useChatStore, type WorkspaceFile, type FileDiff } from '../stores/chatStore'
import { useConversationStore } from '../stores/conversationStore'
import { api } from '../services/api'

export function FilesPanel() {
  const { files, setFiles, clearFiles, fileDiffs } = useChatStore()
  const { currentConversationId } = useConversationStore()
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [selectedFile, setSelectedFile] = useState<WorkspaceFile | null>(null)
  const [viewMode, setViewMode] = useState<'files' | 'diffs'>('files')
  const [selectedDiff, setSelectedDiff] = useState<FileDiff | null>(null)

  // Fetch files when conversation changes
  useEffect(() => {
    if (!currentConversationId) {
      clearFiles()
      return
    }

    const fetchFiles = async () => {
      setIsLoading(true)
      setError(null)
      try {
        // Use conversationId as threadId
        const response = await api.getWorkspaceFiles(currentConversationId)
        if (response.files) {
          setFiles(response.files)
        }
      } catch (err) {
        setError('Failed to load files')
        console.error('Error fetching files:', err)
      } finally {
        setIsLoading(false)
      }
    }

    fetchFiles()
    // Poll for updates every 3 seconds
    const interval = setInterval(fetchFiles, 3000)
    return () => clearInterval(interval)
  }, [currentConversationId, setFiles, clearFiles])

  // Format file size
  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  // Get file icon based on type
  const getFileIcon = (fileType: string, filename: string) => {
    if (fileType.includes('python') || filename.endsWith('.py')) return '🐍'
    if (fileType.includes('javascript') || filename.endsWith('.js')) return '🟨'
    if (fileType.includes('typescript') || filename.endsWith('.ts')) return '🔷'
    if (fileType.includes('json') || filename.endsWith('.json')) return '📄'
    if (fileType.includes('markdown') || filename.endsWith('.md')) return '📝'
    if (fileType.includes('html') || filename.endsWith('.html')) return '🌐'
    if (fileType.includes('css') || filename.endsWith('.css')) return '🎨'
    if (fileType.includes('image') || filename.match(/\.(png|jpg|jpeg|gif|svg)$/i)) return '🖼️'
    if (fileType.includes('pdf') || filename.endsWith('.pdf')) return '📕'
    return '📄'
  }

  // Group files by directory
  const groupByDirectory = (files: WorkspaceFile[]) => {
    const groups: Record<string, WorkspaceFile[]> = {}
    files.forEach(file => {
      const dir = file.path.split('/').slice(0, -1).join('/') || 'root'
      if (!groups[dir]) groups[dir] = []
      groups[dir].push(file)
    })
    return groups
  }

  // Get diff lines with highlighting
  const getDiffLines = (diff: FileDiff) => {
    const oldLines = diff.oldContent.split('\n')
    const newLines = diff.newContent.split('\n')

    // Simple diff algorithm
    const lines: Array<{ type: 'same' | 'added' | 'removed', content: string }> = []

    let i = 0, j = 0
    while (i < oldLines.length || j < newLines.length) {
      if (i < oldLines.length && j < newLines.length && oldLines[i] === newLines[j]) {
        lines.push({ type: 'same', content: oldLines[i] })
        i++
        j++
      } else if (j < newLines.length && (i >= oldLines.length || !oldLines.slice(i).includes(newLines[j]))) {
        lines.push({ type: 'added', content: newLines[j] })
        j++
      } else if (i < oldLines.length && (j >= newLines.length || !newLines.slice(j).includes(oldLines[i]))) {
        lines.push({ type: 'removed', content: oldLines[i] })
        i++
      } else {
        // Fallback: just add new line
        if (j < newLines.length) {
          lines.push({ type: 'added', content: newLines[j] })
          j++
        } else if (i < oldLines.length) {
          lines.push({ type: 'removed', content: oldLines[i] })
          i++
        }
      }
    }

    return lines
  }

  const fileGroups = groupByDirectory(files)

  return (
    <div className="fixed right-0 top-14 bottom-0 w-96 bg-[var(--bg-primary)] border-l border-[var(--border)] shadow-xl z-20 flex flex-col">
      {/* Header */}
      <div className="px-4 py-3 border-b border-[var(--border)] flex items-center justify-between">
        <div className="flex items-center gap-2">
          <svg className="w-4 h-4 text-[var(--text-primary)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <span className="text-sm font-semibold text-[var(--text-primary)]">
            {viewMode === 'files' ? 'Workspace Files' : 'File Diffs'}
          </span>
          {viewMode === 'files' && files.length > 0 && (
            <span className="text-xs px-2 py-0.5 rounded-full bg-[var(--primary)] text-white">
              {files.length}
            </span>
          )}
          {viewMode === 'diffs' && fileDiffs.length > 0 && (
            <span className="text-xs px-2 py-0.5 rounded-full bg-[var(--primary)] text-white">
              {fileDiffs.length}
            </span>
          )}
        </div>

        {/* View mode toggle */}
        <div className="flex items-center gap-1 bg-[var(--surface-secondary)] rounded p-0.5">
          <button
            onClick={() => setViewMode('files')}
            className={`px-2 py-1 text-xs rounded transition-colors ${
              viewMode === 'files'
                ? 'bg-[var(--primary)] text-white'
                : 'text-[var(--text-secondary)] hover:bg-[var(--surface-elevated)]'
            }`}
          >
            Files
          </button>
          <button
            onClick={() => setViewMode('diffs')}
            className={`px-2 py-1 text-xs rounded transition-colors ${
              viewMode === 'diffs'
                ? 'bg-[var(--primary)] text-white'
                : 'text-[var(--text-secondary)] hover:bg-[var(--surface-elevated)]'
            }`}
          >
            Diffs
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4">
        {viewMode === 'files' ? (
          // Files view
          <>
            {isLoading && files.length === 0 ? (
              <div className="text-sm text-[var(--text-secondary)] text-center py-8">
                <div className="animate-spin mb-2 mx-auto w-5 h-5 border-2 border-[var(--primary)] border-t-transparent rounded-full"></div>
                Loading files...
              </div>
            ) : error ? (
              <div className="text-sm text-[var(--error)] text-center py-4">{error}</div>
            ) : files.length === 0 ? (
              <div className="text-sm text-[var(--text-secondary)] text-center py-8">
                <svg className="w-12 h-12 mx-auto mb-3 opacity-30" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                No workspace files yet.
                <div className="text-xs mt-2 opacity-70">
                  Ask the agent to create files using filesystem tools.
                </div>
              </div>
            ) : (
              <div className="space-y-4">
                {Object.entries(fileGroups).map(([dir, dirFiles]) => (
                  <div key={dir} className="border border-[var(--border)] rounded-lg overflow-hidden">
                    {/* Directory header */}
                    <div className="px-3 py-2 bg-[var(--surface-secondary)] text-xs font-semibold text-[var(--text-secondary)] flex items-center gap-2">
                      <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
                      </svg>
                      {dir === 'root' ? './' : dir + '/'}
                    </div>

                    {/* Files in directory */}
                    <div className="divide-y divide-[var(--border)]">
                      {dirFiles.map((file) => (
                        <div
                          key={file.id}
                          className="group flex items-center justify-between p-3 hover:bg-[var(--surface-elevated)] transition-colors cursor-pointer"
                          onClick={() => setSelectedFile(file)}
                        >
                          <div className="flex items-center gap-3 flex-1 min-w-0">
                            <span className="text-lg">{getFileIcon(file.file_type, file.name)}</span>
                            <div className="flex-1 min-w-0">
                              <div className="text-sm font-medium text-[var(--text-primary)] truncate">
                                {file.name}
                              </div>
                              <div className="text-xs text-[var(--text-secondary)]">
                                {formatSize(file.size)}
                              </div>
                            </div>
                          </div>
                          <svg className="w-4 h-4 text-[var(--text-secondary)] opacity-0 group-hover:opacity-100 transition-opacity" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                          </svg>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </>
        ) : (
          // Diffs view
          <>
            {fileDiffs.length === 0 ? (
              <div className="text-sm text-[var(--text-secondary)] text-center py-8">
                <svg className="w-12 h-12 mx-auto mb-3 opacity-30" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
                </svg>
                No file changes yet.
                <div className="text-xs mt-2 opacity-70">
                  Diffs will appear when files are modified.
                </div>
              </div>
            ) : (
              <div className="space-y-2">
                {fileDiffs.slice().reverse().map((diff) => (
                  <div
                    key={diff.id}
                    className="border border-[var(--border)] rounded-lg overflow-hidden hover:border-[var(--primary)] transition-colors cursor-pointer"
                    onClick={() => setSelectedDiff(diff)}
                  >
                    <div className="px-3 py-2 bg-[var(--surface-secondary)] flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className={`text-xs px-1.5 py-0.5 rounded font-medium ${
                          diff.changeType === 'added' ? 'bg-[var(--success)] text-white' :
                          diff.changeType === 'modified' ? 'bg-[var(--warning)] text-black' :
                          'bg-[var(--error)] text-white'
                        }`}>
                          {diff.changeType.toUpperCase()}
                        </span>
                        <span className="text-sm font-medium text-[var(--text-primary)]">
                          {diff.fileName}
                        </span>
                      </div>
                      <span className="text-xs text-[var(--text-secondary)]">
                        {new Date(diff.timestamp).toLocaleTimeString()}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </>
        )}
      </div>

      {/* File Preview Modal */}
      {selectedFile && (
        <div className="fixed inset-0 bg-black/50 z-30 flex items-center justify-center p-4" onClick={() => setSelectedFile(null)}>
          <div className="bg-[var(--bg-primary)] border border-[var(--border)] rounded-lg w-full max-w-2xl max-h-[80vh] flex flex-col shadow-2xl" onClick={(e) => e.stopPropagation()}>
            {/* Modal Header */}
            <div className="px-4 py-3 border-b border-[var(--border)] flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-lg">{getFileIcon(selectedFile.file_type, selectedFile.name)}</span>
                <span className="text-sm font-semibold text-[var(--text-primary)]">{selectedFile.name}</span>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => {
                    const blob = new Blob([selectedFile.content], { type: 'text/plain' })
                    const url = URL.createObjectURL(blob)
                    const a = document.createElement('a')
                    a.href = url
                    a.download = selectedFile.name
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
                <button
                  onClick={() => setSelectedFile(null)}
                  className="p-1.5 hover:bg-[var(--surface-elevated)] rounded transition-colors"
                >
                  <svg className="w-4 h-4 text-[var(--text-primary)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>

            {/* File Content */}
            <div className="flex-1 overflow-auto p-4 bg-[var(--bg-secondary)]">
              <pre className="text-xs font-mono whitespace-pre-wrap break-all text-[var(--text-primary)]">
                {selectedFile.content || '(No content available)'}
              </pre>
            </div>

            {/* Footer */}
            <div className="px-4 py-2 border-t border-[var(--border)] text-xs text-[var(--text-secondary)] flex justify-between">
              <span>Path: {selectedFile.path}</span>
              <span>Size: {formatSize(selectedFile.size)}</span>
            </div>
          </div>
        </div>
      )}

      {/* Diff Viewer Modal */}
      {selectedDiff && (
        <div className="fixed inset-0 bg-black/50 z-30 flex items-center justify-center p-4" onClick={() => setSelectedDiff(null)}>
          <div className="bg-[var(--bg-primary)] border border-[var(--border)] rounded-lg w-full max-w-4xl max-h-[85vh] flex flex-col shadow-2xl" onClick={(e) => e.stopPropagation()}>
            {/* Modal Header */}
            <div className="px-4 py-3 border-b border-[var(--border)] flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className={`text-xs px-1.5 py-0.5 rounded font-medium ${
                  selectedDiff.changeType === 'added' ? 'bg-[var(--success)] text-white' :
                  selectedDiff.changeType === 'modified' ? 'bg-[var(--warning)] text-black' :
                  'bg-[var(--error)] text-white'
                }`}>
                  {selectedDiff.changeType.toUpperCase()}
                </span>
                <span className="text-sm font-semibold text-[var(--text-primary)]">{selectedDiff.fileName}</span>
                <span className="text-xs text-[var(--text-secondary)]">
                  {new Date(selectedDiff.timestamp).toLocaleString()}
                </span>
              </div>
              <button
                onClick={() => setSelectedDiff(null)}
                className="p-1.5 hover:bg-[var(--surface-elevated)] rounded transition-colors"
              >
                <svg className="w-4 h-4 text-[var(--text-primary)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Diff Content - Side by Side */}
            <div className="flex-1 overflow-auto p-4 bg-[var(--bg-secondary)]">
              {selectedDiff.changeType === 'added' ? (
                <div className="space-y-2">
                  <div className="text-xs font-semibold text-[var(--success)]">New Content:</div>
                  <pre className="text-xs font-mono whitespace-pre-wrap bg-[var(--bg-primary)] p-3 rounded text-[var(--text-primary)]">
                    {selectedDiff.newContent}
                  </pre>
                </div>
              ) : selectedDiff.changeType === 'deleted' ? (
                <div className="space-y-2">
                  <div className="text-xs font-semibold text-[var(--error)]">Deleted Content:</div>
                  <pre className="text-xs font-mono whitespace-pre-wrap bg-[var(--bg-primary)] p-3 rounded text-[var(--text-primary)] line-through opacity-70">
                    {selectedDiff.oldContent}
                  </pre>
                </div>
              ) : (
                // Modified - show side by side
                <div className="space-y-3">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <div className="text-xs font-semibold text-[var(--text-secondary)] mb-2">Original</div>
                      <div className="text-xs font-mono whitespace-pre-wrap bg-[var(--bg-primary)] p-3 rounded">
                        {getDiffLines(selectedDiff).map((line, idx) => (
                          <div key={idx} className={line.type === 'removed' ? 'bg-[var(--error)]/20 text-[var(--error)]' : line.type === 'same' ? '' : 'opacity-30'}>
                            {line.content || ' '}
                          </div>
                        ))}
                      </div>
                    </div>
                    <div>
                      <div className="text-xs font-semibold text-[var(--text-secondary)] mb-2">Modified</div>
                      <div className="text-xs font-mono whitespace-pre-wrap bg-[var(--bg-primary)] p-3 rounded">
                        {getDiffLines(selectedDiff).map((line, idx) => (
                          <div key={idx} className={line.type === 'added' ? 'bg-[var(--success)]/20 text-[var(--success)]' : line.type === 'same' ? '' : 'opacity-30'}>
                            {line.content || ' '}
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="px-4 py-2 border-t border-[var(--border)] text-xs text-[var(--text-secondary)] flex justify-between">
              <span>Lines changed</span>
              <span className="flex items-center gap-3">
                <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-[var(--success)]"></span>Added</span>
                <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-[var(--error)]"></span>Removed</span>
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
