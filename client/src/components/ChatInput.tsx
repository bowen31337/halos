import { useState, useRef, useEffect } from 'react'
import { useConversationStore } from '../stores/conversationStore'
import { api } from '../services/api'
import { v4 as uuidv4 } from 'uuid'

export function ChatInput() {
  const [inputValue, setInputValue] = useState('')
  const { isStreaming, isLoading, addMessage, appendToLastMessage, setStreaming, setLoading, currentConversationId, createConversation } = useConversationStore()
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const abortControllerRef = useRef<AbortController | null>(null)

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 200) + 'px'
    }
  }, [inputValue])

  const handleSend = async () => {
    // If streaming, this is a stop request
    if (isStreaming) {
      abortControllerRef.current?.abort()
      setStreaming(false)
      setLoading(false)
      return
    }

    if (!inputValue.trim() || isLoading) return

    const convId = currentConversationId || 'default'
    const userMessage = {
      id: uuidv4(),
      conversationId: convId,
      role: 'user' as const,
      content: inputValue,
      createdAt: new Date().toISOString(),
    }

    addMessage(userMessage)
    const messageToSend = inputValue
    setInputValue('')
    setLoading(true)
    setStreaming(true)

    // Create assistant message placeholder for streaming
    const assistantMessageId = uuidv4()
    const assistantMessage = {
      id: assistantMessageId,
      conversationId: convId,
      role: 'assistant' as const,
      content: '',
      createdAt: new Date().toISOString(),
      isStreaming: true,
    }
    addMessage(assistantMessage)

    // Create abort controller for cancellation
    const abortController = new AbortController()
    abortControllerRef.current = abortController

    try {
      // Call the backend SSE API with conversation ID
      const response = await fetch('/api/agent/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: messageToSend,
          conversationId: convId,
          thread_id: convId
        }),
        signal: abortController.signal,
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const reader = response.body?.getReader()
      if (!reader) {
        throw new Error('No response body')
      }

      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || '' // Keep incomplete line in buffer

        // SSE events can span multiple lines: event: X \n data: Y \n\n
        // We need to buffer event and data lines together
        let currentEvent: string | null = null
        let currentData: string | null = null

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
                    if (eventData.content) {
                      appendToLastMessage(eventData.content)
                    }
                    break
                  case 'tool_start':
                    console.log('Tool started:', eventData.tool, eventData.input)
                    break
                  case 'tool_end':
                    console.log('Tool ended:', eventData.output)
                    break
                  case 'done':
                    console.log('Stream completed')
                    break
                  case 'error':
                    console.error('Stream error:', eventData.error)
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
                if (eventData.content) {
                  appendToLastMessage(eventData.content)
                }
              } catch (e) {
                console.warn('Failed to parse SSE data:', e)
              }
              currentData = null
            }
          }
        }
      }

      // Mark message as no longer streaming
      const { messages } = useConversationStore.getState()
      const currentIndex = messages.findIndex(m => m.id === assistantMessageId)
      if (currentIndex >= 0) {
        const updatedMessages = [...messages]
        updatedMessages[currentIndex] = { ...updatedMessages[currentIndex], isStreaming: false }
        useConversationStore.setState({ messages: updatedMessages })
      }

    } catch (error: unknown) {
      if (error instanceof Error && error.name === 'AbortError') {
        console.log('Request cancelled by user')
      } else {
        console.error('Error sending message:', error)
        // Add error message
        addMessage({
          id: uuidv4(),
          conversationId: convId,
          role: 'assistant',
          content: `Error: ${error instanceof Error ? error.message : String(error)}. The backend may not be running or API key not configured.`,
          createdAt: new Date().toISOString(),
        })
      }
    } finally {
      setLoading(false)
      setStreaming(false)
      abortControllerRef.current = null
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="max-w-3xl mx-auto p-4">
      <div className="flex items-end gap-3">
        <div className="flex-1 relative">
          <textarea
            ref={textareaRef}
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type your message..."
            disabled={isLoading || isStreaming}
            className="w-full resize-none border border-[var(--border-primary)] rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-[var(--primary)] bg-[var(--bg-primary)] text-[var(--text-primary)] disabled:opacity-50 min-h-[60px] max-h-[200px]"
            rows={1}
          />
        </div>
        <button
          onClick={handleSend}
          disabled={!inputValue.trim() && !isStreaming}
          className="px-6 py-3 bg-[var(--primary)] hover:bg-[var(--primary-hover)] text-white rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isStreaming ? 'Stop' : 'Send'}
        </button>
      </div>
      <div className="flex justify-between mt-2 text-xs text-[var(--text-secondary)]">
        <span>{inputValue.length} characters</span>
        <span>Enter to send, Shift+Enter for newline</span>
      </div>
    </div>
  )
}
