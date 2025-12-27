import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export interface Project {
  id: string
  name: string
  description?: string
  color: string
  icon?: string
  custom_instructions?: string
  is_archived: boolean
  is_pinned: boolean
  created_at: string
  updated_at: string
}

export interface ProjectFile {
  id: string
  project_id: string
  filename: string
  original_filename: string
  file_url: string
  file_size: number
  content_type?: string
  content?: string
  created_at: string
}

interface ProjectState {
  projects: Project[]
  selectedProjectId: string | null
  isLoading: boolean
  error: string | null
  files: ProjectFile[] // Files for currently selected project

  // Actions
  fetchProjects: () => Promise<void>
  createProject: (data: {
    name: string
    description?: string
    color?: string
    icon?: string
    custom_instructions?: string
  }) => Promise<Project>
  updateProject: (id: string, data: Partial<Project>) => Promise<void>
  deleteProject: (id: string) => Promise<void>
  setSelectedProject: (id: string | null) => void
  clearProjects: () => void

  // File actions
  fetchFiles: (projectId: string) => Promise<void>
  uploadFile: (projectId: string, file: File) => Promise<ProjectFile>
  deleteFile: (projectId: string, fileId: string) => Promise<void>
  clearFiles: () => void
}

export const useProjectStore = create<ProjectState>()(
  persist(
    (set, get) => ({
      // Initial state
      projects: [],
      selectedProjectId: null,
      isLoading: false,
      error: null,
      files: [],

      // Fetch all projects
      fetchProjects: async () => {
        set({ isLoading: true, error: null })
        try {
          const response = await fetch('/api/projects')
          if (!response.ok) throw new Error('Failed to fetch projects')

          const projects: Project[] = await response.json()
          set({ projects, isLoading: false })
        } catch (error) {
          set({
            error: error instanceof Error ? error.message : 'Failed to fetch projects',
            isLoading: false,
          })
        }
      },

      // Create a new project
      createProject: async (data) => {
        set({ isLoading: true, error: null })
        try {
          const response = await fetch('/api/projects', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
          })

          if (!response.ok) throw new Error('Failed to create project')

          const newProject: Project = await response.json()
          set((state) => ({
            projects: [...state.projects, newProject],
            isLoading: false,
          }))

          return newProject
        } catch (error) {
          set({
            error: error instanceof Error ? error.message : 'Failed to create project',
            isLoading: false,
          })
          throw error
        }
      },

      // Update an existing project
      updateProject: async (id, data) => {
        set({ isLoading: true, error: null })
        try {
          const response = await fetch(`/api/projects/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
          })

          if (!response.ok) throw new Error('Failed to update project')

          const updatedProject: Project = await response.json()
          set((state) => ({
            projects: state.projects.map((p) => (p.id === id ? updatedProject : p)),
            isLoading: false,
          }))
        } catch (error) {
          set({
            error: error instanceof Error ? error.message : 'Failed to update project',
            isLoading: false,
          })
          throw error
        }
      },

      // Delete a project
      deleteProject: async (id) => {
        set({ isLoading: true, error: null })
        try {
          const response = await fetch(`/api/projects/${id}`, {
            method: 'DELETE',
          })

          if (!response.ok) throw new Error('Failed to delete project')

          set((state) => ({
            projects: state.projects.filter((p) => p.id !== id),
            selectedProjectId: state.selectedProjectId === id ? null : state.selectedProjectId,
            isLoading: false,
          }))
        } catch (error) {
          set({
            error: error instanceof Error ? error.message : 'Failed to delete project',
            isLoading: false,
          })
          throw error
        }
      },

      // Set the currently selected project
      setSelectedProject: (id) => {
        set({ selectedProjectId: id })
      },

      // Clear all projects (for testing/logout)
      clearProjects: () => {
        set({ projects: [], selectedProjectId: null, error: null, files: [] })
      },

      // Fetch files for a project
      fetchFiles: async (projectId: string) => {
        set({ isLoading: true, error: null })
        try {
          const response = await fetch(`/api/projects/${projectId}/files`)
          if (!response.ok) throw new Error('Failed to fetch files')

          const files: ProjectFile[] = await response.json()
          set({ files, isLoading: false })
        } catch (error) {
          set({
            error: error instanceof Error ? error.message : 'Failed to fetch files',
            isLoading: false,
          })
        }
      },

      // Upload a file to a project
      uploadFile: async (projectId: string, file: File) => {
        set({ isLoading: true, error: null })
        try {
          const formData = new FormData()
          formData.append('file', file)

          const response = await fetch(`/api/projects/${projectId}/files`, {
            method: 'POST',
            body: formData,
          })

          if (!response.ok) throw new Error('Failed to upload file')

          const newFile: ProjectFile = await response.json()
          set((state) => ({
            files: [newFile, ...state.files],
            isLoading: false,
          }))

          return newFile
        } catch (error) {
          set({
            error: error instanceof Error ? error.message : 'Failed to upload file',
            isLoading: false,
          })
          throw error
        }
      },

      // Delete a file from a project
      deleteFile: async (projectId: string, fileId: string) => {
        set({ isLoading: true, error: null })
        try {
          const response = await fetch(`/api/projects/${projectId}/files/${fileId}`, {
            method: 'DELETE',
          })

          if (!response.ok) throw new Error('Failed to delete file')

          set((state) => ({
            files: state.files.filter((f) => f.id !== fileId),
            isLoading: false,
          }))
        } catch (error) {
          set({
            error: error instanceof Error ? error.message : 'Failed to delete file',
            isLoading: false,
          })
          throw error
        }
      },

      // Clear files
      clearFiles: () => {
        set({ files: [] })
      },
    }),
    {
      name: 'claude-project-store',
      partialize: (state) => ({
        selectedProjectId: state.selectedProjectId,
      }),
    }
  )
)
