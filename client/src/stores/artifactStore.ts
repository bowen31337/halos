import { create } from 'zustand'

export interface Artifact {
  id: string
  title: string
  content: string
  language: string
  artifact_type: string
  version: number
  createdAt: string
  conversationId?: string
  parentArtifactId?: string
}

interface ArtifactState {
  artifacts: Artifact[]
  currentArtifactId: string | null
  isDetecting: boolean
  versions: Artifact[] // For version history
  isLoadingVersions: boolean

  // Actions
  setArtifacts: (artifacts: Artifact[]) => void
  addArtifact: (artifact: Artifact) => void
  removeArtifact: (id: string) => void
  setCurrentArtifactId: (id: string | null) => void
  clearArtifacts: () => void
  setVersions: (versions: Artifact[]) => void

  // API Actions
  detectArtifacts: (content: string, conversationId?: string) => Promise<Artifact[]>
  createArtifact: (artifact: Omit<Artifact, 'id' | 'version' | 'createdAt'>) => Promise<Artifact>
  loadArtifactsForConversation: (conversationId: string) => Promise<void>
  updateArtifact: (artifactId: string, data: { content?: string; title?: string }) => Promise<Artifact>
  deleteArtifact: (artifactId: string) => Promise<void>
  forkArtifact: (artifactId: string) => Promise<Artifact>
  getArtifactVersions: (artifactId: string) => Promise<Artifact[]>
  downloadArtifact: (artifactId: string) => Promise<{ filename: string; content: string; content_type: string }>
}

