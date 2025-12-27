import { useConversationStore } from '../stores/conversationStore'
import { MessageBubble } from './MessageBubble'
import { ThinkingIndicator } from './ThinkingIndicator'
import { VariableSizeList as List } from 'react-window'
import { useRef, useCallback, useEffect, useState } from 'react'
import type { Message } from '../stores/conversationStore'
import { useUIStore } from '../stores/uiStore'

// Default height for messages before measurement
const DEFAULT_ROW_HEIGHT = 150
// Maximum height cap to prevent extreme cases
const MAX_ROW_HEIGHT = 800
// Threshold for switching to virtualized mode
const VIRTUALIZATION_THRESHOLD = 15


// Helper to group messages by comparison group
interface GroupedMessages {
  type: 'single' | 'comparison'
  messages: Message[]
  comparisonGroup?: string
}

function groupMessagesForDisplay(messages: Message[]): GroupedMessages[] {
  const result: GroupedMessages[] = []
  let i = 0

  while (i < messages.length) {
    const currentMsg = messages[i]

    // Check if this is part of a comparison group
    if (currentMsg.comparisonGroup) {
      const group = currentMsg.comparisonGroup
      const groupMessages: Message[] = []

      // Collect all messages with the same comparison group
      while (i < messages.length && messages[i].comparisonGroup === group) {
        groupMessages.push(messages[i])
        i++
      }

      result.push({
        type: 'comparison',
        messages: groupMessages,
        comparisonGroup: group,
      })
    } else {
      // Single message
      result.push({
        type: 'single',
        messages: [currentMsg],
      })
      i++
    }
  }

  return result
}

interface RowProps {
  index: number
  style: React.CSSProperties
  data: {
    messages: Message[]
    onRegenerate: (messageId: string) => void
    onEdit: (messageId: string, content: string) => void
    onSuggestionClick: (suggestion: string) => void
    measureRef: (index: number, element: HTMLElement | null) => void
    isStreaming: boolean
    isLastMessageThinking: boolean
  }
}

function Row({ index, style, data }: RowProps) {
  const { messages, onRegenerate, onEdit, onSuggestionClick, measureRef, isStreaming, isLastMessageThinking } = data

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
          onSuggestionClick={onSuggestionClick}
        />
      </div>
    </div>
  )
}

export function MessageList() {
  const { messages, isStreaming, regenerateLastResponse, editAndResend, setInputMessage, currentConversationId } = useConversationStore()
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

  // Handle suggestion click - dispatch event to set input and focus
  const handleSuggestionClick = useCallback((suggestion: string) => {
    // Use the same custom event as PromptModal to set input and focus
    const event = new CustomEvent('usePrompt', { detail: { content: suggestion } })
    window.dispatchEvent(event)
  }, [])

  // For small message lists, use regular rendering for better performance
  if (messages.length < VIRTUALIZATION_THRESHOLD) {
    const groupedMessages = groupMessagesForDisplay(messages)
    
    return (
      <div className="max-w-3xl mx-auto py-8 px-4">
        {groupedMessages.map((group, groupIndex) => {
          if (group.type === 'comparison') {
            // Render comparison group side-by-side
            return (
              <div key={group.comparisonGroup || groupIndex} className="mb-6">
                <div className="grid grid-cols-2 gap-4">
                  {group.messages.map((message) => (
                    <div key={message.id} className="bg-[var(--bg-secondary)] rounded-lg border border-[var(--border)] overflow-hidden">
                      <div className="px-4 py-2 bg-[var(--surface-elevated)] border-b border-[var(--border)] text-xs font-medium text-[var(--text-secondary)] flex justify-between items-center">
                        <span>{message.model || 'Model'}</span>
                        {message.isStreaming && <span className="loading-dots"><span></span><span></span><span></span></span>}
                      </div>
                      <div className="px-4 py-3">
                        <MessageBubble
                          message={message}
                          onRegenerate={regenerateLastResponse}
                          onEdit={editAndResend}
                          onSuggestionClick={handleSuggestionClick}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )
          } else {
            // Render single message
            return group.messages.map((message) => (
              <MessageBubble
                key={message.id}
                message={message}
                onRegenerate={regenerateLastResponse}
                onEdit={editAndResend}
                onSuggestionClick={handleSuggestionClick}
              />
            ))
          }
        })}
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
            onSuggestionClick: handleSuggestionClick,
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
