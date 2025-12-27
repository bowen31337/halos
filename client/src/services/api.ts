/**
 * API Service for backend communication
 */

import { Conversation, Message } from '@/stores/conversationStore'

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

  // Message APIs
  async listMessages(conversationId: string): Promise<Message[]> {
    const response = await fetch(`${API_BASE}/conversations/${conversationId}/messages`)
    return response.json()
  }

  async createMessage(
    conversationId: string,
    data: { content: string; role: 'user' | 'assistant' }
  ): Promise<Message> {
    const response = await fetch(`${API_BASE}/conversations/${conversationId}/messages`, {
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
      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || '' // Keep incomplete line in buffer

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const dataStr = line.slice(6)
            if (!dataStr) continue

            try {
              // Handle SSE format: event: name\ndata: {...}
              // The line might be just data or have event prefix
              const eventMatch = line.match(/^event:\s*(\w+)/)
              const dataMatch = line.match(/data:\s*(.+)/)

              if (eventMatch && dataMatch) {
                const event = eventMatch[1]
                const eventData = JSON.parse(dataMatch[1])

                switch (event) {
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
                }
              } else if (dataMatch) {
                // Handle just data line
                const eventData = JSON.parse(dataMatch[1])
                if (eventData.content) onMessage(eventData.content)
              }
            } catch (e) {
              console.warn('Failed to parse SSE data:', e)
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
