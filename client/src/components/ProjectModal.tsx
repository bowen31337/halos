import { useState, useEffect } from 'react'
import { useProjectStore, Project } from '../stores/projectStore'
import { ProjectFiles } from './ProjectFiles'

interface ProjectModalProps {
  isOpen: boolean
  onClose: () => void
  project?: Project
}

const COLOR_OPTIONS = [
  { name: 'Orange', value: '#CC785C' },
  { name: 'Blue', value: '#3B82F6' },
  { name: 'Green', value: '#10B981' },
  { name: 'Purple', value: '#8B5CF6' },
  { name: 'Red', value: '#EF4444' },
  { name: 'Yellow', value: '#F59E0B' },
  { name: 'Pink', value: '#EC4899' },
  { name: 'Cyan', value: '#06B6D4' },
]

const ICON_OPTIONS = [
  { name: 'Folder', icon: '📁' },
  { name: 'Star', icon: '⭐' },
  { name: 'Rocket', icon: '🚀' },
  { name: 'Book', icon: '📚' },
  { name: 'Code', icon: '💻' },
  { name: 'Lightbulb', icon: '💡' },
  { name: 'Fire', icon: '🔥' },
  { name: 'Heart', icon: '❤️' },
]

export function ProjectModal({ isOpen, onClose, project }: ProjectModalProps) {
  const { createProject, updateProject } = useProjectStore()

  const [name, setName] = useState(project?.name || '')
  const [description, setDescription] = useState(project?.description || '')
  const [color, setColor] = useState(project?.color || '#CC785C')
  const [icon, setIcon] = useState(project?.icon || '📁')
  const [customInstructions, setCustomInstructions] = useState(project?.custom_instructions || '')
  const [isSubmitting, setIsSubmitting] = useState(false)

  // Handle Escape key to close modal
  useEffect(() => {
    if (!isOpen) return

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose()
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [isOpen, onClose])

  // Reset form when project prop changes or modal opens/closes
  useEffect(() => {
    if (isOpen) {
      setName(project?.name || '')
      setDescription(project?.description || '')
      setColor(project?.color || '#CC785C')
      setIcon(project?.icon || '📁')
      setCustomInstructions(project?.custom_instructions || '')
    }
  }, [isOpen, project])

  if (!isOpen) return null

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!name.trim()) {
      alert('Project name is required')
      return
    }

    setIsSubmitting(true)
    try {
      if (project) {
        // Update existing project
        await updateProject(project.id, {
          name: name.trim(),
          description: description.trim() || undefined,
          color,
          icon,
          custom_instructions: customInstructions.trim() || undefined,
        })
      } else {
        // Create new project
        await createProject({
          name: name.trim(),
          description: description.trim() || undefined,
          color,
          icon,
          custom_instructions: customInstructions.trim() || undefined,
        })
      }
      onClose()
    } catch (error) {
      console.error('Failed to save project:', error)
      alert('Failed to save project. Please try again.')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-[var(--bg-primary)] rounded-xl shadow-2xl w-full max-w-lg mx-4 overflow-hidden">
        {/* Header */}
        <div className="px-6 py-4 border-b border-[var(--border-primary)] flex items-center justify-between">
          <h2 className="text-xl font-semibold text-[var(--text-primary)]">
            {project ? 'Edit Project' : 'Create New Project'}
          </h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-[var(--surface-elevated)] rounded-lg transition-colors"
            disabled={isSubmitting}
          >
            <svg className="w-5 h-5 text-[var(--text-secondary)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-6 max-h-[70vh] overflow-y-auto">
          {/* Project Name */}
          <div>
            <label className="block text-sm font-medium text-[var(--text-primary)] mb-2">
              Project Name <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="My Project"
              className="w-full px-4 py-2 bg-[var(--surface-elevated)] border border-[var(--border-primary)] rounded-lg text-[var(--text-primary)] placeholder-[var(--text-secondary)] focus:outline-none focus:ring-2 focus:ring-[var(--primary)] focus:border-transparent"
              disabled={isSubmitting}
              autoFocus
            />
          </div>

          {/* Description */}
          <div>
            <label className="block text-sm font-medium text-[var(--text-primary)] mb-2">
              Description
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="What is this project about?"
              rows={3}
              className="w-full px-4 py-2 bg-[var(--surface-elevated)] border border-[var(--border-primary)] rounded-lg text-[var(--text-primary)] placeholder-[var(--text-secondary)] focus:outline-none focus:ring-2 focus:ring-[var(--primary)] focus:border-transparent resize-none"
              disabled={isSubmitting}
            />
          </div>

          {/* Color Selection */}
          <div>
            <label className="block text-sm font-medium text-[var(--text-primary)] mb-2">
              Color
            </label>
            <div className="flex flex-wrap gap-2">
              {COLOR_OPTIONS.map((colorOption) => (
                <button
                  key={colorOption.value}
                  type="button"
                  onClick={() => setColor(colorOption.value)}
                  className={`w-8 h-8 rounded-full border-2 transition-all ${
                    color === colorOption.value
                      ? 'border-[var(--text-primary)] scale-110'
                      : 'border-transparent hover:scale-105'
                  }`}
                  style={{ backgroundColor: colorOption.value }}
                  title={colorOption.name}
                  disabled={isSubmitting}
                />
              ))}
            </div>
          </div>

          {/* Icon Selection */}
          <div>
            <label className="block text-sm font-medium text-[var(--text-primary)] mb-2">
              Icon
            </label>
            <div className="flex flex-wrap gap-2">
              {ICON_OPTIONS.map((iconOption) => (
                <button
                  key={iconOption.name}
                  type="button"
                  onClick={() => setIcon(iconOption.icon)}
                  className={`w-10 h-10 rounded-lg border-2 flex items-center justify-center text-xl transition-all ${
                    icon === iconOption.icon
                      ? 'border-[var(--primary)] bg-[var(--surface-elevated)]'
                      : 'border-[var(--border-primary)] hover:border-[var(--text-secondary)]'
                  }`}
                  title={iconOption.name}
                  disabled={isSubmitting}
                >
                  {iconOption.icon}
                </button>
              ))}
            </div>
          </div>

          {/* Custom Instructions */}
          <div>
            <label className="block text-sm font-medium text-[var(--text-primary)] mb-2">
              Custom Instructions (Optional)
            </label>
            <textarea
              value={customInstructions}
              onChange={(e) => setCustomInstructions(e.target.value)}
              placeholder="Custom instructions for this project..."
              rows={4}
              className="w-full px-4 py-2 bg-[var(--surface-elevated)] border border-[var(--border-primary)] rounded-lg text-[var(--text-primary)] placeholder-[var(--text-secondary)] focus:outline-none focus:ring-2 focus:ring-[var(--primary)] focus:border-transparent resize-none text-sm"
              disabled={isSubmitting}
            />
            <p className="mt-1 text-xs text-[var(--text-secondary)]">
              These instructions will be applied to all conversations in this project.
            </p>
          </div>

          {/* Project Files Section */}
          {project && (
            <div>
              <label className="block text-sm font-medium text-[var(--text-primary)] mb-2">
                Project Files (Knowledge Base)
              </label>
              <ProjectFiles project={project} />
            </div>
          )}
        </form>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-[var(--border-primary)] flex items-center justify-end gap-3">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-[var(--text-primary)] hover:bg-[var(--surface-elevated)] rounded-lg transition-colors"
            disabled={isSubmitting}
          >
            Cancel
          </button>
          <button
            type="submit"
            onClick={handleSubmit}
            disabled={isSubmitting || !name.trim()}
            className="px-4 py-2 text-sm font-medium text-white bg-[var(--primary)] hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg transition-colors"
          >
            {isSubmitting ? 'Saving...' : project ? 'Save Changes' : 'Create Project'}
          </button>
        </div>
      </div>
    </div>
  )
}
