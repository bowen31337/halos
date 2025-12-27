import { create } from 'zustand'

export interface Todo {
  id: string
  content: string
  status: 'pending' | 'in_progress' | 'completed' | 'cancelled'
}

export interface WorkspaceFile {
  id: string
  name: string
  path: string
  content: string
  size: number
  file_type: string
  created_at: string
}

export interface FileDiff {
  id: string
  fileId: string
  fileName: string
  oldContent: string
  newContent: string
  timestamp: string
  changeType: 'added' | 'modified' | 'deleted'
}

export interface SubAgentState {
  isDelegated: boolean
  subAgentName: string | null
  reason: string | null
  progress: number
  status: 'idle' | 'delegated' | 'working' | 'completed'
  result: string | null
}

// Interface for delegation events from backend
export interface SubAgentDelegationEvent {
  isActive: boolean
  subAgentName: string
  progress: number
  isCompleted: boolean
  taskDescription?: string
}

interface ChatState {
  // Input
  inputMessage: string
  isStreaming: boolean
  stopRequested: boolean

  // Agent state
  todos: Todo[]
  files: WorkspaceFile[]
  fileHistory: Map<string, string[]> // fileId -> array of content versions
  fileDiffs: FileDiff[]
  subAgent: SubAgentState

  // UI state
  showThinking: boolean

  // Actions
  setInputMessage: (message: string) => void
  setIsStreaming: (streaming: boolean) => void
  setStopRequested: (stop: boolean) => void
  setTodos: (todos: Todo[]) => void
  updateTodo: (id: string, status: Todo['status']) => void
  setFiles: (files: WorkspaceFile[]) => void
  addFile: (file: WorkspaceFile) => void
  updateFile: (id: string, updates: Partial<WorkspaceFile>) => void
  removeFile: (id: string) => void
  clearFiles: () => void
  addFileDiff: (diff: Omit<FileDiff, 'id' | 'timestamp'>) => void
  clearFileDiffs: () => void
  setShowThinking: (show: boolean) => void
  clearInput: () => void
  // SubAgent actions
  setSubAgentDelegated: (name: string, reason: string) => void
  setSubAgentProgress: (progress: number, status?: 'working' | 'completed') => void
  setSubAgentResult: (result: string) => void
  clearSubAgent: () => void
  // Aliases for ChatInput compatibility
  setSubAgentDelegation: (delegation: SubAgentState | null) => void
  updateSubAgentProgress: (progress: number) => void
  completeSubAgentDelegation: () => void
}

