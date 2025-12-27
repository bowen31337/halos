import { useState, useEffect, useRef } from 'react'
import { useParams } from 'react-router-dom'
import { useUIStore } from '../stores/uiStore'
import { useProjectStore } from '../stores/projectStore'
import { useConversationStore } from '../stores/conversationStore'
import { SettingsModal } from './SettingsModal'
import { ProjectModal } from './ProjectModal'
import { ProjectFilesModal } from './ProjectFilesModal'
import { BranchSelector } from './BranchSelector'
import { CheckpointManager } from './CheckpointManager'
import { SubAgentModal } from './SubAgentModal'
import { MemoryManager } from './MemoryManager'
import { ShareModal } from './ShareModal'
import { PromptModal } from './PromptModal'
import { MCPModal } from './MCPModal'
import { exportToPDF } from '../utils/exportPdf'
import { NetworkStatusBadge } from './NetworkStatusIndicator'
import { useNetworkStore } from '../stores/networkStore'
import { ComparisonModal } from './ComparisonModal'
import { Tooltip, IconButtonWithTooltip } from './Tooltip'
import { useToast } from './ToastManager'

const MODELS = [
  {
    id: 'claude-sonnet-4-5-20250929',
    name: 'Claude Sonnet 4.5',
    description: 'Balanced',
    capabilities: ['Reasoning', 'Code generation', 'Analysis', 'Multi-step tasks'],
    strengths: 'Best balance of intelligence and speed for most tasks',
    limits: '200K context window, moderate cost'
  },
  {
    id: 'claude-haiku-4-5-20251001',
    name: 'Claude Haiku 4.5',
    description: 'Fast',
    capabilities: ['Quick responses', 'Simple tasks', 'High volume', 'Cost-effective'],
    strengths: 'Fastest model, lowest cost, great for simple queries',
    limits: 'Less reasoning capability, 200K context window'
  },
  {
    id: 'claude-opus-4-1-20250805',
    name: 'Claude Opus 4.1',
    description: 'Most capable',
    capabilities: ['Advanced reasoning', 'Complex analysis', 'Creative writing', 'Deep understanding'],
    strengths: 'Highest intelligence, handles complex problems, nuanced understanding',
    limits: '200K context window, highest cost, slower responses'
  },
]

