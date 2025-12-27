import { create } from 'zustand'
import { api } from '../services/api'

export interface Artifact {
  id: string
  title: string
  content: string
  language: string
  version: number
  createdAt: string
  conversationId?: string
}

interface ArtifactState {
  artifacts: Artifact[]
  currentArtifactId: string | null
  isDetecting: boolean

  // Actions
  setArtifacts: (artifacts: Artifact[]) => void
  addArtifact: (artifact: Artifact) => void
  removeArtifact: (id: string) => void
  setCurrentArtifactId: (id: string | null) => void
  clearArtifacts: () => void

  // API Actions
  detectArtifacts: (content: string, conversationId?: string) => Promise<Artifact[]>
  createArtifact: (artifact: Omit<Artifact, 'id' | 'version' | 'createdAt'>) => Promise<Artifact>
  loadArtifactsForConversation: (conversationId: string) => Promise<void>
}

export const useArtifactStore = create<ArtifactState>((set, get) => ({
  artifacts: [],
  currentArtifactId: null,
  isDetecting: false,

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

  clearArtifacts: () => set({ artifacts: [], currentArtifactId: null }),

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
        version: created.version,
        createdAt: created.created_at,
        conversationId: created.conversation_id,
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
        version: a.version,
        createdAt: a.created_at,
        conversationId: a.conversation_id,
      }))

      set({ artifacts, currentArtifactId: artifacts[0]?.id || null })
    } catch (error) {
      console.error('Load artifacts error:', error)
    }
  },
}))
