import { useState, useEffect, useRef } from 'react'
import { useUIStore } from '../stores/uiStore'
import { useArtifactStore, Artifact } from '../stores/artifactStore'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism'

export function ArtifactPanel() {
  const { setPanelType } = useUIStore()
  const {
    artifacts,
    currentArtifactId,
    setCurrentArtifactId,
    deleteArtifact,
    updateArtifact,
    forkArtifact,
    getArtifactVersions,
    versions,
    downloadArtifact: downloadArtifactAPI
  } = useArtifactStore()

  const [copiedCode, setCopiedCode] = useState<string | null>(null)
  const [showEditModal, setShowEditModal] = useState(false)
  const [showVersionModal, setShowVersionModal] = useState(false)
  const [editContent, setEditContent] = useState('')
  const [editTitle, setEditTitle] = useState('')
  const [isEditing, setIsEditing] = useState(false)
  const [mermaidReady, setMermaidReady] = useState(false)
  const mermaidRef = useRef<HTMLDivElement>(null)

  // Get current artifact
  const currentArtifact = artifacts.find(a => a.id === currentArtifactId) || artifacts[0] || null

  // Load Mermaid.js dynamically when needed
  useEffect(() => {
    if (currentArtifact?.artifact_type === 'mermaid') {
      // Check if mermaid is already loaded
      if (typeof window !== 'undefined' && (window as any).mermaid) {
        setMermaidReady(true)
        return
      }

      // Load mermaid script from CDN
      const script = document.createElement('script')
      script.src = 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js'
      script.onload = () => {
        if (typeof window !== 'undefined') {
          (window as any).mermaid.initialize({ startOnLoad: false, theme: 'dark' })
          setMermaidReady(true)
        }
      }
      document.head.appendChild(script)

      return () => {
        if (script.parentNode) {
          script.parentNode.removeChild(script)
        }
      }
    } else {
      setMermaidReady(false)
    }
  }, [currentArtifact?.artifact_type])

  // Render Mermaid diagram when ready
  useEffect(() => {
    if (
      currentArtifact?.artifact_type === 'mermaid' &&
      mermaidReady &&
      mermaidRef.current
    ) {
      const mermaid = (window as any).mermaid
      if (mermaid) {
        // Generate a unique ID for the mermaid element
        const id = `mermaid-${currentArtifact.id}`

        // Clear previous content
        mermaidRef.current.innerHTML = ''

        // Create mermaid container
        const container = document.createElement('div')
        container.id = id
        container.className = 'mermaid'
        container.textContent = currentArtifact.content
        mermaidRef.current.appendChild(container)

        // Render
        mermaid.render(id, currentArtifact.content, (svgCode: string) => {
          container.innerHTML = svgCode
        })
      }
    }
  }, [currentArtifact?.id, currentArtifact?.content, mermaidReady])

  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text)
      setCopiedCode('copied')
      setTimeout(() => setCopiedCode(null), 2000)
    } catch (err) {
      console.error('Failed to copy:', err)
    }
  }

  const handleDownload = async () => {
    if (!currentArtifact) return
    try {
      const data = await downloadArtifactAPI(currentArtifact.id)

      // Determine proper filename extension based on artifact type
      let filename = data.filename
      if (currentArtifact.artifact_type === 'svg') {
        filename = `${currentArtifact.title}.svg`
      } else if (currentArtifact.artifact_type === 'html') {
        filename = `${currentArtifact.title}.html`
      } else if (currentArtifact.artifact_type === 'mermaid') {
        filename = `${currentArtifact.title}.mmd`
      } else if (currentArtifact.artifact_type === 'latex') {
        filename = `${currentArtifact.title}.tex`
      }

      // Determine content type
      let contentType = data.content_type
      if (currentArtifact.artifact_type === 'svg') {
        contentType = 'image/svg+xml'
      } else if (currentArtifact.artifact_type === 'html') {
        contentType = 'text/html'
      }

      const blob = new Blob([data.content], { type: contentType })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    } catch (err) {
      console.error('Download failed:', err)
      // Fallback to client-side download
      const blob = new Blob([currentArtifact.content], { type: 'text/plain' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${currentArtifact.title}.${currentArtifact.language.toLowerCase().replace('/', '-')}.txt`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    }
  }

  const handleDelete = async () => {
    if (!currentArtifact) return
    if (confirm(`Delete artifact "${currentArtifact.title}"?`)) {
      try {
        await deleteArtifact(currentArtifact.id)
      } catch (err) {
        console.error('Delete failed:', err)
      }
    }
  }

  const handleEdit = async () => {
    if (!currentArtifact) return
    setIsEditing(true)
    try {
      await updateArtifact(currentArtifact.id, {
        content: editContent,
        title: editTitle
      })
      setShowEditModal(false)
    } catch (err) {
      console.error('Update failed:', err)
    } finally {
      setIsEditing(false)
    }
  }

  const handleFork = async () => {
    if (!currentArtifact) return
    try {
      await forkArtifact(currentArtifact.id)
    } catch (err) {
      console.error('Fork failed:', err)
    }
  }

  const handleShowVersions = async () => {
    if (!currentArtifact) return
    try {
      await getArtifactVersions(currentArtifact.id)
      setShowVersionModal(true)
    } catch (err) {
      console.error('Get versions failed:', err)
    }
  }

  const openEditModal = () => {
    if (!currentArtifact) return
    setEditContent(currentArtifact.content)
    setEditTitle(currentArtifact.title)
    setShowEditModal(true)
  }

  const closePanel = () => {
    setPanelType(null)
  }

  // Render content based on artifact type
  const renderContent = () => {
    if (!currentArtifact) return null

    const { artifact_type, content, language } = currentArtifact

    // HTML Preview (Feature #39)
    if (artifact_type === 'html') {
      return (
        <div className="flex-1 overflow-auto bg-white">
          <iframe
            srcDoc={content}
            className="w-full h-full border-0"
            title="HTML Preview"
            sandbox="allow-scripts"
          />
        </div>
      )
    }

    // SVG Rendering (Feature #40)
    if (artifact_type === 'svg') {
      return (
        <div className="flex-1 overflow-auto bg-[var(--bg-primary)] flex items-center justify-center p-4">
          <div
            className="w-full max-w-full"
            dangerouslySetInnerHTML={{ __html: content }}
          />
        </div>
      )
    }

    // Mermaid Diagram (Feature #41)
    if (artifact_type === 'mermaid') {
      return (
        <div className="flex-1 overflow-auto bg-[var(--bg-primary)] p-4">
          <div ref={mermaidRef} className="flex justify-center items-center min-h-[200px]">
            {!mermaidReady ? (
              <div className="text-[var(--text-secondary)] text-sm">
                Loading Mermaid renderer...
              </div>
            ) : (
              <div className="text-[var(--text-secondary)] text-sm">
                Rendering diagram...
              </div>
            )}
          </div>
        </div>
      )
    }

    // Code Display (default)
    return (
      <div className="flex-1 overflow-auto bg-[var(--bg-primary)]">
        <SyntaxHighlighter
          language={mapLanguageForHighlighter(language)}
          style={oneDark}
          customStyle={{
            margin: 0,
            padding: '1rem',
            background: 'var(--bg-primary)',
            fontSize: '0.875rem',
            lineHeight: '1.5',
          }}
          codeTagProps={{
            style: {
              fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace',
            }
          }}
        >
          {content}
        </SyntaxHighlighter>
      </div>
    )
  }

  if (artifacts.length === 0) {
    return null
  }

  return (
    <>
      <div className="fixed right-0 top-[60px] bottom-0 w-[450px] bg-[var(--bg-primary)] border-l border-[var(--border-primary)] flex flex-col shadow-xl z-30">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-[var(--border-primary)] bg-[var(--bg-secondary)]">
          <div className="flex items-center gap-2">
            <span className="text-lg">📦</span>
            <span className="font-semibold text-[var(--text-primary)]">Artifacts</span>
            <span className="text-xs px-2 py-0.5 bg-[var(--bg-tertiary)] rounded-full text-[var(--text-secondary)]">
              {artifacts.length}
            </span>
          </div>
          <button
            onClick={closePanel}
            className="p-1 hover:bg-[var(--bg-tertiary)] rounded transition-colors"
            title="Close panel"
          >
            ✕
          </button>
        </div>

        {/* Content */}
        <div className="flex flex-1 overflow-hidden">
          {/* Artifact List */}
          <div className="w-1/3 border-r border-[var(--border-primary)] overflow-y-auto">
            {artifacts.map((artifact) => (
              <div
                key={artifact.id}
                onClick={() => setCurrentArtifactId(artifact.id)}
                className={`p-3 cursor-pointer border-b border-[var(--border-primary)] hover:bg-[var(--bg-secondary)] transition-colors ${
                  currentArtifactId === artifact.id ? 'bg-[var(--bg-secondary)] border-l-2 border-l-[var(--primary)]' : ''
                }`}
              >
                <div className="text-sm font-medium text-[var(--text-primary)] mb-1 truncate">
                  {artifact.title}
                </div>
                <div className="flex items-center justify-between gap-1">
                  <span className="text-xs text-[var(--text-secondary)] truncate">
                    {artifact.artifact_type || 'code'}
                  </span>
                  <span className="text-xs text-[var(--text-secondary)]">v{artifact.version}</span>
                </div>
              </div>
            ))}
          </div>

          {/* Artifact Detail */}
          <div className="flex-1 flex flex-col overflow-hidden">
            {currentArtifact ? (
              <>
                {/* Artifact Actions */}
                <div className="flex items-center justify-between px-4 py-2 border-b border-[var(--border-primary)] bg-[var(--bg-secondary)] flex-wrap gap-2">
                  <div className="flex items-center gap-2 flex-1 min-w-0">
                    <span className="font-medium text-[var(--text-primary)] truncate">
                      {currentArtifact.title}
                    </span>
                    <span className="text-xs px-2 py-0.5 bg-[var(--bg-tertiary)] rounded text-[var(--text-secondary)] whitespace-nowrap">
                      {currentArtifact.language}
                    </span>
                    {currentArtifact.artifact_type !== 'code' && (
                      <span className="text-xs px-2 py-0.5 bg-[var(--primary)]/20 text-[var(--primary)] rounded whitespace-nowrap">
                        {currentArtifact.artifact_type}
                      </span>
                    )}
                  </div>
                  <div className="flex gap-1 flex-wrap">
                    <button
                      onClick={() => copyToClipboard(currentArtifact.content)}
                      className="p-1.5 hover:bg-[var(--bg-tertiary)] rounded text-sm transition-colors"
                      title="Copy code"
                    >
                      {copiedCode ? '✓' : '📋'}
                    </button>
                    <button
                      onClick={handleDownload}
                      className="p-1.5 hover:bg-[var(--bg-tertiary)] rounded text-sm transition-colors"
                      title="Download"
                    >
                      ⬇️
                    </button>
                    <button
                      onClick={openEditModal}
                      className="p-1.5 hover:bg-[var(--bg-tertiary)] rounded text-sm transition-colors"
                      title="Edit artifact"
                    >
                      ✏️
                    </button>
                    <button
                      onClick={handleFork}
                      className="p-1.5 hover:bg-[var(--bg-tertiary)] rounded text-sm transition-colors"
                      title="Fork artifact"
                    >
                      🾱
                    </button>
                    <button
                      onClick={handleShowVersions}
                      className="p-1.5 hover:bg-[var(--bg-tertiary)] rounded text-sm transition-colors"
                      title="Version history"
                    >
                      🕐
                    </button>
                    <button
                      onClick={handleDelete}
                      className="p-1.5 hover:bg-[var(--bg-tertiary)] rounded text-sm transition-colors text-red-400"
                      title="Delete"
                    >
                      🗑️
                    </button>
                  </div>
                </div>

                {/* Content Display */}
                {renderContent()}

                {/* Metadata */}
                <div className="px-4 py-2 border-t border-[var(--border-primary)] bg-[var(--bg-secondary)] text-xs text-[var(--text-secondary)]">
                  <div>Created: {new Date(currentArtifact.createdAt).toLocaleString()}</div>
                  <div>Version: {currentArtifact.version}</div>
                  {currentArtifact.parentArtifactId && (
                    <div>Parent: {currentArtifact.parentArtifactId.slice(0, 8)}...</div>
                  )}
                </div>
              </>
            ) : (
              <div className="flex items-center justify-center h-full text-[var(--text-secondary)]">
                <div className="text-center">
                  <div className="text-4xl mb-2">📦</div>
                  <div>No artifact selected</div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Edit Modal */}
      {showEditModal && currentArtifact && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-[var(--bg-primary)] border border-[var(--border-primary)] rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] flex flex-col">
            <div className="px-4 py-3 border-b border-[var(--border-primary)] flex items-center justify-between">
              <h3 className="font-semibold text-[var(--text-primary)]">Edit Artifact</h3>
              <button
                onClick={() => setShowEditModal(false)}
                className="p-1 hover:bg-[var(--bg-tertiary)] rounded"
              >
                ✕
              </button>
            </div>
            <div className="p-4 flex-1 overflow-auto space-y-3">
              <div>
                <label className="block text-sm text-[var(--text-secondary)] mb-1">Title</label>
                <input
                  type="text"
                  value={editTitle}
                  onChange={(e) => setEditTitle(e.target.value)}
                  className="w-full px-3 py-2 bg-[var(--bg-secondary)] border border-[var(--border-primary)] rounded text-[var(--text-primary)] focus:outline-none focus:border-[var(--primary)]"
                />
              </div>
              <div>
                <label className="block text-sm text-[var(--text-secondary)] mb-1">Content</label>
                <textarea
                  value={editContent}
                  onChange={(e) => setEditContent(e.target.value)}
                  rows={15}
                  className="w-full px-3 py-2 bg-[var(--bg-secondary)] border border-[var(--border-primary)] rounded text-[var(--text-primary)] font-mono text-sm focus:outline-none focus:border-[var(--primary)] resize-y"
                />
              </div>
            </div>
            <div className="px-4 py-3 border-t border-[var(--border-primary)] flex justify-end gap-2">
              <button
                onClick={() => setShowEditModal(false)}
                className="px-4 py-2 hover:bg-[var(--bg-tertiary)] rounded transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleEdit}
                disabled={isEditing}
                className="px-4 py-2 bg-[var(--primary)] text-white rounded hover:opacity-90 transition-colors disabled:opacity-50"
              >
                {isEditing ? 'Saving...' : 'Save Changes'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Version History Modal */}
      {showVersionModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-[var(--bg-primary)] border border-[var(--border-primary)] rounded-lg shadow-xl max-w-3xl w-full max-h-[90vh] flex flex-col">
            <div className="px-4 py-3 border-b border-[var(--border-primary)] flex items-center justify-between">
              <h3 className="font-semibold text-[var(--text-primary)]">Version History</h3>
              <button
                onClick={() => setShowVersionModal(false)}
                className="p-1 hover:bg-[var(--bg-tertiary)] rounded"
              >
                ✕
              </button>
            </div>
            <div className="flex-1 overflow-auto">
              {versions.length === 0 ? (
                <div className="p-8 text-center text-[var(--text-secondary)]">
                  No versions available
                </div>
              ) : (
                <div className="divide-y divide-[var(--border-primary)]">
                  {versions.map((version) => (
                    <div
                      key={version.id}
                      className="p-4 hover:bg-[var(--bg-secondary)] transition-colors"
                    >
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="font-medium text-[var(--text-primary)]">
                              {version.title}
                            </span>
                            <span className="text-xs px-2 py-0.5 bg-[var(--bg-tertiary)] rounded text-[var(--text-secondary)]">
                              v{version.version}
                            </span>
                            {version.parentArtifactId && (
                              <span className="text-xs text-[var(--text-secondary)]">
                                (fork)
                              </span>
                            )}
                          </div>
                          <div className="text-xs text-[var(--text-secondary)]">
                            {new Date(version.createdAt).toLocaleString()}
                          </div>
                          <div className="text-xs text-[var(--text-secondary)] mt-1 truncate">
                            {version.content.slice(0, 100)}{version.content.length > 100 ? '...' : ''}
                          </div>
                        </div>
                        <button
                          onClick={() => {
                            setCurrentArtifactId(version.id)
                            setShowVersionModal(false)
                          }}
                          className="px-3 py-1 text-sm bg-[var(--primary)]/10 text-[var(--primary)] rounded hover:bg-[var(--primary)]/20 transition-colors"
                        >
                          View
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  )
}

// Map artifact language to syntax highlighter language
function mapLanguageForHighlighter(language: string): string {
  const map: Record<string, string> = {
    'React/JSX': 'jsx',
    'javascript': 'javascript',
    'js': 'javascript',
    'typescript': 'typescript',
    'ts': 'typescript',
    'python': 'python',
    'py': 'python',
    'java': 'java',
    'cpp': 'cpp',
    'c++': 'cpp',
    'csharp': 'csharp',
    'cs': 'csharp',
    'go': 'go',
    'rust': 'rust',
    'rs': 'rust',
    'ruby': 'ruby',
    'rb': 'ruby',
    'php': 'php',
    'swift': 'swift',
    'kotlin': 'kotlin',
    'kt': 'kotlin',
    'html': 'html',
    'css': 'css',
    'json': 'json',
    'yaml': 'yaml',
    'markdown': 'markdown',
    'md': 'markdown',
    'bash': 'bash',
    'shell': 'bash',
    'sql': 'sql',
    'graphql': 'graphql',
    'xml': 'xml',
  }
  return map[language] || 'text'
}
