/**
 * API Service for backend communication
 */

import type { Conversation, Message } from '@/stores/conversationStore'

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
}

export const api = new APIService()
