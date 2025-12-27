import { useConversationStore } from '../stores/conversationStore'
import { MessageBubble } from './MessageBubble'
import { ThinkingIndicator } from './ThinkingIndicator'
import { VariableSizeList as List } from 'react-window'
import { useRef, useCallback, useEffect, useState } from 'react'
import type { Message } from '../stores/conversationStore'

// Default height for messages before measurement
const DEFAULT_ROW_HEIGHT = 150
// Maximum height cap to prevent extreme cases
const MAX_ROW_HEIGHT = 800
// Threshold for switching to virtualized mode
const VIRTUALIZATION_THRESHOLD = 15

interface RowProps {
  index: number
  style: React.CSSProperties
  data: {
    messages: Message[]
    onRegenerate: (messageId: string) => void
    onEdit: (messageId: string, content: string) => void
    measureRef: (index: number, element: HTMLElement | null) => void
    isStreaming: boolean
    isLastMessageThinking: boolean
  }
}

function Row({ index, style, data }: RowProps) {
  const { messages, onRegenerate, onEdit, measureRef, isStreaming, isLastMessageThinking } = data

  // Last index is for thinking indicator
  if (index === messages.length) {
    return (
      <div style={style}>
        <div className="max-w-3xl mx-auto px-4 py-2">
          <ThinkingIndicator />
        </div>
      </div>
    )
  }

  const message = messages[index]

  return (
    <div style={style} ref={(el) => measureRef(index, el)}>
      <div className="max-w-3xl mx-auto px-4">
        <MessageBubble
          message={message}
          onRegenerate={onRegenerate}
          onEdit={onEdit}
        />
      </div>
    </div>
  )
}

export function MessageList() {
  const { messages, isStreaming, regenerateLastResponse, editAndResend } = useConversationStore()
  const listRef = useRef<List>(null)
  const sizeMap = useRef<Record<number, number>>({})
  const [listHeight, setListHeight] = useState(0)
  const [isClient, setIsClient] = useState(false)

  // Check if the last message is thinking
  const lastMessage = messages[messages.length - 1]
  const isLastMessageThinking = lastMessage?.role === 'assistant' && lastMessage?.isThinking

  // Set client flag on mount
  useEffect(() => {
    setIsClient(true)
  }, [])

  // Calculate the list container height dynamically
  useEffect(() => {
    if (!isClient) return

    const updateHeight = () => {
      // Subtract header/input area estimates
      const availableHeight = window.innerHeight - 250
      setListHeight(Math.max(300, availableHeight))
    }

    updateHeight()
    window.addEventListener('resize', updateHeight)
    return () => window.removeEventListener('resize', updateHeight)
  }, [isClient])

  // Function to measure and set row size dynamically
  const setRowHeight = useCallback((index: number, element: HTMLElement | null) => {
    if (element) {
      const height = element.getBoundingClientRect().height
      // Only update if height changed significantly (prevents infinite re-renders)
      if (sizeMap.current[index] !== height && height > 0 && height < MAX_ROW_HEIGHT) {
        sizeMap.current[index] = height
        // Force list to recompute sizes
        listRef.current?.resetAfterIndex(index)
      }
    }
  }, [])

  // Get size for a row - returns measured height or default
  const getRowSize = useCallback((index: number) => {
    // Last item (thinking indicator)
    if (index === messages.length) {
      return 60
    }
    return sizeMap.current[index] || DEFAULT_ROW_HEIGHT
  }, [messages.length])

  // Scroll to bottom when new messages arrive
  useEffect(() => {
    if (messages.length > 0 && listRef.current) {
      setTimeout(() => {
        listRef.current?.scrollToItem(messages.length - 1, 'end')
      }, 100)
    }
  }, [messages.length])

  // For small message lists, use regular rendering for better performance
  if (messages.length < VIRTUALIZATION_THRESHOLD) {
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
        {(isStreaming || isLastMessageThinking) && (
          <div className="py-4 flex justify-center">
            <ThinkingIndicator />
          </div>
        )}
      </div>
    )
  }

  // Use virtualized list for large conversations
  const itemCount = isStreaming || isLastMessageThinking ? messages.length + 1 : messages.length

  return (
    <div className="max-w-3xl mx-auto px-4 flex flex-col h-full overflow-hidden">
      <div className="flex-1" style={{ height: listHeight || 600 }}>
        <List
          ref={listRef}
          height={listHeight || 600}
          itemCount={itemCount}
          itemSize={getRowSize}
          itemData={{
            messages,
            onRegenerate: regenerateLastResponse,
            onEdit: editAndResend,
            measureRef: setRowHeight,
            isStreaming,
            isLastMessageThinking,
          }}
          width="100%"
          overscanCount={5} // Pre-render 5 items above/below viewport
        >
          {Row}
        </List>
      </div>
    </div>
  )
}
