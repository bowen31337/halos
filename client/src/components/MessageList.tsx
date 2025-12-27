import { useConversationStore } from '../stores/conversationStore'
import { MessageBubble } from './MessageBubble'
import { ThinkingIndicator } from './ThinkingIndicator'
import { VariableSizeList as List } from 'react-window'
import { useRef, useCallback, useEffect, useState } from 'react'

// Estimated heights for different message types (in pixels)
const ESTIMATED_HEIGHTS = {
  small: 80,
  medium: 150,
  large: 250,
  thinking: 60,
}

export function MessageList() {
  const { messages, isStreaming, regenerateLastResponse, editAndResend } = useConversationStore()
  const listRef = useRef<List>(null)
  const [listHeight, setListHeight] = useState(0)

  // Check if the last message is thinking
  const lastMessage = messages[messages.length - 1]
  const isLastMessageThinking = lastMessage?.role === 'assistant' && lastMessage?.isThinking

  // Calculate dynamic height for each message
  const getItemSize = useCallback((index: number) => {
    if (index >= messages.length) return ESTIMATED_HEIGHTS.thinking

    const message = messages[index]
    const contentLength = message.content?.length || 0

    // Estimate height based on content length and type
    if (message.isThinking) return ESTIMATED_HEIGHTS.thinking
    if (contentLength < 100) return ESTIMATED_HEIGHTS.small
    if (contentLength < 500) return ESTIMATED_HEIGHTS.medium
    return ESTIMATED_HEIGHTS.large
  }, [messages])

  // Update list height on mount and window resize
  useEffect(() => {
    const updateHeight = () => {
      // Calculate available height: window height - header - input area - padding
      const availableHeight = window.innerHeight - 250
      setListHeight(Math.max(availableHeight, 300))
    }

    updateHeight()
    window.addEventListener('resize', updateHeight)
    return () => window.removeEventListener('resize', updateHeight)
  }, [])

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (listRef.current && messages.length > 0) {
      // Use setTimeout to ensure DOM is updated
      setTimeout(() => {
        listRef.current?.scrollToItem(messages.length - 1, 'end')
      }, 50)
    }
  }, [messages.length])

  // Row renderer for virtualized list
  const Row = ({ index, style }: { index: number; style: React.CSSProperties }) => {
    // Handle thinking indicator at the end
    if (index === messages.length) {
      return (
        <div style={style}>
          <div className="max-w-3xl mx-auto px-4">
            <ThinkingIndicator />
          </div>
        </div>
      )
    }

    const message = messages[index]
    return (
      <div style={style}>
        <div className="max-w-3xl mx-auto px-4">
          <MessageBubble
            key={message.id}
            message={message}
            onRegenerate={regenerateLastResponse}
            onEdit={editAndResend}
          />
        </div>
      </div>
    )
  }

  // For small message lists (< 10 messages), use regular rendering for better performance
  if (messages.length < 10) {
    return (
      <div className="max-w-3xl mx-auto py-8 px-4">
        {messages.map((message) => (
          <MessageBubble
            key={message.id}
            message={message}
            onRegenerate={regenerateLastResponse}
            onEdit={editAndResend}
          />
        ))}
        {(isStreaming || isLastMessageThinking) && <ThinkingIndicator />}
      </div>
    )
  }

  // Virtualized list for large conversations
  const listSize = isStreaming || isLastMessageThinking ? messages.length + 1 : messages.length

  return (
    <div className="max-w-3xl mx-auto py-8 px-4 h-full">
      <List
        ref={listRef}
        height={listHeight || 600}
        itemCount={listSize}
        itemSize={getItemSize}
        width="100%"
        className="custom-scrollbar"
      >
        {Row}
      </List>
    </div>
  )
}
