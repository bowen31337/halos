import { useState, useEffect } from 'react'
import { useProjectStore, Project } from '../stores/projectStore'
import { detectFileType, getFileDescription } from '../utils/fileTypeDetection'

interface ProjectFilesProps {
  project: Project
}

export function ProjectFiles({ project }: ProjectFilesProps) {
  const [files, setFiles] = useState<any[]>([])
  const [isUploading, setIsUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [error, setError] = useState<string | null>(null)
  const [showFiles, setShowFiles] = useState(false)

  useEffect(() => {
    if (project && showFiles) {
      fetchFiles()
    }
  }, [project, showFiles])

  const fetchFiles = async () => {
    try {
      const response = await fetch(`/api/projects/${project.id}/files`)
      if (!response.ok) throw new Error('Failed to fetch files')
      const data = await response.json()
      setFiles(data)
    } catch (error) {
      console.error('Failed to fetch files:', error)
      setError('Failed to load files')
    }
  }

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    setIsUploading(true)
    setUploadProgress(0)
    setError(null)

    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await fetch(`/api/projects/${project.id}/files`, {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        const errorText = await response.text()
        throw new Error(`Upload failed: ${errorText}`)
      }

      await fetchFiles() // Refresh file list
    } catch (error) {
      console.error('Upload failed:', error)
      setError('Upload failed. Please try again.')
    } finally {
      setIsUploading(false)
      setUploadProgress(100)
      // Reset file input
      event.target.value = ''
    }
  }

  const handleDownload = async (file: any) => {
    try {
      const response = await fetch(file.file_url)
      if (!response.ok) throw new Error('Download failed')

      const blob = await response.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = file.original_filename
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    } catch (error) {
      console.error('Download failed:', error)
      setError('Download failed. Please try again.')
    }
  }

  const handleDelete = async (fileId: string) => {
    if (!confirm('Delete this file?')) return

    try {
      const response = await fetch(`/api/projects/${project.id}/files/${fileId}`, {
        method: 'DELETE',
      })

      if (!response.ok) throw new Error('Delete failed')

      await fetchFiles() // Refresh file list
    } catch (error) {
      console.error('Delete failed:', error)
      setError('Delete failed. Please try again.')
    }
  }

  if (!showFiles) {
    return (
      <button
        onClick={() => setShowFiles(true)}
        className="w-full px-4 py-2 bg-[var(--primary)] hover:bg-[var(--primary-hover)] text-white rounded-lg font-medium transition-colors"
      >
        View Project Files
      </button>
    )
  }

  return (
    <div className="border border-[var(--border)] rounded-lg p-4 bg-[var(--bg-secondary)]">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-[var(--text-primary)]">Project Files</h3>
        <button
          onClick={() => setShowFiles(false)}
          className="p-2 hover:bg-[var(--bg-primary)] rounded-lg transition-colors"
        >
          <svg className="w-5 h-5 text-[var(--text-secondary)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <div className="space-y-4">
        {/* Upload Section */}
        <div className="border border-[var(--border)] rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-[var(--text-primary)]">Upload Files</span>
            <span className="text-xs text-[var(--text-secondary)]">
              PDF files will have text extracted automatically
            </span>
          </div>

          <div className="flex items-center gap-2">
            <input
              type="file"
              accept=".pdf,.txt,.md,.doc,.docx,.csv"
              onChange={handleFileUpload}
              disabled={isUploading}
              className="flex-1 px-3 py-2 bg-[var(--bg-primary)] border border-[var(--border)] rounded-lg text-sm text-[var(--text-primary)] file:mr-4 file:px-4 file:py-2 file:bg-[var(--primary)] file:text-white file:border-0 file:rounded-lg file:hover:opacity-90 disabled:opacity-50"
            />
            {isUploading && (
              <div className="flex items-center gap-2 text-sm text-[var(--text-secondary)]">
                <div className="w-16 bg-[var(--border)] rounded-full h-2 overflow-hidden">
                  <div
                    className="bg-[var(--primary)] h-2 rounded-full transition-all"
                    style={{ width: `${uploadProgress}%` }}
                  />
                </div>
                <span className="flex items-center gap-2">
                  <span className="loading-spinner primary small"></span>
                  Uploading...
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="p-3 bg-red-500/10 border border-red-500/50 rounded-lg">
            <span className="text-red-400 text-sm">{error}</span>
          </div>
        )}

        {/* Files List */}
        <div className="space-y-2">
          <h4 className="text-sm font-medium text-[var(--text-primary)]">Files ({files.length})</h4>

          {files.length === 0 ? (
            <div className="p-4 text-center text-[var(--text-secondary)]">
              No files uploaded yet. Upload a file to add it to the project knowledge base.
            </div>
          ) : (
            files.map((file) => {
              const fileType = detectFileType(file.original_filename)
              const fileDescription = getFileDescription(file.original_filename)

              return (
              <div
                key={file.id}
                className="flex items-center justify-between p-3 bg-[var(--bg-primary)] border border-[var(--border)] rounded-lg"
              >
                <div className="flex items-center gap-3 flex-1 min-w-0">
                  <div className="flex items-center justify-center w-10 h-10 bg-[var(--surface-elevated)] rounded-lg text-xl" title={fileDescription}>
                    {fileType.icon}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="font-medium text-[var(--text-primary)] truncate">
                      {file.original_filename}
                    </div>
                    <div className="text-xs text-[var(--text-secondary)] flex gap-2">
                      <span>{fileDescription}</span>
                      <span>•</span>
                      <span>{(file.file_size / 1024).toFixed(1)} KB</span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handleDownload(file)}
                    className="px-3 py-1 text-sm bg-[var(--primary)] hover:bg-[var(--primary-hover)] text-white rounded-lg transition-colors"
                  >
                    Download
                  </button>
                  <button
                    onClick={() => handleDelete(file.id)}
                    className="p-2 hover:bg-red-500/10 rounded-lg transition-colors"
                    title="Delete file"
                  >
                    <svg className="w-4 h-4 text-[var(--text-secondary)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  )
}