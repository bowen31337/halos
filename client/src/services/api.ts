/**
 * API Service for backend communication
 */

import type { Conversation, Message, Tag } from '@/stores/conversationStore'

const API_BASE = '/api'

export interface AgentRequest {
  message: string
  conversationId?: string
  threadId?: string
  model?: string
  permissionMode?: string
  extendedThinking?: boolean
  customInstructions?: string
  systemPromptOverride?: string
  temperature?: number
  maxTokens?: number
}

export interface AgentResponse {
  threadId: string
  response: string
  model: string
  status: string
}

export interface SSEEvent {
  event: 'start' | 'message' | 'tool_start' | 'tool_end' | 'done' | 'error' | 'thinking' | 'todos' | 'files' | 'interrupt' | 'subagent_start' | 'subagent_progress' | 'subagent_end'
  data: string
}

class APIService {
  // Health check
  async healthCheck(): Promise<{ status: string; version: string }> {
    const response = await fetch(`${API_BASE}/health`)
    return response.json()
  }

  // Conversation APIs
  async listConversations(): Promise<Conversation[]> {
    const response = await fetch(`${API_BASE}/conversations`)
    return response.json()
  }

  async createConversation(data: {
    title?: string
    projectId?: string
    model?: string
  }): Promise<Conversation> {
    const response = await fetch(`${API_BASE}/conversations`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })
    return response.json()
  }

  async getConversation(id: string): Promise<Conversation> {
    const response = await fetch(`${API_BASE}/conversations/${id}`)
    return response.json()
  }

  async updateConversation(
    id: string,
    data: { title?: string; isArchived?: boolean; isPinned?: boolean }
  ): Promise<Conversation> {
    const response = await fetch(`${API_BASE}/conversations/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })
    return response.json()
  }

  async deleteConversation(id: string): Promise<void> {
    await fetch(`${API_BASE}/conversations/${id}`, {
      method: 'DELETE',
    })
  }

  async moveConversation(id: string, projectId: string | null): Promise<Conversation> {
    const response = await fetch(`${API_BASE}/conversations/${id}/move`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ project_id: projectId }),
    })
    return response.json()
  }

  async duplicateConversation(id: string): Promise<Conversation> {
    const response = await fetch(`${API_BASE}/conversations/${id}/duplicate`, {
      method: 'POST',
    })
    return response.json()
  }

  async exportConversation(id: string, format: 'json' | 'markdown'): Promise<Blob> {
    const response = await fetch(`${API_BASE}/conversations/${id}/export?format=${format}`, {
      method: 'POST',
    })
    if (!response.ok) {
      throw new Error(`Export failed: ${response.status}`)
    }
    return response.blob()
  }

  // Batch Operations
  async batchExportConversations(
    conversationIds: string[],
    format: 'json' | 'markdown' = 'json'
  ): Promise<Blob> {
    const response = await fetch(`${API_BASE}/conversations/batch/export?format=${format}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ conversation_ids: conversationIds }),
    })
    if (!response.ok) {
      throw new Error(`Batch export failed: ${response.status}`)
    }
    return response.blob()
  }

  async batchDeleteConversations(
    conversationIds: string[]
  ): Promise<{ success_count: number; failure_count: number; deleted_ids: string[] }> {
    const response = await fetch(`${API_BASE}/conversations/batch/delete`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ conversation_ids: conversationIds }),
    })
    if (!response.ok) {
      throw new Error(`Batch delete failed: ${response.status}`)
    }
    return response.json()
  }

  async batchArchiveConversations(
    conversationIds: string[]
  ): Promise<{ success_count: number; failure_count: number; deleted_ids: string[] }> {
    const response = await fetch(`${API_BASE}/conversations/batch/archive`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ conversation_ids: conversationIds }),
    })
    if (!response.ok) {
      throw new Error(`Batch archive failed: ${response.status}`)
    }
    return response.json()
  }

  async batchDuplicateConversations(
    conversationIds: string[]
  ): Promise<{ success_count: number; failure_count: number; results: any[] }> {
    const response = await fetch(`${API_BASE}/conversations/batch/duplicate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ conversation_ids: conversationIds }),
    })
    if (!response.ok) {
      throw new Error(`Batch duplicate failed: ${response.status}`)
    }
    return response.json()
  }

  async batchMoveConversations(
    conversationIds: string[],
    projectId: string | null
  ): Promise<{ success_count: number; failure_count: number; results: any[] }> {
    const params = new URLSearchParams()
    if (projectId) params.append('project_id', projectId)
    const response = await fetch(`${API_BASE}/conversations/batch/move?${params.toString()}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ conversation_ids: conversationIds }),
    })
    if (!response.ok) {
      throw new Error(`Batch move failed: ${response.status}`)
    }
    return response.json()
  }

  async createConversationBranch(
    conversationId: string,
    branchPointMessageId: string,
    branchName?: string,
    branchColor?: string
  ): Promise<any> {
    const response = await fetch(`${API_BASE}/conversations/${conversationId}/branch`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        branch_point_message_id: branchPointMessageId,
        branch_name: branchName,
        branch_color: branchColor
      }),
    })
    if (!response.ok) {
      throw new Error(`Branch creation failed: ${response.status}`)
    }
    return response.json()
  }

  async listConversationBranches(conversationId: string): Promise<any[]> {
    const response = await fetch(`${API_BASE}/conversations/${conversationId}/branches`)
    if (!response.ok) {
      throw new Error(`Failed to get branches: ${response.status}`)
    }
    return response.json()
  }

  async getConversationBranchTree(conversationId: string): Promise<any> {
    const response = await fetch(`${API_BASE}/conversations/${conversationId}/branch-tree`)
    if (!response.ok) {
      throw new Error(`Failed to get branch tree: ${response.status}`)
    }
    return response.json()
  }

  async switchToBranch(
    conversationId: string,
    targetConversationId: string
  ): Promise<any> {
    throw new Error("Switching branches should be handled by switching conversations in the frontend")
  }

  // Message APIs
  async listMessages(conversationId: string): Promise<Message[]> {
    const response = await fetch(`${API_BASE}/messages/conversations/${conversationId}/messages`)
    return response.json()
  }

  async createMessage(
    conversationId: string,
    data: { content: string; role: 'user' | 'assistant'; attachments?: string[]; thinkingContent?: string }
  ): Promise<Message> {
    const response = await fetch(`${API_BASE}/messages/conversations/${conversationId}/messages`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })
    return response.json()
  }

  // Agent APIs
  async invokeAgent(data: AgentRequest): Promise<AgentResponse> {
    const response = await fetch(`${API_BASE}/agent/invoke`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })
    return response.json()
  }

  async streamAgent(
    data: AgentRequest,
    onMessage: (content: string) => void,
    onToolStart?: (tool: string, input: any) => void,
    onToolEnd?: (output: string) => void,
    onDone?: (thinkingContent?: string) => void,
    onError?: (error: string) => void,
    onThinking?: (content: string, status?: string) => void
  ): Promise<void> {
    const response = await fetch(`${API_BASE}/agent/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })

    if (!response.ok) {
      onError?.(`HTTP error! status: ${response.status}`)
      return
    }

    const reader = response.body?.getReader()
    if (!reader) {
      onError?.('No response body')
      return
    }

    const decoder = new TextDecoder()
    let buffer = ''

    try {
      // SSE events can span multiple lines: event: X \n data: Y \n\n
      // We need to buffer event and data lines together
      let currentEvent: string | null = null
      let currentData: string | null = null

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || '' // Keep incomplete line in buffer

        for (const line of lines) {
          const trimmed = line.trim()

          if (trimmed.startsWith('event:')) {
            currentEvent = trimmed.slice(6).trim()
          } else if (trimmed.startsWith('data:')) {
            currentData = trimmed.slice(5).trim()
          } else if (trimmed === '') {
            // Empty line indicates end of event, process what we have
            if (currentEvent && currentData) {
              try {
                const eventData = JSON.parse(currentData)

                switch (currentEvent) {
                  case 'message':
                    if (eventData.content) onMessage(eventData.content)
                    break
                  case 'thinking':
                    onThinking?.(eventData.content || '', eventData.status)
                    break
                  case 'tool_start':
                    onToolStart?.(eventData.tool, eventData.input)
                    break
                  case 'tool_end':
                    onToolEnd?.(eventData.output)
                    break
                  case 'done':
                    onDone?.(eventData.thinking_content)
                    break
                  case 'error':
                    onError?.(eventData.error)
                    break
                  case 'start':
                    // Start event - could be used for initialization
                    break
                }
              } catch (e) {
                console.warn('Failed to parse SSE data:', e)
              }

              // Reset for next event
              currentEvent = null
              currentData = null
            } else if (currentData) {
              // Handle data-only lines (fallback for non-standard format)
              try {
                const eventData = JSON.parse(currentData)
                if (eventData.content) onMessage(eventData.content)
              } catch (e) {
                console.warn('Failed to parse SSE data:', e)
              }
              currentData = null
            }
          }
        }
      }
    } catch (e) {
      onError?.(String(e))
    } finally {
      reader.releaseLock()
    }
  }

  async handleInterrupt(
    threadId: string,
    decision: 'approve' | 'edit' | 'reject',
    editedInput?: any
  ): Promise<any> {
    const response = await fetch(`${API_BASE}/agent/interrupt`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ threadId, decision, editedInput }),
    })
    return response.json()
  }

  async getPendingApproval(threadId: string): Promise<any> {
    const response = await fetch(`${API_BASE}/agent/pending-approval/${threadId}`)
    return response.json()
  }

  async getAgentState(threadId: string): Promise<any> {
    const response = await fetch(`${API_BASE}/agent/state/${threadId}`)
    return response.json()
  }

  async getTodos(threadId: string): Promise<any> {
    const response = await fetch(`${API_BASE}/agent/todos/${threadId}`)
    return response.json()
  }

  async getWorkspaceFiles(threadId: string): Promise<any> {
    const response = await fetch(`${API_BASE}/agent/files/${threadId}`)
    return response.json()
  }

  // SubAgent APIs
  async getBuiltinSubagents(): Promise<any[]> {
    const response = await fetch(`${API_BASE}/subagents/builtin`)
    return response.json()
  }

  async getSubagents(includeBuiltin: boolean = true): Promise<any[]> {
    const response = await fetch(`${API_BASE}/subagents?include_builtin=${includeBuiltin}`)
    return response.json()
  }

  async getSubagent(subagentId: string): Promise<any> {
    const response = await fetch(`${API_BASE}/subagents/${subagentId}`)
    return response.json()
  }

  async createSubagent(data: {
    name: string
    description?: string
    system_prompt: string
    model?: string
    tools?: string[]
  }): Promise<any> {
    const response = await fetch(`${API_BASE}/subagents`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })
    return response.json()
  }

  async updateSubagent(subagentId: string, data: {
    description?: string
    system_prompt?: string
    model?: string
    tools?: string[]
    is_active?: boolean
  }): Promise<any> {
    const response = await fetch(`${API_BASE}/subagents/${subagentId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })
    return response.json()
  }

  async deleteSubagent(subagentId: string): Promise<void> {
    const response = await fetch(`${API_BASE}/subagents/${subagentId}`, {
      method: 'DELETE',
    })
    if (!response.ok) {
      throw new Error(`Failed to delete subagent: ${response.status}`)
    }
  }

  async getSubagentTools(subagentId: string): Promise<string[]> {
    const response = await fetch(`${API_BASE}/subagents/${subagentId}/tools`)
    return response.json()
  }

  // Settings APIs
  async getSettings(): Promise<any> {
    const response = await fetch(`${API_BASE}/settings`)
    return response.json()
  }

  async updateSettings(data: any): Promise<any> {
    const response = await fetch(`${API_BASE}/settings`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })
    return response.json()
  }

  async updateCustomInstructions(instructions: string): Promise<any> {
    const response = await fetch(`${API_BASE}/settings/custom-instructions`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ instructions }),
    })
    return response.json()
  }

  async updateSystemPrompt(prompt: string): Promise<any> {
    const response = await fetch(`${API_BASE}/settings/system-prompt`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prompt }),
    })
    return response.json()
  }

  // Project File APIs
  async listProjectFiles(projectId: string): Promise<any[]> {
    const response = await fetch(`${API_BASE}/projects/${projectId}/files`)
    return response.json()
  }

  async uploadProjectFile(projectId: string, file: File): Promise<any> {
    const formData = new FormData()
    formData.append('file', file)
    const response = await fetch(`${API_BASE}/projects/${projectId}/files`, {
      method: 'POST',
      body: formData,
    })
    if (!response.ok) {
      throw new Error(`Upload failed: ${response.status}`)
    }
    return response.json()
  }

  async downloadProjectFile(projectId: string, filename: string): Promise<Blob> {
    const response = await fetch(`${API_BASE}/projects/${projectId}/files/${filename}`)
    if (!response.ok) {
      throw new Error(`Download failed: ${response.status}`)
    }
    return response.blob()
  }

  async deleteProjectFile(projectId: string, fileId: string): Promise<void> {
    const response = await fetch(`${API_BASE}/projects/${projectId}/files/${fileId}`, {
      method: 'DELETE',
    })
    if (!response.ok) {
      throw new Error(`Delete failed: ${response.status}`)
    }
  }

  async getProjectFileContent(projectId: string, fileId: string): Promise<any> {
    const response = await fetch(`${API_BASE}/projects/${projectId}/files/${fileId}/content`)
    return response.json()
  }

  // Artifact APIs
  async listArtifacts(conversationId: string): Promise<any[]> {
    const response = await fetch(`${API_BASE}/artifacts/conversations/${conversationId}/artifacts`)
    return response.json()
  }

  async createArtifact(data: {
    conversation_id: string
    content: string
    title: string
    language: string
  }): Promise<any> {
    const response = await fetch(`${API_BASE}/artifacts/create`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })
    if (!response.ok) {
      throw new Error(`Failed to create artifact: ${response.status}`)
    }
    return response.json()
  }

  async getArtifact(artifactId: string): Promise<any> {
    const response = await fetch(`${API_BASE}/artifacts/${artifactId}`)
    return response.json()
  }

  async updateArtifact(artifactId: string, data: { content?: string; title?: string }): Promise<any> {
    const response = await fetch(`${API_BASE}/artifacts/${artifactId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })
    return response.json()
  }

  async deleteArtifact(artifactId: string): Promise<void> {
    const response = await fetch(`${API_BASE}/artifacts/${artifactId}`, {
      method: 'DELETE',
    })
    if (!response.ok) {
      throw new Error(`Failed to delete artifact: ${response.status}`)
    }
  }

  async forkArtifact(artifactId: string): Promise<any> {
    const response = await fetch(`${API_BASE}/artifacts/${artifactId}/fork`, {
      method: 'POST',
    })
    return response.json()
  }

  async getArtifactVersions(artifactId: string): Promise<any[]> {
    const response = await fetch(`${API_BASE}/artifacts/${artifactId}/versions`)
    return response.json()
  }

  async downloadArtifact(artifactId: string): Promise<any> {
    const response = await fetch(`${API_BASE}/artifacts/${artifactId}/download`)
    return response.json()
  }

  async executeArtifact(artifactId: string, timeout: number = 10): Promise<{
    artifact_id: string
    title: string
    language: string
    execution: {
      success: boolean
      output: string
      error: string | null
      execution_time: number
      return_code: number
    }
  }> {
    const response = await fetch(`${API_BASE}/artifacts/${artifactId}/execute`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ timeout }),
    })
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }))
      throw new Error(error.detail || `Failed to execute artifact: ${response.status}`)
    }
    return response.json()
  }

  async detectArtifacts(content: string): Promise<any[]> {
    const response = await fetch(`${API_BASE}/artifacts/detect`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content }),
    })
    return response.json()
  }

  // Checkpoint APIs
  async listCheckpoints(conversationId: string): Promise<any[]> {
    const response = await fetch(`${API_BASE}/conversations/${conversationId}/checkpoints`)
    return response.json()
  }

  async createCheckpoint(
    conversationId: string,
    data: { name?: string; notes?: string }
  ): Promise<any> {
    const response = await fetch(`${API_BASE}/conversations/${conversationId}/checkpoints`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })
    if (!response.ok) {
      throw new Error(`Failed to create checkpoint: ${response.status}`)
    }
    return response.json()
  }

  async getCheckpoint(checkpointId: string): Promise<any> {
    const response = await fetch(`${API_BASE}/checkpoints/${checkpointId}`)
    return response.json()
  }

  async updateCheckpoint(
    checkpointId: string,
    data: { name?: string; notes?: string }
  ): Promise<any> {
    const response = await fetch(`${API_BASE}/checkpoints/${checkpointId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })
    return response.json()
  }

  async restoreCheckpoint(checkpointId: string): Promise<any> {
    const response = await fetch(`${API_BASE}/checkpoints/${checkpointId}/restore`, {
      method: 'POST',
    })
    if (!response.ok) {
      throw new Error(`Failed to restore checkpoint: ${response.status}`)
    }
    return response.json()
  }

  async deleteCheckpoint(checkpointId: string): Promise<void> {
    const response = await fetch(`${API_BASE}/checkpoints/${checkpointId}`, {
      method: 'DELETE',
    })
    if (!response.ok) {
      throw new Error(`Failed to delete checkpoint: ${response.status}`)
    }
  }

  // Memory APIs
  async listMemories(category?: string, activeOnly: boolean = true): Promise<any[]> {
    const params = new URLSearchParams()
    if (category) params.append('category', category)
    if (activeOnly) params.append('active_only', 'true')
    const response = await fetch(`${API_BASE}/memory?${params}`)
    return response.json()
  }

  async searchMemories(query: string): Promise<any[]> {
    const response = await fetch(`${API_BASE}/memory/search?q=${encodeURIComponent(query)}`)
    return response.json()
  }

  async getMemory(memoryId: string): Promise<any> {
    const response = await fetch(`${API_BASE}/memory/${memoryId}`)
    if (!response.ok) {
      throw new Error(`Failed to get memory: ${response.status}`)
    }
    return response.json()
  }

  async createMemory(data: {
    content: string
    category?: string
  }): Promise<any> {
    const response = await fetch(`${API_BASE}/memory`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })
    if (!response.ok) {
      throw new Error(`Failed to create memory: ${response.status}`)
    }
    return response.json()
  }

  async updateMemory(
    memoryId: string,
    data: {
      content?: string
      category?: string
      is_active?: boolean
    }
  ): Promise<any> {
    const response = await fetch(`${API_BASE}/memory/${memoryId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })
    if (!response.ok) {
      throw new Error(`Failed to update memory: ${response.status}`)
    }
    return response.json()
  }

  async deleteMemory(memoryId: string): Promise<void> {
    const response = await fetch(`${API_BASE}/memory/${memoryId}`, {
      method: 'DELETE',
    })
    if (!response.ok) {
      throw new Error(`Failed to delete memory: ${response.status}`)
    }
  }

  // Cache stats APIs
  async getCacheStats(): Promise<{
    cache_hits: number
    cache_misses: number
    hit_rate: number
    tokens_saved: number
    cost_saved: number
  }> {
    const response = await fetch(`${API_BASE}/usage/cache-stats`)
    if (!response.ok) {
      throw new Error(`Failed to get cache stats: ${response.status}`)
    }
    return response.json()
  }

  async getConversationUsage(conversationId: string): Promise<{
    conversation_id: string
    total_tokens: number
    input_tokens: number
    output_tokens: number
    cache_read_tokens: number
    cache_write_tokens: number
    estimated_cost: number
    cache_hits: number
    cache_misses: number
    hit_rate: number
    tokens_saved: number
    cost_saved: number
  }> {
    const response = await fetch(`${API_BASE}/usage/conversations/${conversationId}`)
    if (!response.ok) {
      throw new Error(`Failed to get conversation usage: ${response.status}`)
    }
    return response.json()
  }

  // Usage dashboard APIs
  async getDailyUsage(): Promise<{
    date: string
    total_tokens: number
    input_tokens: number
    output_tokens: number
    cache_read_tokens: number
    cache_write_tokens: number
    conversations: number
    messages: number
    estimated_cost: number
  }> {
    const response = await fetch(`${API_BASE}/usage/daily`)
    if (!response.ok) {
      throw new Error(`Failed to get daily usage: ${response.status}`)
    }
    return response.json()
  }

  async getMonthlyUsage(): Promise<{
    month: string
    total_tokens: number
    input_tokens: number
    output_tokens: number
    cache_read_tokens: number
    cache_write_tokens: number
    conversations: number
    messages: number
    estimated_cost: number
    daily_breakdown: any[]
  }> {
    const response = await fetch(`${API_BASE}/usage/monthly`)
    if (!response.ok) {
      throw new Error(`Failed to get monthly usage: ${response.status}`)
    }
    return response.json()
  }

  async getUsageByModel(): Promise<Array<{
    model: string
    total_tokens: number
    input_tokens: number
    output_tokens: number
    messages: number
    estimated_cost: number
  }>> {
    const response = await fetch(`${API_BASE}/usage/by-model`)
    if (!response.ok) {
      throw new Error(`Failed to get usage by model: ${response.status}`)
    }
    return response.json()
  }

  // Sharing APIs
  async createShareLink(conversationId: string, data: {
    access_level?: 'read' | 'comment' | 'edit'
    allow_comments?: boolean
    expires_in_days?: number
  }): Promise<{
    id: string
    conversation_id: string
    share_token: string
    access_level: string
    allow_comments: boolean
    is_public: boolean
    created_at: string
    expires_at: string | null
    view_count: number
  }> {
    const response = await fetch(`${API_BASE}/conversations/${conversationId}/share`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })
    if (!response.ok) {
      throw new Error(`Failed to create share link: ${response.status}`)
    }
    return response.json()
  }

  async getSharedConversation(shareToken: string): Promise<{
    id: string
    title: string
    model: string
    messages: Array<{
      id: string
      role: string
      content: string
      created_at: string
    }>
    access_level: string
    allow_comments: boolean
  }> {
    const response = await fetch(`${API_BASE}/conversations/share/${shareToken}`)
    if (!response.ok) {
      throw new Error(`Failed to get shared conversation: ${response.status}`)
    }
    return response.json()
  }

  async listShares(conversationId: string): Promise<Array<{
    id: string
    share_token: string
    conversation_id: string
    access_level: string
    allow_comments: boolean
    is_public: boolean
    created_at: string
    expires_at: string | null
    view_count: number
    last_viewed_at: string | null
  }>> {
    const response = await fetch(`${API_BASE}/conversations/${conversationId}/shares`)
    if (!response.ok) {
      throw new Error(`Failed to list shares: ${response.status}`)
    }
    return response.json()
  }

  async revokeShareLink(shareToken: string): Promise<void> {
    const response = await fetch(`${API_BASE}/conversations/share/${shareToken}`, {
      method: 'DELETE',
    })
    if (!response.ok) {
      throw new Error(`Failed to revoke share link: ${response.status}`)
    }
  }

  async revokeAllShares(conversationId: string): Promise<void> {
    const response = await fetch(`${API_BASE}/conversations/${conversationId}/shares`, {
      method: 'DELETE',
    })
    if (!response.ok) {
      throw new Error(`Failed to revoke all shares: ${response.status}`)
    }
  }

  // Prompt Library APIs
  async listPrompts(category?: string, activeOnly: boolean = true): Promise<any[]> {
    const params = new URLSearchParams()
    if (category) params.append('category', category)
    if (activeOnly) params.append('active_only', 'true')
    const response = await fetch(`${API_BASE}/prompts?${params}`)
    return response.json()
  }

  async searchPrompts(query: string): Promise<any[]> {
    const response = await fetch(`${API_BASE}/prompts/search?q=${encodeURIComponent(query)}`)
    return response.json()
  }

  async getPrompt(promptId: string): Promise<any> {
    const response = await fetch(`${API_BASE}/prompts/${promptId}`)
    if (!response.ok) {
      throw new Error(`Failed to get prompt: ${response.status}`)
    }
    return response.json()
  }

  async createPrompt(data: {
    title: string
    content: string
    category?: string
    description?: string
    tags?: string[]
  }): Promise<any> {
    const response = await fetch(`${API_BASE}/prompts`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })
    if (!response.ok) {
      throw new Error(`Failed to create prompt: ${response.status}`)
    }
    return response.json()
  }

  async updatePrompt(
    promptId: string,
    data: {
      title?: string
      content?: string
      category?: string
      description?: string
      tags?: string[]
      is_active?: boolean
    }
  ): Promise<any> {
    const response = await fetch(`${API_BASE}/prompts/${promptId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })
    if (!response.ok) {
      throw new Error(`Failed to update prompt: ${response.status}`)
    }
    return response.json()
  }

  async deletePrompt(promptId: string): Promise<void> {
    const response = await fetch(`${API_BASE}/prompts/${promptId}`, {
      method: 'DELETE',
    })
    if (!response.ok) {
      throw new Error(`Failed to delete prompt: ${response.status}`)
    }
  }

  async usePrompt(promptId: string): Promise<any> {
    const response = await fetch(`${API_BASE}/prompts/${promptId}/use`, {
      method: 'POST',
    })
    if (!response.ok) {
      throw new Error(`Failed to mark prompt as used: ${response.status}`)
    }
    return response.json()
  }

  async listPromptCategories(): Promise<string[]> {
    const response = await fetch(`${API_BASE}/prompts/categories/list`)
    return response.json()
  }

  // MCP Server APIs
  async listMCPServers(activeOnly: boolean = false): Promise<any[]> {
    const response = await fetch(`${API_BASE}/mcp?active_only=${activeOnly}`)
    if (!response.ok) {
      throw new Error(`Failed to list MCP servers: ${response.status}`)
    }
    return response.json()
  }

  async createMCPServer(data: {
    name: string
    server_type: string
    config: Record<string, any>
    description?: string
  }): Promise<any> {
    const response = await fetch(`${API_BASE}/mcp`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })
    if (!response.ok) {
      throw new Error(`Failed to create MCP server: ${response.status}`)
    }
    return response.json()
  }

  async getMCPServer(serverId: string): Promise<any> {
    const response = await fetch(`${API_BASE}/mcp/${serverId}`)
    if (!response.ok) {
      throw new Error(`Failed to get MCP server: ${response.status}`)
    }
    return response.json()
  }

  async updateMCPServer(
    serverId: string,
    data: {
      name?: string
      config?: Record<string, any>
      description?: string
      is_active?: boolean
    }
  ): Promise<any> {
    const response = await fetch(`${API_BASE}/mcp/${serverId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })
    if (!response.ok) {
      throw new Error(`Failed to update MCP server: ${response.status}`)
    }
    return response.json()
  }

  async deleteMCPServer(serverId: string): Promise<void> {
    const response = await fetch(`${API_BASE}/mcp/${serverId}`, {
      method: 'DELETE',
    })
    if (!response.ok) {
      throw new Error(`Failed to delete MCP server: ${response.status}`)
    }
  }

  async testMCPServer(serverId: string): Promise<any> {
    const response = await fetch(`${API_BASE}/mcp/${serverId}/test`, {
      method: 'POST',
    })
    if (!response.ok) {
      throw new Error(`Failed to test MCP server: ${response.status}`)
    }
    return response.json()
  }

  async testMCPConnection(serverType: string, config: Record<string, any>): Promise<any> {
    const response = await fetch(`${API_BASE}/mcp/test-connection`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ server_type: serverType, config }),
    })
    if (!response.ok) {
      throw new Error(`Failed to test MCP connection: ${response.status}`)
    }
    return response.json()
  }

  async listMCPServerTypes(): Promise<any[]> {
    const response = await fetch(`${API_BASE}/mcp/types/list`)
    if (!response.ok) {
      throw new Error(`Failed to list MCP server types: ${response.status}`)
    }
    return response.json()
  }

  // API Key Management APIs
  async validateAPIKey(apiKey: string): Promise<{ valid: boolean; message: string; key_preview: string }> {
    const response = await fetch(`${API_BASE}/settings/api-key/validate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ api_key: apiKey }),
    })
    if (!response.ok) {
      throw new Error(`Failed to validate API key: ${response.status}`)
    }
    return response.json()
  }

  async saveAPIKey(apiKey: string): Promise<{ message: string; key_preview: string }> {
    const response = await fetch(`${API_BASE}/settings/api-key/save`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ api_key: apiKey }),
    })
    if (!response.ok) {
      throw new Error(`Failed to save API key: ${response.status}`)
    }
    return response.json()
  }

  async getAPIKeyStatus(): Promise<{ configured: boolean; has_saved_key: boolean; key_preview: string; message: string }> {
    const response = await fetch(`${API_BASE}/settings/api-key/status`)
    if (!response.ok) {
      throw new Error(`Failed to get API key status: ${response.status}`)
    }
    return response.json()
  }

  async removeAPIKey(): Promise<{ message: string }> {
    const response = await fetch(`${API_BASE}/settings/api-key`, {
      method: 'DELETE',
    })
    if (!response.ok) {
      throw new Error(`Failed to remove API key: ${response.status}`)
    }
    return response.json()
  }

  // Session Management APIs
  async refreshSession(): Promise<{
    status: string
    message: string
    timestamp: number
    session_active: boolean
  }> {
    const response = await fetch(`${API_BASE}/settings/refresh-session`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    })
    if (!response.ok) {
      throw new Error(`Failed to refresh session: ${response.status}`)
    }
    return response.json()
  }

  async getSessionStatus(): Promise<{
    session_active: boolean
    last_activity: number
    timeout_minutes: number
    settings: {
      timeout_duration: number
      warning_duration: number
    }
  }> {
    const response = await fetch(`${API_BASE}/settings/session-status`)
    if (!response.ok) {
      throw new Error(`Failed to get session status: ${response.status}`)
    }
    return response.json()
  }

  // Auth APIs
  async login(username: string, password: string): Promise<{
    access_token: string
    refresh_token: string
    token_type: string
    username: string
    expires_in: number
    session_id: string
  }> {
    const formData = new FormData()
    formData.append('username', username)
    formData.append('password', password)

    const response = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      body: formData,
    })

    if (!response.ok) {
      throw new Error(`Login failed: ${response.status}`)
    }

    const data = await response.json()
    // Store tokens in localStorage
    localStorage.setItem('access_token', data.access_token)
    if (data.refresh_token) {
      localStorage.setItem('refresh_token', data.refresh_token)
    }
    if (data.session_id) {
      localStorage.setItem('session_id', data.session_id)
    }
    return data
  }

  async refreshToken(refreshToken?: string): Promise<{
    access_token: string
    token_type: string
    expires_in: number
  }> {
    // Use provided refresh token or get from localStorage
    const token = refreshToken || localStorage.getItem('refresh_token')

    const response = await fetch(`${API_BASE}/auth/refresh`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ refresh_token: token }),
    })

    if (!response.ok) {
      throw new Error(`Token refresh failed: ${response.status}`)
    }

    const data = await response.json()
    // Update token in localStorage
    localStorage.setItem('access_token', data.access_token)
    return data
  }

  async logout(): Promise<void> {
    const token = localStorage.getItem('access_token')
    if (token) {
      try {
        await fetch(`${API_BASE}/auth/logout`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        })
      } catch (e) {
        // Ignore errors on logout
      }
    }
    // Clear tokens from localStorage
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('session_id')
  }

  async getSessionInfo(): Promise<{
    username: string
    session_id: string
    session_info: any
  }> {
    const token = localStorage.getItem('access_token')
    if (!token) {
      throw new Error('No access token found')
    }

    const response = await fetch(`${API_BASE}/auth/session-info`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    })

    if (!response.ok) {
      throw new Error(`Failed to get session info: ${response.status}`)
    }

    return response.json()
  }

  async checkSessionStatus(): Promise<{
    is_active: boolean
    is_expired: boolean
    remaining_seconds: number
    remaining_minutes: number
    expires_at: number
  }> {
    const token = localStorage.getItem('access_token')
    if (!token) {
      throw new Error('No access token found')
    }

    const response = await fetch(`${API_BASE}/auth/session/status`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    })

    if (!response.ok) {
      throw new Error(`Failed to check session status: ${response.status}`)
    }

    return response.json()
  }

  async keepSessionAlive(): Promise<{
    message: string
    session_info: any
  }> {
    const token = localStorage.getItem('access_token')
    if (!token) {
      throw new Error('No access token found')
    }

    const response = await fetch(`${API_BASE}/auth/session/keep-alive`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    })

    if (!response.ok) {
      throw new Error(`Failed to keep session alive: ${response.status}`)
    }

    return response.json()
  }

  getAccessToken(): string | null {
    return localStorage.getItem('access_token')
  }

  getRefreshToken(): string | null {
    return localStorage.getItem('refresh_token')
  }

  setAccessToken(token: string): void {
    localStorage.setItem('access_token', token)
  }

  setRefreshToken(token: string): void {
    localStorage.setItem('refresh_token', token)
  }

  clearAccessToken(): void {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('session_id')
  }

  // Data Export & Account Management APIs

  /**
   * Export all user data including conversations, messages, settings, memories, etc.
   * Returns a JSON file download.
   */
  async exportAllUserData(): Promise<Blob> {
    const response = await fetch(`${API_BASE}/settings/export-all`)
    if (!response.ok) {
      throw new Error(`Failed to export data: ${response.status}`)
    }
    return response.blob()
  }

  /**
   * Delete user account and all associated data.
   * Requires confirmation string "DELETE_ACCOUNT".
   */
  async deleteAccount(confirm: string): Promise<{
    status: string
    message: string
    deleted_items: Record<string, number>
    total_deleted: number
  }> {
    const response = await fetch(`${API_BASE}/settings/account?confirm=${encodeURIComponent(confirm)}`, {
      method: 'DELETE',
    })
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }))
      throw new Error(error.detail || `Failed to delete account: ${response.status}`)
    }
    return response.json()
  }

  // Tag APIs
  async listTags(): Promise<Tag[]> {
    const response = await fetch(`${API_BASE}/tags`)
    if (!response.ok) {
      throw new Error(`Failed to list tags: ${response.status}`)
    }
    return response.json()
  }

  async createTag(data: { name: string; color?: string }): Promise<Tag> {
    const response = await fetch(`${API_BASE}/tags`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }))
      throw new Error(error.detail || `Failed to create tag: ${response.status}`)
    }
    return response.json()
  }

  async updateTag(tagId: string, data: { name?: string; color?: string }): Promise<Tag> {
    const response = await fetch(`${API_BASE}/tags/${tagId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }))
      throw new Error(error.detail || `Failed to update tag: ${response.status}`)
    }
    return response.json()
  }

  async deleteTag(tagId: string): Promise<void> {
    const response = await fetch(`${API_BASE}/tags/${tagId}`, {
      method: 'DELETE',
    })
    if (!response.ok) {
      throw new Error(`Failed to delete tag: ${response.status}`)
    }
  }

  async updateConversationTags(conversationId: string, tagIds: string[]): Promise<{ conversation_id: string; tag_ids: string[]; tags: Tag[] }> {
    const response = await fetch(`${API_BASE}/tags/conversations/${conversationId}/tags`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ tag_ids: tagIds }),
    })
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }))
      throw new Error(error.detail || `Failed to update conversation tags: ${response.status}`)
    }
    return response.json()
  }

  async filterConversationsByTags(tagIds: string[]): Promise<Conversation[]> {
    const response = await fetch(`${API_BASE}/tags/conversations/filter/by-tags?tag_ids=${encodeURIComponent(tagIds.join(','))}`)
    if (!response.ok) {
      throw new Error(`Failed to filter conversations by tags: ${response.status}`)
    }
    return response.json()
  }

  // Comment APIs for shared conversations
  async createComment(shareToken: string, data: {
    message_id: string
    content: string
    parent_comment_id?: string
    anonymous_name?: string
  }): Promise<{
    id: string
    message_id: string
    conversation_id: string
    user_id: string | null
    anonymous_name: string | null
    content: string
    parent_comment_id: string | null
    created_at: string
    updated_at: string | null
    replies: any[]
  }> {
    const response = await fetch(`${API_BASE}/comments/shared/${shareToken}/comments`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }))
      throw new Error(error.detail || `Failed to create comment: ${response.status}`)
    }
    return response.json()
  }

  async getComments(shareToken: string, messageId?: string): Promise<Array<{
    id: string
    message_id: string
    conversation_id: string
    user_id: string | null
    anonymous_name: string | null
    content: string
    parent_comment_id: string | null
    created_at: string
    updated_at: string | null
    replies: any[]
  }>> {
    const url = messageId
      ? `${API_BASE}/comments/shared/${shareToken}/comments?message_id=${messageId}`
      : `${API_BASE}/comments/shared/${shareToken}/comments`
    const response = await fetch(url)
    if (!response.ok) {
      throw new Error(`Failed to get comments: ${response.status}`)
    }
    return response.json()
  }

  async updateComment(shareToken: string, commentId: string, content: string): Promise<{
    id: string
    message_id: string
    conversation_id: string
    user_id: string | null
    anonymous_name: string | null
    content: string
    parent_comment_id: string | null
    created_at: string
    updated_at: string | null
    replies: any[]
  }> {
    const response = await fetch(`${API_BASE}/comments/shared/${shareToken}/comments/${commentId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content }),
    })
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }))
      throw new Error(error.detail || `Failed to update comment: ${response.status}`)
    }
    return response.json()
  }

  async deleteComment(shareToken: string, commentId: string): Promise<void> {
    const response = await fetch(`${API_BASE}/comments/shared/${shareToken}/comments/${commentId}`, {
      method: 'DELETE',
    })
    if (!response.ok) {
      throw new Error(`Failed to delete comment: ${response.status}`)
    }
  }

  // Saved Searches APIs
  async listSavedSearches(searchType?: string): Promise<Array<{
    id: string
    user_id: string
    name: string
    query: string
    filters: Record<string, any>
    search_type: string
    description: string | null
    is_active: boolean
    usage_count: number
    display_order: number
    created_at: string
    updated_at: string
    last_used_at: string | null
  }>> {
    const url = searchType
      ? `${API_BASE}/saved-searches?search_type=${searchType}`
      : `${API_BASE}/saved-searches`
    const response = await fetch(url)
    if (!response.ok) {
      throw new Error(`Failed to list saved searches: ${response.status}`)
    }
    return response.json()
  }

  async createSavedSearch(data: {
    name: string
    query: string
    filters?: Record<string, any>
    search_type?: string
    description?: string
  }): Promise<any> {
    const response = await fetch(`${API_BASE}/saved-searches`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })
    if (!response.ok) {
      throw new Error(`Failed to create saved search: ${response.status}`)
    }
    return response.json()
  }

  async getSavedSearch(searchId: string): Promise<any> {
    const response = await fetch(`${API_BASE}/saved-searches/${searchId}`)
    if (!response.ok) {
      throw new Error(`Failed to get saved search: ${response.status}`)
    }
    return response.json()
  }

  async updateSavedSearch(searchId: string, data: {
    name?: string
    query?: string
    filters?: Record<string, any>
    search_type?: string
    description?: string
    display_order?: number
  }): Promise<any> {
    const response = await fetch(`${API_BASE}/saved-searches/${searchId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })
    if (!response.ok) {
      throw new Error(`Failed to update saved search: ${response.status}`)
    }
    return response.json()
  }

  async deleteSavedSearch(searchId: string): Promise<void> {
    const response = await fetch(`${API_BASE}/saved-searches/${searchId}`, {
      method: 'DELETE',
    })
    if (!response.ok) {
      throw new Error(`Failed to delete saved search: ${response.status}`)
    }
  }

  async runSavedSearch(searchId: string): Promise<{
    search_id: string
    query: string
    filters: Record<string, any>
    search_type: string
    name: string
  }> {
    const response = await fetch(`${API_BASE}/saved-searches/${searchId}/run`, {
      method: 'POST',
    })
    if (!response.ok) {
      throw new Error(`Failed to run saved search: ${response.status}`)
    }
    return response.json()
  }

  async reorderSavedSearch(searchId: string, newOrder: number): Promise<{ message: string; new_order: number }> {
    const response = await fetch(`${API_BASE}/saved-searches/${searchId}/reorder`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ new_order: newOrder }),
    })
    if (!response.ok) {
      throw new Error(`Failed to reorder saved search: ${response.status}`)
    }
    return response.json()
  }

  // Activity Feed APIs
  async logActivity(data: {
    action_type: string
    resource_type?: string
    resource_id?: string
    resource_name?: string
    details?: Record<string, any>
    user_id?: string
    user_name?: string
  }): Promise<{ id: string }> {
    const params = new URLSearchParams()
    if (data.user_id) params.append('user_id', data.user_id)
    if (data.user_name) params.append('user_name', data.user_name)

    const response = await fetch(`${API_BASE}/activity?${params.toString()}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        action_type: data.action_type,
        resource_type: data.resource_type,
        resource_id: data.resource_id,
        resource_name: data.resource_name,
        details: data.details,
      }),
    })
    if (!response.ok) {
      throw new Error(`Failed to log activity: ${response.status}`)
    }
    return response.json()
  }

  async getActivities(filters?: {
    action_type?: string
    resource_type?: string
    user_id?: string
    time_range?: string
    limit?: number
    offset?: number
  }): Promise<{
    activities: Array<{
      id: string
      user_id: string
      user_name: string
      action_type: string
      resource_type?: string
      resource_id?: string
      resource_name?: string
      details?: any
      created_at: string
    }>
    total: number
    has_more: boolean
  }> {
    const params = new URLSearchParams()
    if (filters?.action_type) params.append('action_type', filters.action_type)
    if (filters?.resource_type) params.append('resource_type', filters.resource_type)
    if (filters?.user_id) params.append('user_id', filters.user_id)
    if (filters?.time_range) params.append('time_range', filters.time_range)
    if (filters?.limit) params.append('limit', filters.limit.toString())
    if (filters?.offset) params.append('offset', filters.offset.toString())

    const url = `${API_BASE}/activity${params.toString() ? '?' + params.toString() : ''}`
    const response = await fetch(url)
    if (!response.ok) {
      throw new Error(`Failed to fetch activities: ${response.status}`)
    }
    return response.json()
  }

  async getActivityTypes(): Promise<{
    action_types: Array<{ type: string; count: number }>
    resource_types: Array<{ type: string; count: number }>
  }> {
    const response = await fetch(`${API_BASE}/activity/types`)
    if (!response.ok) {
      throw new Error(`Failed to fetch activity types: ${response.status}`)
    }
    return response.json()
  }

  async getActivitySummary(days: number = 7): Promise<{
    total: number
    by_user: Record<string, number>
    by_type: Record<string, number>
    by_resource: Record<string, number>
  }> {
    const response = await fetch(`${API_BASE}/activity/summary?days=${days}`)
    if (!response.ok) {
      throw new Error(`Failed to fetch activity summary: ${response.status}`)
    }
    return response.json()
  }

  async deleteActivity(activityId: string): Promise<void> {
    const response = await fetch(`${API_BASE}/activity/${activityId}`, {
      method: 'DELETE',
    })
    if (!response.ok) {
      throw new Error(`Failed to delete activity: ${response.status}`)
    }
  }
}

export const api = new APIService()
