import { useEffect, useRef, useState } from 'react'

interface MonacoEditorProps {
  value: string
  language?: string
  onChange?: (value: string) => void
  readOnly?: boolean
  theme?: 'vs' | 'vs-dark' | 'hc-black'
  height?: string | number
}

/**
 * MonacoEditor Component
 *
 * Note: This component requires Monaco Editor to be loaded.
 * It will attempt to load Monaco from a CDN if not available.
 *
 * For production use, consider adding @monaco-editor/react to package.json:
 * npm install @monaco-editor/react
 */

declare global {
  interface Window {
    monaco?: any
    require?: any
  }
}

export function MonacoEditor({
  value,
  language = 'typescript',
  onChange,
  readOnly = false,
  theme = 'vs-dark',
  height = '400px',
}: MonacoEditorProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const editorRef = useRef<any>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Load Monaco Editor from CDN
  useEffect(() => {
    const loadMonaco = async () => {
      // Check if already loaded
      if (window.monaco) {
        setIsLoading(false)
        return
      }

      // Check if require is available
      if (!window.require) {
        // Load require.js first
        const requireScript = document.createElement('script')
        requireScript.src = 'https://cdnjs.cloudflare.com/ajax/libs/require.js/2.3.6/require.min.js'
        await new Promise((resolve, reject) => {
          requireScript.onload = resolve
          requireScript.onerror = () => reject(new Error('Failed to load require.js'))
          document.head.appendChild(requireScript)
        })
      }

      // Configure require paths
      window.require.config({
        paths: { vs: 'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.44.0/min/vs' },
      })

      // Load Monaco
      await new Promise((resolve, reject) => {
        window.require(['vs/editor/editor.main'], () => {
          resolve(window.monaco)
        }, (err: any) => {
          reject(err)
        })
      })

      setIsLoading(false)
    }

    loadMonaco().catch((err) => {
      console.error('Failed to load Monaco Editor:', err)
      setError('Failed to load Monaco Editor. Please add @monaco-editor/react to dependencies.')
    })
  }, [])

  // Initialize editor
  useEffect(() => {
    if (!containerRef.current || !window.monaco || isLoading || error) return

    // Create editor if not exists
    if (!editorRef.current) {
      editorRef.current = window.monaco.editor.create(containerRef.current, {
        value,
        language,
        readOnly,
        theme,
        automaticLayout: true,
        minimap: { enabled: false },
        scrollBeyondLastLine: false,
        fontSize: 13,
        fontFamily: "'JetBrains Mono', 'Fira Code', 'Consolas', monospace",
      })

      // Add change listener
      if (onChange && editorRef.current) {
        editorRef.current.onDidChangeModelContent(() => {
          onChange(editorRef.current.getValue())
        })
      }
    } else {
      // Update value if changed
      const currentValue = editorRef.current.getValue()
      if (currentValue !== value) {
        editorRef.current.setValue(value)
      }

      // Update language
      const model = editorRef.current.getModel()
      if (model) {
        window.monaco.editor.setModelLanguage(model, language)
      }

      // Update theme
      window.monaco.editor.setTheme(theme)
    }

    return () => {
      if (editorRef.current) {
        editorRef.current.dispose()
        editorRef.current = null
      }
    }
  }, [value, language, readOnly, theme, isLoading, error, onChange])

  if (error) {
    return (
      <div className=\"p-4 border border-red-300 bg-red-50 text-red-700 rounded-lg text-sm\">
        <p className=\"font-semibold mb-2\">Monaco Editor Error</p>
        <p>{error}</p>
        <p className=\"mt-2 text-xs\">To fix: <code>npm install @monaco-editor/react</code></p>
        <p className=\"text-xs mt-1\">Or use the fallback code editor below:</p>
        <textarea
          className=\"mt-2 w-full h-32 p-2 border rounded font-mono text-xs\"
          value={value}
          onChange={(e) => onChange?.(e.target.value)}
          readOnly={readOnly}
        />
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className=\"flex items-center justify-center\" style={{ height: typeof height === 'number' ? `${height}px` : height }}>
        <div className=\"text-center\">
          <div className=\"animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-2\"></div>
          <div className=\"text-sm text-gray-500\">Loading Monaco Editor...</div>
        </div>
      </div>
    )
  }

  return (
    <div
      ref={containerRef}
      style={{ height: typeof height === 'number' ? `${height}px` : height }}
      className=\"border border-[var(--border)] rounded-lg overflow-hidden\"
    />
  )
}
