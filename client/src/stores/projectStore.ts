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

interface ProjectState {
  projects: Project[]
  selectedProjectId: string | null
  isLoading: boolean
  error: string | null

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
}

export const useProjectStore = create<ProjectState>()(
  persist(
    (set, get) => ({
      // Initial state
      projects: [],
      selectedProjectId: null,
      isLoading: false,
      error: null,

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
        set({ projects: [], selectedProjectId: null, error: null })
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
