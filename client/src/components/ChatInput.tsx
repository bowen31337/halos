import { useState, useRef, useEffect } from 'react'
import { useConversationStore } from '../stores/conversationStore'
import { v4 as uuidv4 } from 'uuid'

export function ChatInput() {
  const [inputValue, setInputValue] = useState('')
  const { isStreaming, isLoading, addMessage, appendToLastMessage, setStreaming, setLoading } = useConversationStore()
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 200) + 'px'
    }
  }, [inputValue])

  const handleSend = async () => {
    if (!inputValue.trim() || isLoading || isStreaming) return

    const userMessage = {
      id: uuidv4(),
      conversationId: 'default',
      role: 'user' as const,
      content: inputValue,
      createdAt: new Date().toISOString(),
    }

    addMessage(userMessage)
    const messageToSend = inputValue
    setInputValue('')
    setLoading(true)
    setStreaming(true)

    try {
      // Call the backend API
      const response = await fetch('http://localhost:8000/api/agent/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: messageToSend }),
      })

      if (!response.ok) throw new Error('Failed to connect to agent')

      // For now, simulate a response
      setTimeout(() => {
        addMessage({
          id: uuidv4(),
          conversationId: 'default',
          role: 'assistant',
          content: `I received your message: "${messageToSend}"\n\nThis is a placeholder response. The backend integration is still being implemented.`,
          createdAt: new Date().toISOString(),
        })
        setLoading(false)
        setStreaming(false)
      }, 1000)

    } catch (error) {
      console.error('Error sending message:', error)
      setLoading(false)
      setStreaming(false)
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
          disabled={!inputValue.trim() || isLoading || isStreaming}
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
