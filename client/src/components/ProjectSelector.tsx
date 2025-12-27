import { useState, useEffect } from 'react'
import { useProjectStore, type Project } from '../stores/projectStore'
import { ProjectFilesModal } from './ProjectFilesModal'

interface ProjectSelectorProps {
  selectedProjectId: string | null
  onProjectChange: (projectId: string | null) => void
}

export function ProjectSelector({ selectedProjectId, onProjectChange }: ProjectSelectorProps) {
  const { projects, fetchProjects, createProject } = useProjectStore()
  const [isOpen, setIsOpen] = useState(false)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showFilesModal, setShowFilesModal] = useState(false)

  useEffect(() => {
    fetchProjects()
  }, [fetchProjects])

  const selectedProject = projects.find(p => p.id === selectedProjectId)

  const handleSelectProject = (projectId: string | null) => {
    onProjectChange(projectId)
    setIsOpen(false)
  }

  const handleCreateProject = async (name: string) => {
    try {
      const newProject = await createProject({ name })
      handleSelectProject(newProject.id)
      setShowCreateModal(false)
    } catch (error) {
      console.error('Failed to create project:', error)
      alert('Failed to create project')
    }
  }

  const handleManageFiles = () => {
    if (selectedProject) {
      setShowFilesModal(true)
      setIsOpen(false)
    }
  }

  return (
    <div className="relative">
      {/* Project Selector Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-3 py-2 bg-[var(--bg-primary)] border border-[var(--border)] rounded-lg text-sm text-left flex items-center justify-between hover:border-[var(--primary)] transition-colors"
      >
        <div className="flex items-center gap-2 flex-1 min-w-0">
          {selectedProject ? (
            <>
              <span className="text-lg">{selectedProject.icon || '📁'}</span>
              <span className="truncate font-medium">{selectedProject.name}</span>
            </>
          ) : (
            <span className="text-[var(--text-secondary)]">All Conversations</span>
          )}
        </div>
        <svg
          className={`w-4 h-4 text-[var(--text-secondary)] transition-transform ${isOpen ? 'rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {/* Dropdown */}
      {isOpen && (
        <>
          <div
            className="fixed inset-0 z-10"
            onClick={() => setIsOpen(false)}
          />
          <div className="absolute z-20 w-full mt-2 bg-[var(--bg-primary)] border border-[var(--border)] rounded-lg shadow-lg max-h-64 overflow-y-auto">
            {/* All Conversations option */}
            <button
              onClick={() => handleSelectProject(null)}
              className={`w-full px-3 py-2 text-sm text-left hover:bg-[var(--bg-secondary)] transition-colors flex items-center gap-2 ${
                !selectedProjectId ? 'bg-[var(--bg-secondary)]' : ''
              }`}
            >
              <span>📋</span>
              <span>All Conversations</span>
            </button>

            {/* Divider */}
            <div className="border-t border-[var(--border)] my-1" />

            {/* Projects list */}
            {projects.length === 0 ? (
              <div className="px-3 py-4 text-sm text-[var(--text-secondary)] text-center">
                No projects yet
              </div>
            ) : (
              projects.map((project) => (
                <button
                  key={project.id}
                  onClick={() => handleSelectProject(project.id)}
                  className={`w-full px-3 py-2 text-sm text-left hover:bg-[var(--bg-secondary)] transition-colors flex items-center gap-2 ${
                    selectedProjectId === project.id ? 'bg-[var(--bg-secondary)]' : ''
                  }`}
                >
                  <span className="text-lg" style={{ color: project.color }}>
                    {project.icon || '📁'}
                  </span>
                  <span className="truncate flex-1">{project.name}</span>
                  <span
                    className="w-2 h-2 rounded-full flex-shrink-0"
                    style={{ backgroundColor: project.color }}
                  />
                </button>
              ))
            )}

            {/* Divider */}
            <div className="border-t border-[var(--border)] my-1" />

            {/* Manage Files Button - only show if a project is selected */}
            {selectedProject && (
              <>
                <button
                  onClick={handleManageFiles}
                  className="w-full px-3 py-2 text-sm text-left hover:bg-[var(--bg-secondary)] transition-colors flex items-center gap-2 text-[var(--primary)]"
                >
                  <span>📎</span>
                  <span>Manage Project Files</span>
                </button>
                <div className="border-t border-[var(--border)] my-1" />
              </>
            )}

            {/* Create Project Button */}
            <button
              onClick={() => {
                setShowCreateModal(true)
                setIsOpen(false)
              }}
              className="w-full px-3 py-2 text-sm text-left hover:bg-[var(--bg-secondary)] transition-colors flex items-center gap-2 text-[var(--primary)]"
            >
              <span>+</span>
              <span>Create New Project</span>
            </button>
          </div>
        </>
      )}

      {/* Create Project Modal */}
      {showCreateModal && (
        <CreateProjectModal
          onClose={() => setShowCreateModal(false)}
          onCreate={handleCreateProject}
        />
      )}

      {/* Project Files Modal */}
      {showFilesModal && selectedProject && (
        <ProjectFilesModal
          isOpen={showFilesModal}
          onClose={() => setShowFilesModal(false)}
          projectId={selectedProject.id}
          projectName={selectedProject.name}
        />
      )}
    </div>
  )
}

interface CreateProjectModalProps {
  onClose: () => void
  onCreate: (name: string) => void
}

function CreateProjectModal({ onClose, onCreate }: CreateProjectModalProps) {
  const [name, setName] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!name.trim()) return

    setIsSubmitting(true)
    try {
      await onCreate(name.trim())
      setName('')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-[var(--bg-primary)] rounded-xl shadow-2xl w-full max-w-md mx-4 p-6">
        <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-4">
          Create New Project
        </h3>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-[var(--text-primary)] mb-2">
              Project Name
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="My Project"
              className="w-full px-4 py-2 bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg text-[var(--text-primary)] placeholder-[var(--text-secondary)] focus:outline-none focus:ring-2 focus:ring-[var(--primary)]"
              autoFocus
            />
          </div>

          <div className="flex gap-3 justify-end">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-[var(--text-primary)] hover:bg-[var(--bg-secondary)] rounded-lg transition-colors"
              disabled={isSubmitting}
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={!name.trim() || isSubmitting}
              className="px-4 py-2 text-sm font-medium text-white bg-[var(--primary)] hover:opacity-90 disabled:opacity-50 rounded-lg transition-colors"
            >
              {isSubmitting ? 'Creating...' : 'Create'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
