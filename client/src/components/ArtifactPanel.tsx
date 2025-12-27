import { useEffect, useState } from 'react'
import { useUIStore } from '../stores/uiStore'
import { useArtifactStore } from '../stores/artifactStore'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism'

interface Artifact {
  id: string
  title: string
  content: string
  language: string
  version: number
  createdAt: string
}

export function ArtifactPanel() {
  const { panelOpen, setPanelOpen } = useUIStore()
  const { artifacts, currentArtifactId, setCurrentArtifactId, removeArtifact } = useArtifactStore()
  const [copiedCode, setCopiedCode] = useState<string | null>(null)

  // Get current artifact
  const currentArtifact = artifacts.find(a => a.id === currentArtifactId) || artifacts[0] || null

  useEffect(() => {
    // Auto-open panel when artifacts are detected
    if (artifacts.length > 0 && !panelOpen) {
      setPanelOpen(true)
    }
  }, [artifacts.length, panelOpen, setPanelOpen])

  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text)
      setCopiedCode('copied')
      setTimeout(() => setCopiedCode(null), 2000)
    } catch (err) {
      console.error('Failed to copy:', err)
    }
  }

  const downloadArtifact = (artifact: Artifact) => {
    const blob = new Blob([artifact.content], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${artifact.title}.${artifact.language.toLowerCase().replace('/', '-')}.txt`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  if (!panelOpen || artifacts.length === 0) {
    return null
  }

  return (
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
          onClick={() => setPanelOpen(false)}
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
              <div className="flex items-center justify-between">
                <span className="text-xs text-[var(--text-secondary)]">{artifact.language}</span>
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
              <div className="flex items-center justify-between px-4 py-2 border-b border-[var(--border-primary)] bg-[var(--bg-secondary)]">
                <div className="flex items-center gap-2">
                  <span className="font-medium text-[var(--text-primary)]">
                    {currentArtifact.title}
                  </span>
                  <span className="text-xs px-2 py-0.5 bg-[var(--bg-tertiary)] rounded text-[var(--text-secondary)]">
                    {currentArtifact.language}
                  </span>
                </div>
                <div className="flex gap-1">
                  <button
                    onClick={() => copyToClipboard(currentArtifact.content)}
                    className="p-1.5 hover:bg-[var(--bg-tertiary)] rounded text-sm transition-colors"
                    title="Copy code"
                  >
                    {copiedCode ? '✓' : '📋'}
                  </button>
                  <button
                    onClick={() => downloadArtifact(currentArtifact)}
                    className="p-1.5 hover:bg-[var(--bg-tertiary)] rounded text-sm transition-colors"
                    title="Download"
                  >
                    ⬇️
                  </button>
                  <button
                    onClick={() => removeArtifact(currentArtifact.id)}
                    className="p-1.5 hover:bg-[var(--bg-tertiary)] rounded text-sm transition-colors text-red-400"
                    title="Delete"
                  >
                    🗑️
                  </button>
                </div>
              </div>

              {/* Code Display */}
              <div className="flex-1 overflow-auto bg-[var(--bg-primary)]">
                <SyntaxHighlighter
                  language={mapLanguageForHighlighter(currentArtifact.language)}
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
                  {currentArtifact.content}
                </SyntaxHighlighter>
              </div>

              {/* Metadata */}
              <div className="px-4 py-2 border-t border-[var(--border-primary)] bg-[var(--bg-secondary)] text-xs text-[var(--text-secondary)]">
                <div>Created: {new Date(currentArtifact.createdAt).toLocaleString()}</div>
                <div>Version: {currentArtifact.version}</div>
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