export const useChatStore = create<ChatState>((set, get) => ({
  // Initial state
  inputMessage: '',
  isStreaming: false,
  stopRequested: false,
  todos: [],
  files: [],
  fileHistory: new Map(),
  fileDiffs: [],
  showThinking: false,
  subAgent: {
    isDelegated: false,
    subAgentName: null,
    reason: null,
    progress: 0,
    status: 'idle',
    result: null,
  },

  // Actions
  setInputMessage: (message) => set({ inputMessage: message }),
  setIsStreaming: (streaming) => set({ isStreaming: streaming }),
  setStopRequested: (stop) => set({ stopRequested: stop }),
  setTodos: (todos) => set({ todos }),
  updateTodo: (id, status) =>
    set((state) => ({
      todos: state.todos.map((t) => (t.id === id ? { ...t, status } : t)),
    })),
  setFiles: (files) => {
    // Track file changes for diffs
    const state = get()
    const newFileHistory = new Map(state.fileHistory)
    const newFileDiffs: FileDiff[] = [...state.fileDiffs]

    files.forEach((file) => {
      const history = newFileHistory.get(file.id) || []
      const lastContent = history[history.length - 1]

      // Track changes if content differs from last known version
      if (lastContent !== undefined && lastContent !== file.content) {
        newFileDiffs.push({
          id: crypto.randomUUID(),
          fileId: file.id,
          fileName: file.name,
          oldContent: lastContent,
          newContent: file.content,
          timestamp: new Date().toISOString(),
          changeType: 'modified'
        })
      } else if (lastContent === undefined && history.length === 0) {
        // New file added
        newFileDiffs.push({
          id: crypto.randomUUID(),
          fileId: file.id,
          fileName: file.name,
          oldContent: '',
          newContent: file.content,
          timestamp: new Date().toISOString(),
          changeType: 'added'
        })
      }

      // Update history
      newFileHistory.set(file.id, [...history, file.content])
    })

    set({ files, fileHistory: newFileHistory, fileDiffs: newFileDiffs })
  },
  addFile: (file) => {
    const state = get()
    const newFileHistory = new Map(state.fileHistory)
    const newFileDiffs: FileDiff[] = [...state.fileDiffs]

    // Track as new file
    newFileDiffs.push({
      id: crypto.randomUUID(),
      fileId: file.id,
      fileName: file.name,
      oldContent: '',
      newContent: file.content,
      timestamp: new Date().toISOString(),
      changeType: 'added'
    })

    newFileHistory.set(file.id, [file.content])

    set({
      files: [...state.files, file],
      fileHistory: newFileHistory,
      fileDiffs: newFileDiffs
    })
  },
  updateFile: (id, updates) => {
    const state = get()
    const fileToUpdate = state.files.find(f => f.id === id)
    if (!fileToUpdate) return

    const updatedFile = { ...fileToUpdate, ...updates }
    const newFileHistory = new Map(state.fileHistory)
    const newFileDiffs: FileDiff[] = [...state.fileDiffs]

    // Track change if content changed
    if (updates.content !== undefined && updates.content !== fileToUpdate.content) {
      newFileDiffs.push({
        id: crypto.randomUUID(),
        fileId: id,
        fileName: updatedFile.name,
        oldContent: fileToUpdate.content,
        newContent: updates.content!,
        timestamp: new Date().toISOString(),
        changeType: 'modified'
      })

      const history = newFileHistory.get(id) || []
      newFileHistory.set(id, [...history, updates.content!])
    }

    set({
      files: state.files.map((f) => (f.id === id ? updatedFile : f)),
      fileHistory: newFileHistory,
      fileDiffs: newFileDiffs
    })
  },
  removeFile: (id) => {
    const state = get()
    const fileToRemove = state.files.find(f => f.id === id)
    if (!fileToRemove) return

    const newFileDiffs: FileDiff[] = [...state.fileDiffs]
    newFileDiffs.push({
      id: crypto.randomUUID(),
      fileId: id,
      fileName: fileToRemove.name,
      oldContent: fileToRemove.content,
      newContent: '',
      timestamp: new Date().toISOString(),
      changeType: 'deleted'
    })

    set({
      files: state.files.filter((f) => f.id !== id),
      fileDiffs: newFileDiffs
    })
  },
  clearFiles: () => set({ files: [], fileHistory: new Map(), fileDiffs: [] }),
  addFileDiff: (diff) => {
    const newDiff: FileDiff = {
      ...diff,
      id: crypto.randomUUID(),
      timestamp: new Date().toISOString()
    }
    set((state) => ({ fileDiffs: [...state.fileDiffs, newDiff] }))
  },
  clearFileDiffs: () => set({ fileDiffs: [] }),
  setShowThinking: (show) => set({ showThinking: show }),
  clearInput: () => set({ inputMessage: '' }),

  // SubAgent actions
  setSubAgentDelegated: (name, reason) =>
    set({
      subAgent: {
        isDelegated: true,
        subAgentName: name,
        reason: reason,
        progress: 0,
        status: 'delegated',
        result: null,
      },
    }),
  setSubAgentProgress: (progress, status) =>
    set((state) => ({
      subAgent: {
        ...state.subAgent,
        progress,
        status: status || (progress >= 100 ? 'completed' : 'working'),
      },
    })),
  setSubAgentResult: (result) =>
    set((state) => ({
      subAgent: {
        ...state.subAgent,
        result,
        status: 'completed',
        progress: 100,
      },
    })),
  clearSubAgent: () =>
    set({
      subAgent: {
        isDelegated: false,
        subAgentName: null,
        reason: null,
        progress: 0,
        status: 'idle',
        result: null,
      },
    }),
  // Aliases for ChatInput compatibility
  // delegation format: { isActive, subAgentName, progress, isCompleted, taskDescription }
  setSubAgentDelegation: (delegation) =>
    set({
      subAgent: {
        isDelegated: delegation?.isActive || false,
        subAgentName: delegation?.subAgentName || null,
        reason: delegation?.taskDescription || null,
        progress: delegation?.progress || 0,
        status: delegation ? (delegation.isCompleted ? 'completed' : 'delegated') : 'idle',
        result: null,
      },
    }),
  updateSubAgentProgress: (progress) =>
    set((state) => ({
      subAgent: {
        ...state.subAgent,
        progress,
        status: progress >= 100 ? 'completed' : 'working',
      },
    })),
  completeSubAgentDelegation: () =>
    set((state) => ({
      subAgent: {
        ...state.subAgent,
        status: 'completed',
        progress: 100,
      },
    })),
}))