export const useArtifactStore = create<ArtifactState>((set) => ({
  artifacts: [],
  currentArtifactId: null,
  isDetecting: false,
  versions: [],
  isLoadingVersions: false,

  setArtifacts: (artifacts) => set({ artifacts }),

  addArtifact: (artifact) => set((state) => {
    // Check if artifact already exists to avoid duplicates
    const exists = state.artifacts.some(a => a.id === artifact.id)
    if (exists) {
      return { artifacts: state.artifacts }
    }
    return {
      artifacts: [...state.artifacts, artifact],
      currentArtifactId: state.currentArtifactId || artifact.id
    }
  }),

  removeArtifact: (id) => set((state) => ({
    artifacts: state.artifacts.filter(a => a.id !== id),
    currentArtifactId: state.currentArtifactId === id ? null : state.currentArtifactId
  })),

  setCurrentArtifactId: (id) => set({ currentArtifactId: id }),

  clearArtifacts: () => set({ artifacts: [], currentArtifactId: null, versions: [] }),

  setVersions: (versions) => set({ versions }),

  detectArtifacts: async (content: string, conversationId?: string): Promise<Artifact[]> => {
    set({ isDetecting: true })
    try {
      const response = await fetch('/api/artifacts/detect', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content, conversation_id: conversationId }),
      })

      if (!response.ok) {
        throw new Error(`Detection failed: ${response.status}`)
      }

      const detected = await response.json()

      // Convert detected artifacts to full artifacts with IDs
      const artifacts: Artifact[] = detected.map((d: any) => ({
        id: crypto.randomUUID(),
        title: d.title,
        content: d.content,
        language: d.language,
        artifact_type: d.artifact_type || 'code',
        version: 1,
        createdAt: new Date().toISOString(),
        conversationId,
      }))

      // Add to store
      if (artifacts.length > 0) {
        set((state) => ({
          artifacts: [...state.artifacts, ...artifacts],
          currentArtifactId: state.currentArtifactId || artifacts[0].id
        }))
      }

      set({ isDetecting: false })
      return artifacts
    } catch (error) {
      console.error('Artifact detection error:', error)
      set({ isDetecting: false })
      return []
    }
  },

  createArtifact: async (artifactData): Promise<Artifact> => {
    try {
      const response = await fetch('/api/artifacts/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          content: artifactData.content,
          title: artifactData.title,
          language: artifactData.language,
          conversation_id: artifactData.conversationId,
        }),
      })

      if (!response.ok) {
        throw new Error(`Creation failed: ${response.status}`)
      }

      const created = await response.json()
      const artifact: Artifact = {
        id: created.id,
        title: created.title,
        content: created.content,
        language: created.language,
        artifact_type: created.artifact_type || 'code',
        version: created.version,
        createdAt: created.created_at,
        conversationId: created.conversation_id,
        parentArtifactId: created.parent_artifact_id,
      }

      set((state) => ({
        artifacts: [...state.artifacts, artifact],
        currentArtifactId: artifact.id
      }))

      return artifact
    } catch (error) {
      console.error('Artifact creation error:', error)
      throw error
    }
  },

  loadArtifactsForConversation: async (conversationId: string): Promise<void> => {
    try {
      const response = await fetch(`/api/artifacts/conversations/${conversationId}/artifacts`)

      if (!response.ok) {
        throw new Error(`Load failed: ${response.status}`)
      }

      const data = await response.json()
      const artifacts: Artifact[] = data.map((a: any) => ({
        id: a.id,
        title: a.title,
        content: a.content,
        language: a.language,
        artifact_type: a.artifact_type || 'code',
        version: a.version,
        createdAt: a.created_at,
        conversationId: a.conversation_id,
        parentArtifactId: a.parent_artifact_id,
      }))

      set({ artifacts, currentArtifactId: artifacts[0]?.id || null })
    } catch (error) {
      console.error('Load artifacts error:', error)
    }
  },

  updateArtifact: async (artifactId: string, data: { content?: string; title?: string }): Promise<Artifact> => {
    try {
      const response = await fetch(`/api/artifacts/${artifactId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      })

      if (!response.ok) {
        throw new Error(`Update failed: ${response.status}`)
      }

      const updated = await response.json()
      const artifact: Artifact = {
        id: updated.id,
        title: updated.title,
        content: updated.content,
        language: updated.language,
        artifact_type: updated.artifact_type || 'code',
        version: updated.version,
        createdAt: updated.created_at,
        conversationId: updated.conversation_id,
        parentArtifactId: updated.parent_artifact_id,
      }

      set((state) => ({
        artifacts: state.artifacts.map(a => a.id === artifactId ? artifact : a),
      }))

      return artifact
    } catch (error) {
      console.error('Update artifact error:', error)
      throw error
    }
  },

  deleteArtifact: async (artifactId: string): Promise<void> => {
    try {
      const response = await fetch(`/api/artifacts/${artifactId}`, {
        method: 'DELETE',
      })

      if (!response.ok) {
        throw new Error(`Delete failed: ${response.status}`)
      }

      set((state) => ({
        artifacts: state.artifacts.filter(a => a.id !== artifactId),
        currentArtifactId: state.currentArtifactId === artifactId ? null : state.currentArtifactId,
      }))
    } catch (error) {
      console.error('Delete artifact error:', error)
      throw error
    }
  },

  forkArtifact: async (artifactId: string): Promise<Artifact> => {
    try {
      const response = await fetch(`/api/artifacts/${artifactId}/fork`, {
        method: 'POST',
      })

      if (!response.ok) {
        throw new Error(`Fork failed: ${response.status}`)
      }

      const forked = await response.json()
      const artifact: Artifact = {
        id: forked.id,
        title: forked.title,
        content: forked.content,
        language: forked.language,
        artifact_type: forked.artifact_type || 'code',
        version: forked.version,
        createdAt: forked.created_at,
        conversationId: forked.conversation_id,
        parentArtifactId: forked.parent_artifact_id,
      }

      set((state) => ({
        artifacts: [...state.artifacts, artifact],
      }))

      return artifact
    } catch (error) {
      console.error('Fork artifact error:', error)
      throw error
    }
  },

  getArtifactVersions: async (artifactId: string): Promise<Artifact[]> => {
    set({ isLoadingVersions: true })
    try {
      const response = await fetch(`/api/artifacts/${artifactId}/versions`)

      if (!response.ok) {
        throw new Error(`Get versions failed: ${response.status}`)
      }

      const data = await response.json()
      const versions: Artifact[] = data.map((a: any) => ({
        id: a.id,
        title: a.title,
        content: a.content,
        language: a.language,
        artifact_type: a.artifact_type || 'code',
        version: a.version,
        createdAt: a.created_at,
        conversationId: a.conversation_id,
        parentArtifactId: a.parent_artifact_id,
      }))

      set({ versions, isLoadingVersions: false })
      return versions
    } catch (error) {
      console.error('Get artifact versions error:', error)
      set({ isLoadingVersions: false })
      throw error
    }
  },

  downloadArtifact: async (artifactId: string): Promise<{ filename: string; content: string; content_type: string }> => {
    try {
      const response = await fetch(`/api/artifacts/${artifactId}/download`)

      if (!response.ok) {
        throw new Error(`Download failed: ${response.status}`)
      }

      return await response.json()
    } catch (error) {
      console.error('Download artifact error:', error)
      throw error
    }
  },
}))
