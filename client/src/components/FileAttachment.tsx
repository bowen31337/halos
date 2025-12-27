import { X } from 'lucide-react'
import { detectFileType, getFileDescription } from '../utils/fileTypeDetection'

interface FileAttachmentProps {
  file: File
  preview?: string
  onRemove: () => void
}

export function FileAttachment({ file, preview, onRemove }: FileAttachmentProps) {
  const fileType = detectFileType(file)
  const description = getFileDescription(file)

  return (
    <div className="file-attachment group relative flex items-center gap-2 bg-gray-100 dark:bg-gray-800 rounded-lg p-2 pr-8 border border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600 transition-colors">
      {/* File icon */}
      <div className="file-icon flex-shrink-0 text-2xl" title={description}>
        {fileType.icon}
      </div>

      {/* File info */}
      <div className="file-info flex-1 min-w-0">
        <div className="file-name text-sm font-medium text-gray-900 dark:text-gray-100 truncate" title={file.name}>
          {file.name}
        </div>
        <div className="file-meta text-xs text-gray-500 dark:text-gray-400 flex items-center gap-2">
          <span>{description}</span>
          <span>•</span>
          <span>{formatFileSize(file.size)}</span>
        </div>
      </div>

      {/* Preview for images */}
      {fileType.type === 'image' && preview && (
        <div className="image-preview flex-shrink-0 w-12 h-12 rounded overflow-hidden border border-gray-200 dark:border-gray-700">
          <img src={preview} alt={file.name} className="w-full h-full object-cover" />
        </div>
      )}

      {/* Language badge for code files */}
      {fileType.type === 'code' && fileType.language && (
        <div className="language-badge flex-shrink-0 px-2 py-1 bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 text-xs font-medium rounded">
          {fileType.language}
        </div>
      )}

      {/* Remove button */}
      <button
        onClick={onRemove}
        className="remove-btn absolute right-1 top-1/2 -translate-y-1/2 p-1 rounded-md hover:bg-gray-200 dark:hover:bg-gray-700 text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 opacity-0 group-hover:opacity-100 transition-all"
        title="Remove attachment"
      >
        <X size={16} />
      </button>
    </div>
  )
}

/**
 * Format file size to human readable string.
 */
function formatFileSize(bytes: number): string {
  if (bytes < 1024) {
    return bytes + ' B'
  }

  const kb = bytes / 1024
  if (kb < 1024) {
    return kb.toFixed(1) + ' KB'
  }

  const mb = kb / 1024
  if (mb < 1024) {
    return mb.toFixed(1) + ' MB'
  }

  const gb = mb / 1024
  return gb.toFixed(1) + ' GB'
}
