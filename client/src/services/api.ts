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
}

export interface AgentResponse {
  threadId: string
  response: string
  model: string
  status: string
}

export interface SSEEvent {
  event: 'start' | 'message' | 'tool_start' | 'tool_end' | 'done' | 'error'
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

  // Message APIs
  async listMessages(conversationId: string): Promise<Message[]> {
    const response = await fetch(`${API_BASE}/messages/conversations/${conversationId}/messages`)
    return response.json()
  }

  async createMessage(
    conversationId: string,
    data: { content: string; role: 'user' | 'assistant'; attachments?: string[] }
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
    onDone?: () => void,
    onError?: (error: string) => void
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
                  case 'tool_start':
                    onToolStart?.(eventData.tool, eventData.input)
                    break
                  case 'tool_end':
                    onToolEnd?.(eventData.output)
                    break
                  case 'done':
                    onDone?.()
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
}

export const api = new APIService()
