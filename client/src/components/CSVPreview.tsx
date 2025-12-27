import { useState, useMemo } from 'react'

interface CSVPreviewProps {
  data: string
  delimiter?: string
  maxRows?: number
}

interface ParsedCSV {
  headers: string[]
  rows: string[][]
  rowCount: number
}

export function CSVPreview({ data, delimiter = ',', maxRows = 100 }: CSVPreviewProps) {
  const [showAll, setShowAll] = useState(false)

  // Parse CSV data
  const parsed = useMemo<ParsedCSV | null>(() => {
    if (!data) return null

    try {
      // Split into lines
      const lines = data.trim().split('\n').filter(line => line.trim().length > 0)
      if (lines.length === 0) return null

      // Parse a single CSV line
      const parseLine = (line: string): string[] => {
        const result: string[] = []
        let current = ''
        let inQuotes = false
        let i = 0

        while (i < line.length) {
          const char = line[i]

          if (char === '"') {
            if (inQuotes && line[i + 1] === '"') {
              // Escaped quote
              current += '"'
              i += 2
            } else {
              inQuotes = !inQuotes
              i++
            }
          } else if (char === delimiter && !inQuotes) {
            result.push(current)
            current = ''
            i++
          } else {
            current += char
            i++
          }
        }
        result.push(current)
        return result
      }

      // First line is headers
      const headers = parseLine(lines[0])
      // Remaining lines are data
      const rows = lines.slice(1).map(parseLine)

      return {
        headers,
        rows,
        rowCount: rows.length,
      }
    } catch (error) {
      console.error('Failed to parse CSV:', error)
      return null
    }
  }, [data, delimiter])

  if (!parsed) {
    return (
      <div className=\"p-4 text-red-500 text-sm\">
        Invalid or empty CSV data
      </div>
    )
  }

  const { headers, rows, rowCount } = parsed
  const displayRows = showAll ? rows : rows.slice(0, maxRows)
  const hasMore = rows.length > maxRows

  return (
    <div className=\"h-full flex flex-col bg-[var(--bg-primary)] border border-[var(--border)] rounded-lg overflow-hidden\">
      {/* Toolbar */}
      <div className=\"flex items-center justify-between px-4 py-2 border-b border-[var(--border)] bg-[var(--surface-secondary)]\">
        <div className=\"flex items-center gap-2 text-sm\">
          <span className=\"font-medium text-[var(--text-primary)]\">CSV Preview</span>
          <span className=\"text-xs text-[var(--text-secondary)] px-2 py-0.5 bg-[var(--bg-primary)] rounded\">
            {rowCount} rows × {headers.length} columns
          </span>
        </div>
        {hasMore && (
          <button
            onClick={() => setShowAll(!showAll)}
            className=\"text-xs px-2 py-1 rounded bg-[var(--primary)] text-white hover:opacity-90 transition-opacity\"
          >
            {showAll ? 'Show Less' : `Show All (${rowCount})`}
          </button>
        )}
      </div>

      {/* Table */}
      <div className=\"flex-1 overflow-auto\">
        <table className=\"w-full text-xs border-collapse\">
          <thead className=\"sticky top-0 bg-[var(--surface-elevated)] shadow-sm z-10\">
            <tr>
              {headers.map((header, idx) => (
                <th
                  key={idx}
                  className=\"px-3 py-2 text-left font-semibold text-[var(--text-primary)] border-b border-[var(--border)] whitespace-nowrap sticky top-0 bg-[var(--surface-elevated)]\"
                >
                  {header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {displayRows.map((row, rowIdx) => (
              <tr
                key={rowIdx}
                className=\"hover:bg-[var(--surface-secondary)] transition-colors\"
              >
                {row.map((cell, cellIdx) => (
                  <td
                    key={cellIdx}
                    className=\"px-3 py-2 text-[var(--text-secondary)] border-b border-[var(--border)]/50 whitespace-nowrap max-w-xs overflow-hidden text-ellipsis\"
                  >
                    {cell || <span className=\"text-[var(--text-secondary)] opacity-50\">—</span>}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>

        {hasMore && !showAll && (
          <div className=\"p-4 text-center text-xs text-[var(--text-secondary)] bg-[var(--surface-secondary)]/50\">
            Showing first {maxRows} of {rowCount} rows
          </div>
        )}
      </div>

      {/* Footer */}
      <div className=\"px-4 py-2 border-t border-[var(--border)] bg-[var(--surface-secondary)] text-xs text-[var(--text-secondary)] flex justify-between\">
        <span>Delimiter: <code className=\"bg-[var(--bg-primary)] px-1 rounded\">{delimiter}</code></span>
        <span>Total: {rowCount} rows</span>
      </div>
    </div>
  )
}