export function Header() {
  const {
    toggleSidebar, sidebarOpen, selectedModel, setSelectedModel,
    extendedThinkingEnabled, toggleExtendedThinking,
    comparisonMode, toggleComparisonMode, comparisonModels, setComparisonModels
  } = useUIStore()
  const { isOffline } = useNetworkStore()
  const { conversationId } = useParams()
  const {
    projects,
    selectedProjectId,
    setSelectedProject,
    fetchProjects,
    isLoading: projectsLoading
  } = useProjectStore()
  const { currentConversationId, conversations } = useConversationStore()

  const [modelDropdownOpen, setModelDropdownOpen] = useState(false)
  const [comparisonModalOpen, setComparisonModalOpen] = useState(false)
  const [exportMenuOpen, setExportMenuOpen] = useState(false)
  const [settingsOpen, setSettingsOpen] = useState(false)
  const [projectMenuOpen, setProjectMenuOpen] = useState(false)
  const [projectModalOpen, setProjectModalOpen] = useState(false)
  const [projectFilesOpen, setProjectFilesOpen] = useState(false)
  const [editingProject, setEditingProject] = useState<{ id: string } | null>(null)
  const [isExporting, setIsExporting] = useState(false)
  const [checkpointManagerOpen, setCheckpointManagerOpen] = useState(false)
  const [subAgentModalOpen, setSubAgentModalOpen] = useState(false)
  const [memoryManagerOpen, setMemoryManagerOpen] = useState(false)
  const [shareModalOpen, setShareModalOpen] = useState(false)
  const [promptModalOpen, setPromptModalOpen] = useState(false)
  const [mcpModalOpen, setMcpModalOpen] = useState(false)
  const [tempComparisonModels, setTempComparisonModels] = useState<string[]>(comparisonModels)

  // Responsive state
  const [isMobile, setIsMobile] = useState(false)
  const [isTablet, setIsTablet] = useState(false)

  // Fetch projects on mount
  useEffect(() => {
    fetchProjects()
  }, [fetchProjects])

  // Handle responsive breakpoints
  useEffect(() => {
    const checkScreenSize = () => {
      const width = window.innerWidth
      setIsMobile(width < 768)
      setIsTablet(width >= 768 && width < 1024)
    }

    checkScreenSize()
    window.addEventListener('resize', checkScreenSize)
    return () => window.removeEventListener('resize', checkScreenSize)
  }, [])

  const handleExport = async (format: 'json' | 'markdown') => {
    if (!conversationId) return

    setIsExporting(true)
    try {
      const response = await fetch(`/api/conversations/${conversationId}/export?format=${format}`, {
        method: 'POST',
      })

      if (!response.ok) {
        throw new Error('Export failed')
      }

      // Get filename from Content-Disposition header
      const contentDisposition = response.headers.get('Content-Disposition')
      let filename = `conversation_export.${format === 'json' ? 'json' : 'md'}`
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="(.+)"/)
        if (filenameMatch) {
          filename = filenameMatch[1]
        }
      }

      // Download the file
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)

      setExportMenuOpen(false)
    } catch (error) {
      console.error('Export failed:', error)
      alert('Failed to export conversation')
    } finally {
      setIsExporting(false)
    }
  }

  const handlePDFExport = async () => {
    if (!conversationId) return

    setIsExporting(true)
    try {
      // Get conversation data
      const conversation = conversations.find(c => c.id === conversationId)
      if (!conversation) {
        throw new Error('Conversation not found')
      }

      // Prepare data for PDF export
      const pdfData = {
        title: conversation.title || 'Untitled Conversation',
        model: conversation.model || 'Claude',
        created_at: conversation.created_at || new Date().toISOString(),
        messages: conversation.messages || []
      }

      // Export to PDF
      await exportToPDF(pdfData)

      setExportMenuOpen(false)
    } catch (error) {
      console.error('PDF export failed:', error)
      alert('Failed to export PDF: ' + (error as Error).message)
    } finally {
      setIsExporting(false)
    }
  }

  const currentModel = MODELS.find(m => m.id === selectedModel) || MODELS[0]
  const selectedProject = projects.find(p => p.id === selectedProjectId)

  const handleCreateProject = () => {
    setEditingProject(null)
    setProjectModalOpen(true)
    setProjectMenuOpen(false)
  }

  const handleEditProject = (projectId: string) => {
    const project = projects.find(p => p.id === projectId)
    if (project) {
      setEditingProject({ id: projectId })
      setProjectModalOpen(true)
      setProjectMenuOpen(false)
    }
  }

  const handleManageFiles = (projectId: string) => {
    if (selectedProjectId === projectId) {
      setProjectFilesOpen(true)
      setProjectMenuOpen(false)
    } else {
      // First select the project, then open files
      setSelectedProject(projectId)
      setTimeout(() => {
        setProjectFilesOpen(true)
        setProjectMenuOpen(false)
      }, 100)
    }
  }

  return (
    <>
      <div className="h-14 border-b border-[var(--border-primary)] bg-[var(--surface-secondary)] flex items-center justify-between px-4" data-tour="header">
      {/* Left: Toggle sidebar and Project selector */}
      <div className="flex items-center gap-3" data-tour="sidebar">
        <Tooltip content="Toggle sidebar" shortcut="Ctrl+B">
          <button
            onClick={toggleSidebar}
            className="p-2 hover:bg-[var(--surface-elevated)] rounded-lg transition-colors"
            aria-label="Toggle conversation sidebar"
            aria-expanded={sidebarOpen}
            aria-controls="sidebar"
          >
            <svg className="w-5 h-5 text-[var(--text-primary)]" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>
        </Tooltip>

        {/* Project Selector */}
        <div className="relative">
          <button
            onClick={() => setProjectMenuOpen(!projectMenuOpen)}
            className="flex items-center gap-2 px-3 py-1.5 bg-[var(--surface-elevated)] hover:bg-[var(--bg-primary)] rounded-full text-sm transition-colors"
            title="Select project"
            aria-label="Select project"
            aria-expanded={projectMenuOpen}
            aria-haspopup="listbox"
            aria-controls="project-dropdown"
          >
            {selectedProject ? (
              <>
                <span className="text-lg" aria-hidden="true">{selectedProject.icon || '📁'}</span>
                <span className="text-[var(--text-primary)] font-medium">{selectedProject.name}</span>
              </>
            ) : (
              <span className="text-[var(--text-secondary)]">All Conversations</span>
            )}
            <svg className={`w-4 h-4 text-[var(--text-secondary)] transition-transform ${projectMenuOpen ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>

          {/* Project dropdown menu */}
          {projectMenuOpen && (
            <>
              <div
                className="fixed inset-0 z-10"
                onClick={() => setProjectMenuOpen(false)}
                aria-hidden="true"
              />
              <div className="absolute top-full left-0 mt-2 w-72 bg-[var(--bg-primary)] border border-[var(--border-primary)] rounded-lg shadow-lg z-20 py-2" role="listbox" id="project-dropdown" aria-label="Project selection">
                {/* All Conversations option */}
                <button
                  onClick={() => {
                    setSelectedProject(null)
                    setProjectMenuOpen(false)
                  }}
                  className={`w-full px-4 py-3 text-left hover:bg-[var(--surface-elevated)] transition-colors ${
                    !selectedProjectId ? 'bg-[var(--surface-elevated)]' : ''
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <span className="text-lg">💬</span>
                    <span className="text-sm font-medium text-[var(--text-primary)]">All Conversations</span>
                  </div>
                </button>

                <div className="border-t border-[var(--border-primary)] my-2" />

                {/* Projects list */}
                <div className="px-3 py-2 text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wider">
                  Projects
                </div>

                {projects.length === 0 ? (
                  <div className="px-4 py-3 text-sm text-[var(--text-secondary)]">
                    No projects yet
                  </div>
                ) : (
                  projects.map((project) => (
                    <div key={project.id} className="group">
                      <button
                        onClick={() => {
                          setSelectedProject(project.id)
                          setProjectMenuOpen(false)
                        }}
                        className={`w-full px-4 py-2 text-left hover:bg-[var(--surface-elevated)] transition-colors flex items-center justify-between ${
                          selectedProjectId === project.id ? 'bg-[var(--surface-elevated)]' : ''
                        }`}
                      >
                        <div className="flex items-center gap-2">
                          <span
                            className="w-3 h-3 rounded-full"
                            style={{ backgroundColor: project.color }}
                          />
                          <span className="text-sm font-medium text-[var(--text-primary)]">
                            {project.icon} {project.name}
                          </span>
                        </div>
                        {selectedProjectId === project.id && (
                          <svg className="w-4 h-4 text-[var(--primary)]" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                          </svg>
                        )}
                      </button>

                      {/* Action buttons on hover */}
                      <div className="absolute right-2 top-2 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            handleManageFiles(project.id)
                          }}
                          className="p-1 hover:bg-[var(--surface-elevated)] rounded"
                          title="Manage files"
                        >
                          <svg className="w-4 h-4 text-[var(--text-secondary)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                          </svg>
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            handleEditProject(project.id)
                          }}
                          className="p-1 hover:bg-[var(--surface-elevated)] rounded"
                          title="Edit project"
                        >
                          <svg className="w-4 h-4 text-[var(--text-secondary)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                          </svg>
                        </button>
                      </div>
                    </div>
                  ))
                )}

                <div className="border-t border-[var(--border-primary)] my-2" />

                {/* Manage files button - only show when a project is selected */}
                {selectedProjectId && (
                  <>
                    <button
                      onClick={() => {
                        setProjectFilesOpen(true)
                        setProjectMenuOpen(false)
                      }}
                      className="w-full px-4 py-2 text-left hover:bg-[var(--surface-elevated)] transition-colors flex items-center gap-2"
                    >
                      <svg className="w-4 h-4 text-[var(--text-secondary)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                      <span className="text-sm font-medium text-[var(--text-primary)]">Manage Files</span>
                    </button>
                    <div className="border-t border-[var(--border-primary)] my-2" />
                  </>
                )}

                {/* Create new project button */}
                <button
                  onClick={handleCreateProject}
                  className="w-full px-4 py-2 text-left hover:bg-[var(--surface-elevated)] transition-colors flex items-center gap-2"
                >
                  <svg className="w-4 h-4 text-[var(--primary)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                  </svg>
                  <span className="text-sm font-medium text-[var(--primary)]">New Project</span>
                </button>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Center: Model selector dropdown and thinking toggle */}
      <div className="flex items-center gap-2 relative" data-tour="model-selector">
        <button
          onClick={() => setModelDropdownOpen(!modelDropdownOpen)}
          className="flex items-center gap-2 px-3 py-1.5 bg-[var(--surface-elevated)] hover:bg-[var(--bg-primary)] rounded-full text-sm transition-colors"
          title="Select model"
        >
          <span className="text-[var(--text-primary)] font-medium">{currentModel.name}</span>
          <span className="text-[var(--text-secondary)] text-xs">{currentModel.description}</span>
          <svg className={`w-4 h-4 text-[var(--text-secondary)] transition-transform ${modelDropdownOpen ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </button>

        {/* Extended Thinking Toggle - hidden on mobile */}
        {!isMobile && (
          <button
            data-tour="thinking-toggle"
            onClick={toggleExtendedThinking}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-sm transition-colors border ${
              extendedThinkingEnabled
                ? 'bg-[var(--primary)] text-white border-[var(--primary)]'
                : 'bg-[var(--surface-elevated)] hover:bg-[var(--bg-primary)] border-[var(--border-primary)] text-[var(--text-secondary)]'
            }`}
            title="Toggle extended thinking mode"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
            </svg>
            <span>Thinking</span>
          </button>
        )}

        {/* Model Comparison Toggle - hidden on mobile */}
        {!isMobile && (
          <button
            onClick={() => {
              if (comparisonMode) {
                toggleComparisonMode()
              } else {
                setComparisonModalOpen(true)
              }
            }}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-sm transition-colors border ${
              comparisonMode
                ? 'bg-[var(--primary)] text-white border-[var(--primary)]'
                : 'bg-[var(--surface-elevated)] hover:bg-[var(--bg-primary)] border-[var(--border-primary)] text-[var(--text-secondary)]'
            }`}
            title="Toggle model comparison mode"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
            <span>Compare</span>
          </button>
        )}

        {/* Branch Selector - only show when in a conversation */}
        {currentConversationId && <BranchSelector conversationId={currentConversationId} />}

        {/* Dropdown menu - Feature #151: Model capabilities display */}
        {modelDropdownOpen && (
          <>
            <div
              className="fixed inset-0 z-10"
              onClick={() => setModelDropdownOpen(false)}
            />
            <div className="absolute top-full left-1/2 -translate-x-1/2 mt-2 w-80 bg-[var(--bg-primary)] border border-[var(--border-primary)] rounded-lg shadow-lg z-20 py-2 max-h-[60vh] overflow-y-auto">
              {MODELS.map((model) => (
                <div key={model.id}>
                  <button
                    onClick={() => {
                      setSelectedModel(model.id)
                      setModelDropdownOpen(false)
                    }}
                    className={`w-full px-4 py-3 text-left hover:bg-[var(--surface-elevated)] transition-colors ${
                      selectedModel === model.id ? 'bg-[var(--surface-elevated)]' : ''
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <div>
                        <div className="font-medium text-[var(--text-primary)]">{model.name}</div>
                        <div className="text-xs text-[var(--text-secondary)]">{model.description}</div>
                      </div>
                      {selectedModel === model.id && (
                        <svg className="w-5 h-5 text-[var(--primary)]" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                        </svg>
                      )}
                    </div>
                  </button>
                  <div className="px-4 pb-3 pt-0 text-xs text-[var(--text-secondary)] space-y-1 bg-[var(--bg-secondary)]/50 mx-2 mb-2 rounded">
                    <div className="font-medium text-[var(--text-primary)]">Capabilities:</div>
                    <div className="flex flex-wrap gap-1">
                      {model.capabilities.map((cap) => (
                        <span key={cap} className="px-1.5 py-0.5 bg-[var(--bg-tertiary)] rounded text-[10px]">
                          {cap}
                        </span>
                      ))}
                    </div>
                    <div className="pt-1 border-t border-[var(--border-primary)]/30 mt-1">
                      <div className="font-medium text-[var(--text-primary)]">Strengths:</div>
                      <div>{model.strengths}</div>
                    </div>
                    <div className="pt-1 border-t border-[var(--border-primary)]/30 mt-1">
                      <div className="font-medium text-[var(--text-primary)]">Limits:</div>
                      <div>{model.limits}</div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </>
        )}
      </div>

      {/* Right: Actions */}
      <div className="flex items-center gap-2">
        {/* Checkpoint button - only show when in a conversation */}
        {conversationId && (
          <button
            onClick={() => setCheckpointManagerOpen(true)}
            className="p-2 hover:bg-[var(--surface-elevated)] rounded-lg transition-colors"
            title="Manage checkpoints"
          >
            <svg className="w-5 h-5 text-[var(--text-primary)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </button>
        )}

        {/* Todo button - only show when in a conversation and not mobile */}
        {conversationId && !isMobile && (
          <button
            onClick={() => {
              const { panelType, setPanelType, panelOpen, setPanelOpen } = useUIStore.getState()
              if (panelType === 'todos' && panelOpen) {
                setPanelOpen(false)
                setTimeout(() => setPanelType(null), 300)
              } else {
                setPanelType('todos')
                setPanelOpen(true)
              }
            }}
            className="p-2 hover:bg-[var(--surface-elevated)] rounded-lg transition-colors"
            title="Toggle task list"
          >
            <svg className="w-5 h-5 text-[var(--text-primary)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
          </button>
        )}

        {/* Files button - only show when in a conversation and not mobile */}
        {conversationId && !isMobile && (
          <button
            onClick={() => {
              const { panelType, setPanelType, panelOpen, setPanelOpen } = useUIStore.getState()
              if (panelType === 'files' && panelOpen) {
                setPanelOpen(false)
                setTimeout(() => setPanelType(null), 300)
              } else {
                setPanelType('files')
                setPanelOpen(true)
              }
            }}
            className="p-2 hover:bg-[var(--surface-elevated)] rounded-lg transition-colors"
            title="Toggle workspace files"
          >
            <svg className="w-5 h-5 text-[var(--text-primary)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </button>
        )}

        {/* Diff button - only show when in a conversation and not mobile */}
        {conversationId && !isMobile && (
          <button
            onClick={() => {
              const { panelType, setPanelType, panelOpen, setPanelOpen } = useUIStore.getState()
              if (panelType === 'diffs' && panelOpen) {
                setPanelOpen(false)
                setTimeout(() => setPanelType(null), 300)
              } else {
                setPanelType('diffs')
                setPanelOpen(true)
              }
            }}
            className="p-2 hover:bg-[var(--surface-elevated)] rounded-lg transition-colors"
            title="Toggle file changes"
          >
            <svg className="w-5 h-5 text-[var(--text-primary)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
            </svg>
          </button>
        )}

        {/* Memory button - only show when in a conversation and not mobile */}
        {conversationId && !isMobile && (
          <button
            onClick={() => {
              const { panelType, setPanelType, panelOpen, setPanelOpen } = useUIStore.getState()
              if (panelType === 'memory' && panelOpen) {
                setPanelOpen(false)
                setTimeout(() => setPanelType(null), 300)
              } else {
                setPanelType('memory')
                setPanelOpen(true)
              }
            }}
            className="p-2 hover:bg-[var(--surface-elevated)] rounded-lg transition-colors"
            title="Toggle memory management"
          >
            <svg className="w-5 h-5 text-[var(--text-primary)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
            </svg>
          </button>
        )}

        {/* Export button - only show when in a conversation */}
        {conversationId && (
          <div className="relative">
            <button
              onClick={() => setExportMenuOpen(!exportMenuOpen)}
              disabled={isExporting}
              className="p-2 hover:bg-[var(--surface-elevated)] rounded-lg transition-colors disabled:opacity-50"
              title="Export conversation"
            >
              <svg className="w-5 h-5 text-[var(--text-primary)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
            </button>

            {/* Export dropdown menu */}
            {exportMenuOpen && (
              <>
                <div
                  className="fixed inset-0 z-10"
                  onClick={() => setExportMenuOpen(false)}
                />
                <div className="absolute top-full right-0 mt-2 w-48 bg-[var(--bg-primary)] border border-[var(--border-primary)] rounded-lg shadow-lg z-20 py-2">
                  <div className="px-3 py-2 text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wider">
                    Export as
                  </div>
                  <button
                    onClick={() => handleExport('json')}
                    disabled={isExporting}
                    className="w-full px-4 py-2 text-left hover:bg-[var(--surface-elevated)] transition-colors flex items-center gap-2 disabled:opacity-50"
                  >
                    <span>📄</span>
                    <span className="text-sm text-[var(--text-primary)]">JSON</span>
                  </button>
                  <button
                    onClick={() => handleExport('markdown')}
                    disabled={isExporting}
                    className="w-full px-4 py-2 text-left hover:bg-[var(--surface-elevated)] transition-colors flex items-center gap-2 disabled:opacity-50"
                  >
                    <span>📝</span>
                    <span className="text-sm text-[var(--text-primary)]">Markdown</span>
                  </button>
                  <button
                    onClick={handlePDFExport}
                    disabled={isExporting}
                    className="w-full px-4 py-2 text-left hover:bg-[var(--surface-elevated)] transition-colors flex items-center gap-2 disabled:opacity-50"
                  >
                    <span>📕</span>
                    <span className="text-sm text-[var(--text-primary)]">PDF</span>
                  </button>
                  {isExporting && (
                    <div className="px-4 py-2 text-xs text-[var(--text-secondary)]">
                      Exporting...
                    </div>
                  )}
                </div>
              </>
            )}
          </div>
        )}

        {/* Share button - only show when in a conversation */}
        {conversationId && (
          <button
            onClick={() => setShareModalOpen(true)}
            className="p-2 hover:bg-[var(--surface-elevated)] rounded-lg transition-colors"
            title="Share conversation"
          >
            <svg className="w-5 h-5 text-[var(--text-primary)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" />
            </svg>
          </button>
        )}

        {/* Prompt Library button */}
        <button
          data-tour="prompt-library"
          onClick={() => setPromptModalOpen(true)}
          className="p-2 hover:bg-[var(--surface-elevated)] rounded-lg transition-colors"
          title="Prompt Library"
        >
          <svg className="w-5 h-5 text-[var(--text-primary)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
        </button>

        {/* MCP Server button */}
        <button
          data-tour="mcp-servers"
          onClick={() => setMcpModalOpen(true)}
          className="p-2 hover:bg-[var(--surface-elevated)] rounded-lg transition-colors"
          title="MCP Servers"
        >
          <svg className="w-5 h-5 text-[var(--text-primary)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01" />
          </svg>
        </button>

        {/* SubAgent button */}
        <button
          onClick={() => setSubAgentModalOpen(true)}
          className="p-2 hover:bg-[var(--surface-elevated)] rounded-lg transition-colors"
          title="SubAgent Library"
        >
          <svg className="w-5 h-5 text-[var(--text-primary)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
          </svg>
        </button>

        {/* Memory button */}
        <button
          onClick={() => setMemoryManagerOpen(true)}
          className="p-2 hover:bg-[var(--surface-elevated)] rounded-lg transition-colors"
          title="Memory Manager"
        >
          <svg className="w-5 h-5 text-[var(--text-primary)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
          </svg>
        </button>

        {/* Settings button */}
        <Tooltip content="Settings" shortcut="Ctrl+,">
          <button
            onClick={() => setSettingsOpen(true)}
            className="p-2 hover:bg-[var(--surface-elevated)] rounded-lg transition-colors"
            aria-label="Open settings"
          >
            <svg className="w-5 h-5 text-[var(--text-primary)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
          </button>
        </Tooltip>

        {/* Network status indicator - only show when offline */}
        {isOffline && <NetworkStatusBadge />}
      </div>
    </div>

    {/* Settings Modal */}
    {settingsOpen && <SettingsModal onClose={() => setSettingsOpen(false)} />}

    {/* Project Modal */}
    {projectModalOpen && (
      <ProjectModal
        isOpen={projectModalOpen}
        onClose={() => {
          setProjectModalOpen(false)
          setEditingProject(null)
        }}
        project={editingProject ? projects.find(p => p.id === editingProject.id) : undefined}
      />
    )}

    {/* Project Files Modal */}
    {projectFilesOpen && selectedProject && (
      <ProjectFilesModal
        isOpen={projectFilesOpen}
        onClose={() => setProjectFilesOpen(false)}
        projectId={selectedProject.id}
        projectName={selectedProject.name}
      />
    )}

    {/* Checkpoint Manager Modal */}
    {checkpointManagerOpen && (
      <CheckpointManager onClose={() => setCheckpointManagerOpen(false)} />
    )}

    {/* SubAgent Modal */}
    {subAgentModalOpen && (
      <SubAgentModal onClose={() => setSubAgentModalOpen(false)} />
    )}

    {/* Memory Manager Modal */}
    {memoryManagerOpen && (
      <MemoryManager onClose={() => setMemoryManagerOpen(false)} />
    )}

    {/* Share Modal */}
    {shareModalOpen && conversationId && (
      <ShareModal
        conversationId={conversationId}
        conversationTitle={conversations.find(c => c.id === conversationId)?.title || 'Untitled Conversation'}
        onClose={() => setShareModalOpen(false)}
      />
    )}

    {/* Prompt Modal */}
    {promptModalOpen && (
      <PromptModal
        onClose={() => setPromptModalOpen(false)}
        onUsePrompt={(content) => {
          // Find the ChatInput component and set its value
          // This will be handled by the parent component via context or store
          // For now, we'll use a custom event
          const event = new CustomEvent('usePrompt', { detail: { content } })
          window.dispatchEvent(event)
        }}
        isOpen={promptModalOpen}
      />
    )}

    {/* MCP Modal */}
    {mcpModalOpen && (
      <MCPModal
        isOpen={mcpModalOpen}
        onClose={() => setMcpModalOpen(false)}
      />
    )}

    {/* Model Comparison Modal */}
    {comparisonModalOpen && (
      <ComparisonModal
        isOpen={comparisonModalOpen}
        onClose={() => setComparisonModalOpen(false)}
        tempComparisonModels={tempComparisonModels}
        setTempComparisonModels={setTempComparisonModels}
        onConfirm={() => {
          setComparisonModels(tempComparisonModels)
          toggleComparisonMode()
          setComparisonModalOpen(false)
        }}
      />
    )}
    </>
  )
}
