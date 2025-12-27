import { useEffect, useState } from 'react'
import { useConversationStore } from '../stores/conversationStore'

export function TokenUsageDisplay() {
  const { messages } = useConversationStore()
  const [totalTokens, setTotalTokens] = useState(0)

  useEffect(() => {
    // Calculate total tokens from all messages
    const total = messages.reduce((sum, message) => {
      return sum + (message.input_tokens || 0) + (message.output_tokens || 0)
    }, 0)
    setTotalTokens(total)
  }, [messages])

  // Don't show if no messages
  if (messages.length === 0) {
    return null
  }

  return (
    <div className="fixed bottom-4 left-4 bg-[var(--bg-primary)] border border-[var(--border-primary)] rounded-lg p-3 shadow-lg z-50">
      <div className="text-sm font-medium text-[var(--text-primary)] mb-2">Token Usage</div>

      <div className="space-y-1 text-xs text-[var(--text-secondary)]">
        <div className="flex justify-between">
          <span>Total tokens:</span>
          <span className="font-medium text-[var(--text-primary)]">{totalTokens.toLocaleString()}</span>
        </div>

        <div className="flex justify-between">
          <span>Messages:</span>
          <span className="font-medium text-[var(--text-primary)]">{messages.length}</span>
        </div>

        <div className="flex justify-between">
          <span>Avg per message:</span>
          <span className="font-medium text-[var(--text-primary)]">
            {messages.length > 0 ? Math.round(totalTokens / messages.length) : 0}
          </span>
        </div>
      </div>

      {/* Breakdown by message type */}
      <div className="mt-3 space-y-1">
        {messages.slice(-3).map((message) => (
          <div key={message.id} className="flex justify-between text-xs">
            <span className={`font-medium ${
              message.role === 'user' ? 'text-blue-400' : 'text-purple-400'
            }`}>
              {message.role === 'user' ? 'User' : 'AI'}
            </span>
            <div className="flex gap-2">
              <span className="text-[var(--text-secondary)]">In:</span>
              <span className="font-medium text-[var(--text-primary)]">{message.input_tokens || 0}</span>
              <span className="text-[var(--text-secondary)]">Out:</span>
              <span className="font-medium text-[var(--text-primary)]">{message.output_tokens || 0}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}