import { useState, useMemo } from 'react'

interface CsvViewerProps {
  data: string
  editable?: boolean
  onChange?: (data: string) => void
}

export function CsvViewer({ data, editable = false, onChange }: CsvViewerProps) {
  const [viewMode, setViewMode] = useState<'table' | 'raw'>('table')
  const [searchQuery, setSearchQuery] = useState('')
  const [sortConfig, setSortConfig] = useState<{ column: number; direction: 'asc' | 'desc' } | null>(null)
  const [copiedCell, setCopiedCell] = useState<string | null>(null)
  const [editingCell, setEditingCell] = useState<{ row: number; col: number } | null>(null)
  const [cellValue, setCellValue] = useState('')

  // Parse CSV data
  const { headers, rows, totalRows } = useMemo(() => {
    const lines = data.trim().split('\n')
    if (lines.length === 0) return { headers: [], rows: [], totalRows: 0 }

    // Parse CSV lines (handle quoted values)
    const parseLine = (line: string): string[] => {
      const result: string[] = []
      let current = ''
      let inQuotes = false

      for (let i = 0; i < line.length; i++) {
        const char = line[i]
        const nextChar = line[i + 1]

        if (char === '"') {
          if (inQuotes && nextChar === '"') {
            current += '"'
            i++
          } else {
            inQuotes = !inQuotes
          }
        } else if (char === ',' && !inQuotes) {
          result.push(current.trim())
          current = ''
        } else {
          current += char
        }
      }
      result.push(current.trim())
      return result
    }

    const headerRow = parseLine(lines[0])
    const dataRows = lines.slice(1).map(parseLine)

    return {
      headers: headerRow,
      rows: dataRows,
      totalRows: dataRows.length
    }
  }, [data])

  // Filter and sort rows
  const filteredRows = useMemo(() => {
    let filtered = rows

    // Apply search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase()
      filtered = filtered.filter(row =>
        row.some(cell => cell.toLowerCase().includes(query))
      )
    }

    // Apply sorting
    if (sortConfig) {
      filtered = [...filtered].sort((a, b) => {
        const aValue = a[sortConfig.column] || ''
        const bValue = b[sortConfig.column] || ''

        // Try numeric sort first
        const aNum = parseFloat(aValue)
        const bNum = parseFloat(bValue)

        if (!isNaN(aNum) && !isNaN(bNum)) {
          return sortConfig.direction === 'asc' ? aNum - bNum : bNum - aNum
        }

        // Fall back to string sort
        const comparison = aValue.localeCompare(bValue)
        return sortConfig.direction === 'asc' ? comparison : -comparison
      })
    }

    return filtered
  }, [rows, searchQuery, sortConfig])

  const handleSort = (columnIndex: number) => {
    setSortConfig(prev => {
      if (prev?.column === columnIndex) {
        return {
          column: columnIndex,
          direction: prev.direction === 'asc' ? 'desc' : 'asc'
        }
      }
      return { column: columnIndex, direction: 'asc' }
    })
  }

  const handleCopyCell = async (value: string) => {
    try {
      await navigator.clipboard.writeText(value)
      setCopiedCell(value)
      setTimeout(() => setCopiedCell(null), 2000)
    } catch (err) {
      console.error('Failed to copy:', err)
    }
  }

  const handleCellEdit = (rowIndex: number, colIndex: number, value: string) => {
    if (onChange) {
      const updatedRows = [...rows]
      updatedRows[rowIndex][colIndex] = value

      // Reconstruct CSV
      const escapeField = (field: string) => {
        if (field.includes(',') || field.includes('"') || field.includes('\n')) {
          return `"${field.replace(/"/g, '""')}"`
        }
        return field
      }

      const newCsv = [
        headers.map(escapeField).join(','),
        ...updatedRows.map(row => row.map(escapeField).join(','))
      ].join('\n')

      onChange(newCsv)
    }
    setEditingCell(null)
  }

  const handleExportCSV = () => {
    const blob = new Blob([data], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'data.csv'
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  if (totalRows === 0) {
    return (
      <div className="p-4 text-center text-gray-500">
        No data to display
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col bg-white dark:bg-gray-900">
      {/* Toolbar */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
            CSV Viewer
          </span>
          <div className="flex bg-gray-200 dark:bg-gray-700 rounded p-0.5">
            <button
              onClick={() => setViewMode('table')}
              className={`px-3 py-1 text-xs rounded transition-colors ${
                viewMode === 'table'
                  ? 'bg-white dark:bg-gray-600 text-gray-900 dark:text-white shadow'
                  : 'text-gray-600 dark:text-gray-400'
              }`}
            >
              Table
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
        <div className="flex items-center gap-2">
          <input
            type="text"
            placeholder="Search..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="px-2 py-1 text-xs border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
          />
          <button
            onClick={handleExportCSV}
            className="px-3 py-1 text-xs bg-blue-500 hover:bg-blue-600 text-white rounded transition-colors"
          >
            Export
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto">
        {viewMode === 'table' ? (
          <table className="w-full text-sm">
            <thead className="bg-gray-100 dark:bg-gray-800 sticky top-0">
              <tr>
                {headers.map((header, index) => (
                  <th
                    key={index}
                    onClick={() => handleSort(index)}
                    className="px-4 py-2 text-left cursor-pointer hover:bg-gray-200 dark:hover:bg-gray-700 select-none border-b border-r border-gray-200 dark:border-gray-700"
                  >
                    <div className="flex items-center gap-1">
                      <span className="font-medium text-gray-700 dark:text-gray-300">{header}</span>
                      {sortConfig?.column === index && (
                        <span className="text-xs text-gray-500">
                          {sortConfig.direction === 'asc' ? '↑' : '↓'}
                        </span>
                      )}
                    </div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filteredRows.map((row, rowIndex) => (
                <tr
                  key={rowIndex}
                  className="hover:bg-gray-50 dark:hover:bg-gray-800 border-b border-gray-200 dark:border-gray-700"
                >
                  {row.map((cell, cellIndex) => (
                    <td
                      key={cellIndex}
                      className="px-4 py-2 border-r border-gray-200 dark:border-gray-700 relative group"
                      onClick={() => editable && setEditingCell({ row: rowIndex, col: cellIndex })}
                    >
                      {editingCell?.row === rowIndex && editingCell?.col === cellIndex ? (
                        <input
                          type="text"
                          defaultValue={cell}
                          autoFocus
                          onBlur={(e) => handleCellEdit(rowIndex, cellIndex, e.target.value)}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter') {
                              handleCellEdit(rowIndex, cellIndex, (e.target as HTMLInputElement).value)
                            } else if (e.key === 'Escape') {
                              setEditingCell(null)
                            }
                          }}
                          className="w-full px-2 py-1 text-xs border border-blue-500 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none"
                        />
                      ) : (
                        <div className="flex items-center justify-between gap-2">
                          <span className="text-gray-700 dark:text-gray-300 truncate">
                            {cell || '-'}
                          </span>
                          <button
                            onClick={(e) => {
                              e.stopPropagation()
                              handleCopyCell(cell)
                            }}
                            className="opacity-0 group-hover:opacity-100 p-0.5 hover:bg-gray-200 dark:hover:bg-gray-600 rounded transition-all"
                            title="Copy cell"
                          >
                            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                            </svg>
                          </button>
                        </div>
                      )}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <pre className="p-4 text-xs font-mono text-gray-800 dark:text-gray-200 whitespace-pre-wrap">
            {data}
          </pre>
        )}
      </div>

      {/* Stats Footer */}
      <div className="px-4 py-2 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 text-xs text-gray-600 dark:text-gray-400">
        <div className="flex items-center justify-between">
          <span>
            {totalRows} rows × {headers.length} columns
          </span>
          {searchQuery && (
            <span>
              Showing {filteredRows.length} of {totalRows} rows
            </span>
          )}
        </div>
      </div>
    </div>
  )
}
