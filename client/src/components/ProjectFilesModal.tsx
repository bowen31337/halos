import { useState, useEffect } from 'react'
import { api } from '../services/api'

interface ProjectFilesModalProps {
  isOpen: boolean
  onClose: () => void
  projectId: string
  projectName: string
}

interface ProjectFile {
  id: string
  filename: string
  original_filename: string
  file_url: string
  file_size: number
  content_type: string
  created_at: string
}

export function ProjectFilesModal({ isOpen, onClose, projectId, projectName }: ProjectFilesModalProps) {
  const [files, setFiles] = useState<ProjectFile[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (isOpen && projectId) {
      loadFiles()
    }
  }, [isOpen, projectId])

  const loadFiles = async () => {
    setIsLoading(true)
    setError(null)
    try {
      const fileList = await api.listProjectFiles(projectId)
      setFiles(fileList)
    } catch (err) {
      setError('Failed to load files')
      console.error(err)
    } finally {
      setIsLoading(false)
    }
  }

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    setIsUploading(true)
    setError(null)
    setUploadProgress(0)

    try {
      // Simulate progress
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => {
          if (prev >= 90) {
            clearInterval(progressInterval)
            return 90
          }
          return prev + 10
        })
      }, 200)

      await api.uploadProjectFile(projectId, file)

      clearInterval(progressInterval)
      setUploadProgress(100)

      // Reload files
      await loadFiles()

      // Reset form
      event.target.value = ''

      // Reset progress after a delay
      setTimeout(() => setUploadProgress(0), 1000)
    } catch (err) {
      setError(`Upload failed: ${err instanceof Error ? err.message : 'Unknown error'}`)
    } finally {
      setIsUploading(false)
    }
  }

  const handleDeleteFile = async (fileId: string) => {
    if (!confirm('Delete this file?')) return

    try {
      await api.deleteProjectFile(projectId, fileId)
      await loadFiles()
    } catch (err) {
      setError('Failed to delete file')
      console.error(err)
    }
  }

  const handleDownloadFile = async (file: ProjectFile) => {
    try {
      const blob = await api.downloadProjectFile(projectId, file.filename)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = file.original_filename
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    } catch (err) {
      setError('Failed to download file')
      console.error(err)
    }
  }

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString()
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="bg-[var(--bg-primary)] rounded-xl shadow-2xl w-full max-w-2xl mx-4 overflow-hidden max-h-[80vh] flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b border-[var(--border)] flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold text-[var(--text-primary)]">
              Project Files
            </h2>
            <p className="text-sm text-[var(--text-secondary)] mt-1">
              {projectName}
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-[var(--surface-elevated)] rounded-lg transition-colors"
            title="Close"
          >
            <svg className="w-5 h-5 text-[var(--text-secondary)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {/* Upload Section */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-[var(--text-primary)] mb-2">
              Upload File
            </label>
            <div className="flex items-center gap-3">
              <label className="flex-1 cursor-pointer">
                <input
                  type="file"
                  onChange={handleFileUpload}
                  disabled={isUploading}
                  className="hidden"
                  id="file-upload"
                />
                <div className={`px-4 py-3 rounded-lg border-2 border-dashed text-center transition-all ${
                  isUploading
                    ? 'border-[var(--primary)] bg-[var(--surface-elevated)] opacity-50'
                    : 'border-[var(--border)] hover:border-[var(--primary)] hover:bg-[var(--surface-elevated)]'
                }`}>
                  <div className="text-sm">
                    {isUploading ? (
                      <div className="flex flex-col items-center gap-2">
                        <span>Uploading...</span>
                        <div className="w-full max-w-xs bg-[var(--border)] rounded-full h-2 overflow-hidden">
                          <div
                            className="bg-[var(--primary)] h-full transition-all"
                            style={{ width: `${uploadProgress}%` }}
                          />
                        </div>
                      </div>
                    ) : (
                      <span>Click to select a file or drag and drop</span>
                    )}
                  </div>
                </div>
              </label>
            </div>
            <p className="mt-1 text-xs text-[var(--text-secondary)]">
              Supports PDF, text, and other document formats. Files are added to the project knowledge base.
            </p>
          </div>

          {/* Error Message */}
          {error && (
            <div className="mb-4 p-3 bg-red-500/10 border border-red-500/30 text-red-500 rounded-lg text-sm">
              {error}
            </div>
          )}

          {/* Files List */}
          <div>
            <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-3">
              Project Files ({files.length})
            </h3>

            {isLoading ? (
              <div className="text-center py-8 text-[var(--text-secondary)]">
                Loading files...
              </div>
            ) : files.length === 0 ? (
              <div className="text-center py-8 text-[var(--text-secondary)] text-sm">
                No files uploaded yet
              </div>
            ) : (
              <div className="space-y-2">
                {files.map((file) => (
                  <div
                    key={file.id}
                    className="flex items-center justify-between p-3 bg-[var(--surface-elevated)] rounded-lg border border-[var(--border)] hover:border-[var(--primary)] transition-colors"
                  >
                    <div className="flex items-center gap-3 flex-1 min-w-0">
                      <div className="text-2xl">
                        {file.content_type?.includes('pdf') ? '📄' :
                         file.content_type?.includes('text') ? '📝' : '📎'}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="font-medium text-sm truncate text-[var(--text-primary)]">
                          {file.original_filename}
                        </div>
                        <div className="text-xs text-[var(--text-secondary)] flex gap-2">
                          <span>{formatFileSize(file.file_size)}</span>
                          <span>•</span>
                          <span>{formatDate(file.created_at)}</span>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 ml-2">
                      <button
                        onClick={() => handleDownloadFile(file)}
                        className="p-2 hover:bg-[var(--bg-primary)] rounded transition-colors"
                        title="Download"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                        </svg>
                      </button>
                      <button
                        onClick={() => handleDeleteFile(file.id)}
                        className="p-2 hover:bg-red-500/20 hover:text-red-500 rounded transition-colors"
                        title="Delete"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                        </svg>
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-[var(--border)] flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-[var(--text-primary)] hover:bg-[var(--surface-elevated)] rounded-lg transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  )
}
