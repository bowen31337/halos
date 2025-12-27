import { useState } from 'react'

interface JsonViewerProps {
  data: any
  expanded?: boolean
  onCopy?: (path: string, value: any) => void
}

interface TreeNodeProps {
  data: any
  keyName?: string
  isLast: boolean
  onCopy?: (path: string, value: any) => void
  path: string
}

function TreeNode({ data, keyName, isLast, onCopy, path }: TreeNodeProps) {
  const [isExpanded, setIsExpanded] = useState(false)
  const isObject = data !== null && typeof data === 'object'
  const isArray = Array.isArray(data)
  const isEmpty = isObject && Object.keys(data).length === 0

  const getTypeColor = (value: any) => {
    if (value === null) return 'text-gray-500'
    if (typeof value === 'string') return 'text-green-600 dark:text-green-400'
    if (typeof value === 'number') return 'text-blue-600 dark:text-blue-400'
    if (typeof value === 'boolean') return 'text-orange-600 dark:text-orange-400'
    return 'text-gray-700 dark:text-gray-300'
  }

  const handleCopy = (value: any) => {
    if (onCopy) {
      onCopy(path, value)
    } else {
      navigator.clipboard.writeText(JSON.stringify(value, null, 2))
    }
  }

  const renderValue = () => {
    if (data === null) return <span className="text-gray-500">null</span>
    if (typeof data === 'string') return <span className="text-green-600 dark:text-green-400">"{data}"</span>
    if (typeof data === 'number') return <span className="text-blue-600 dark:text-blue-400">{data}</span>
    if (typeof data === 'boolean') return <span className="text-orange-600 dark:text-orange-400">{String(data)}</span>
    return null
  }

  if (!isObject) {
    return (
      <div className="pl-4">
        {keyName && (
          <span className="text-purple-600 dark:text-purple-400 font-medium">
            "{keyName}"
          </span>
        )}
        {keyName && <span className="text-gray-500">: </span>}
        {renderValue()}
        {!isLast && <span className="text-gray-500">,</span>}
      </div>
    )
  }

  if (isEmpty) {
    return (
      <div className="pl-4">
        {keyName && (
          <span className="text-purple-600 dark:text-purple-400 font-medium">
            "{keyName}"
          </span>
        )}
        {keyName && <span className="text-gray-500">: </span>}
        <span className="text-gray-500">{isArray ? '[]' : '{}'}</span>
        {!isLast && <span className="text-gray-500">,</span>}
      </div>
    )
  }

  const keys = Object.keys(data)
  const bracketOpen = isArray ? '[' : '{'
  const bracketClose = isArray ? ']' : '}'

  return (
    <div className="pl-4">
      <div className="flex items-center gap-1">
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="p-0.5 hover:bg-gray-200 dark:hover:bg-gray-700 rounded transition-colors"
          aria-label={isExpanded ? 'Collapse' : 'Expand'}
        >
          <svg
            className={`w-3 h-3 transition-transform ${isExpanded ? 'rotate-90' : ''}`}
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path d="M6 6L14 10L6 14V6Z" />
          </svg>
        </button>
        {keyName && (
          <>
            <span className="text-purple-600 dark:text-purple-400 font-medium">
              "{keyName}"
            </span>
            <span className="text-gray-500">: </span>
          </>
        )}
        <span className="text-gray-500">{bracketOpen}</span>
        <span className="text-gray-400 text-sm">
          {keys.length} {keys.length === 1 ? 'item' : 'items'}
        </span>
        <span className="text-gray-500">{bracketClose}</span>
        {!isLast && <span className="text-gray-500">,</span>}
        <button
          onClick={() => handleCopy(data)}
          className="p-0.5 hover:bg-gray-200 dark:hover:bg-gray-700 rounded transition-colors ml-2"
          title="Copy value"
        >
          <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
          </svg>
        </button>
      </div>

      {isExpanded && (
        <div className="border-l border-gray-300 dark:border-gray-600 ml-1.5 mt-1">
          {keys.map((key, index) => (
            <TreeNode
              key={key}
              data={data[key]}
              keyName={isArray ? undefined : key}
              isLast={index === keys.length - 1}
              onCopy={onCopy}
              path={path ? (isArray ? `${path}[${key}]` : `${path}.${key}`) : key}
            />
          ))}
        </div>
      )}
    </div>
  )
}

export function JsonViewer({ data, expanded = false, onCopy }: JsonViewerProps) {
  const [parsedData, setParsedData] = useState<any>(() => {
    try {
      if (typeof data === 'string') {
        return JSON.parse(data)
      }
      return data
    } catch (error) {
      console.error('Failed to parse JSON:', error)
      return null
    }
  })

  const [viewMode, setViewMode] = useState<'tree' | 'raw'>('tree')
  const [searchQuery, setSearchQuery] = useState('')
  const [copySuccess, setCopySuccess] = useState(false)

  if (parsedData === null) {
    return (
      <div className="p-4 text-red-500">
        Invalid JSON data
      </div>
    )
  }

  const handleCopyAll = async () => {
    try {
      await navigator.clipboard.writeText(JSON.stringify(parsedData, null, 2))
      setCopySuccess(true)
      setTimeout(() => setCopySuccess(false), 2000)
    } catch (err) {
      console.error('Failed to copy:', err)
    }
  }

  const handleCopyPath = (path: string, value: any) => {
    const valueStr = JSON.stringify(value, null, 2)
    navigator.clipboard.writeText(`// ${path}\n${valueStr}`)
  }

  return (
    <div className="h-full flex flex-col bg-white dark:bg-gray-900">
      {/* Toolbar */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
            JSON Viewer
          </span>
          <div className="flex bg-gray-200 dark:bg-gray-700 rounded p-0.5">
            <button
              onClick={() => setViewMode('tree')}
              className={`px-3 py-1 text-xs rounded transition-colors ${
                viewMode === 'tree'
                  ? 'bg-white dark:bg-gray-600 text-gray-900 dark:text-white shadow'
                  : 'text-gray-600 dark:text-gray-400'
              }`}
            >
              Tree
            </button>
            <button
              onClick={() => setViewMode('raw')}
              className={`px-3 py-1 text-xs rounded transition-colors ${
                viewMode === 'raw'
                  ? 'bg-white dark:bg-gray-600 text-gray-900 dark:text-white shadow'
                  : 'text-gray-600 dark:text-gray-400'
              }`}
            >
              Raw
            </button>
          </div>
        </div>
        <button
          onClick={handleCopyAll}
          className="px-3 py-1 text-xs bg-blue-500 hover:bg-blue-600 text-white rounded transition-colors flex items-center gap-1"
        >
          {copySuccess ? '✓ Copied!' : '📋 Copy All'}
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto p-4">
        {viewMode === 'tree' ? (
          <TreeNode
            data={parsedData}
            onCopy={handleCopyPath}
            path=""
            isLast={true}
          />
        ) : (
          <pre className="text-sm font-mono text-gray-800 dark:text-gray-200 whitespace-pre-wrap">
            {JSON.stringify(parsedData, null, 2)}
          </pre>
        )}
      </div>

      {/* Stats Footer */}
      <div className="px-4 py-2 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 text-xs text-gray-600 dark:text-gray-400">
        {typeof parsedData === 'object' && parsedData !== null && (
          <span>
            {Array.isArray(parsedData)
              ? `${parsedData.length} items in array`
              : `${Object.keys(parsedData).length} keys in object`}
            {' • '}
            {JSON.stringify(parsedData).length} bytes
          </span>
        )}
      </div>
    </div>
  )
}
