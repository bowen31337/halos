import { useConversationStore } from '../stores/conversationStore'
import { ComparisonMessageBubble } from './ComparisonMessageBubble'
import { ThinkingIndicator } from './ThinkingIndicator'
import { useUIStore } from '../stores/uiStore'
import { useCallback } from 'react'
import type { Message } from '../stores/conversationStore'

interface ComparisonMessageListProps {
  messages: Message[]
  onSuggestionClick?: (suggestion: string) => void
}

export function ComparisonMessageList({ messages, onSuggestionClick }: ComparisonMessageListProps) {
  const { isStreaming, regenerateLastResponse, editAndResend } = useConversationStore()
  const { comparisonModels } = useUIStore()

  // Handle suggestion click - dispatch event to set input and focus
  const handleSuggestionClick = useCallback((suggestion: string) => {
    if (onSuggestionClick) {
      onSuggestionClick(suggestion)
    }
  }, [onSuggestionClick])

  // Group messages for comparison view
  // We need to process messages in order and group assistant messages by comparisonGroup
  const renderMessages = () => {
    const elements: JSX.Element[] = []
    const processedAssistantGroups = new Set<string>()
    let i = 0

    while (i < messages.length) {
      const message = messages[i]

      if (message.role === 'user') {
        // User message - show full width
        elements.push(
          <div key={message.id} className="w-full px-4 py-6">
            <ComparisonMessageBubble
              message={message}
              modelId={comparisonModels[0]}
              isLeft={true}
              onSuggestionClick={handleSuggestionClick}
            />
          </div>
        )
        i++
      } else if (message.role === 'assistant' && message.comparisonGroup) {
        // Assistant message in comparison mode
        const group = message.comparisonGroup

        // Skip if we've already processed this group
        if (processedAssistantGroups.has(group)) {
          i++
          continue
        }

        processedAssistantGroups.add(group)

        // Find all messages in this group
        const groupMessages = messages.filter(m => m.comparisonGroup === group)

        // Get messages for each model
        const leftMsg = groupMessages.find(m => m.model === comparisonModels[0])
        const rightMsg = groupMessages.find(m => m.model === comparisonModels[1])

        // Determine if any message in this group is streaming
        const isGroupStreaming = groupMessages.some(m => m.isStreaming)

        elements.push(
          <div key={group} className="flex gap-4 border border-[var(--border-primary)] rounded-lg mb-8 mx-4">
            {/* Left side - Model 1 */}
            <div className="w-1/2 pr-2 border-r border-[var(--border-primary)]">
              {leftMsg ? (
                <ComparisonMessageBubble
                  message={leftMsg}
                  modelId={comparisonModels[0]}
                  isLeft={true}
                  onSuggestionClick={handleSuggestionClick}
                />
              ) : isGroupStreaming ? (
                <div className="p-6 text-center text-[var(--text-secondary)] text-sm">
                  <ThinkingIndicator />
                </div>
              ) : (
                <div className="p-6 text-center text-[var(--text-secondary)] text-sm">
                  No response
                </div>
              )}
            </div>
            {/* Right side - Model 2 */}
            <div className="w-1/2 pl-2">
              {rightMsg ? (
                <ComparisonMessageBubble
                  message={rightMsg}
                  modelId={comparisonModels[1]}
                  isLeft={false}
                  onSuggestionClick={handleSuggestionClick}
                />
              ) : isGroupStreaming ? (
                <div className="p-6 text-center text-[var(--text-secondary)] text-sm">
                  <ThinkingIndicator />
                </div>
              ) : (
                <div className="p-6 text-center text-[var(--text-secondary)] text-sm">
                  No response
                </div>
              )}
            </div>
          </div>
        )

        i++
      } else if (message.role === 'assistant') {
        // Assistant message without comparisonGroup (single model mode fallback)
        elements.push(
          <div key={message.id} className="w-full px-4 py-6">
            <ComparisonMessageBubble
              message={message}
              modelId={comparisonModels[0]}
              isLeft={true}
              onSuggestionClick={handleSuggestionClick}
            />
          </div>
        )
        i++
      } else {
        // Other message types (tool, system) - skip for now
        i++
      }
    }

    return elements
  }

  return (
    <div className="max-w-6xl mx-auto py-8">
      {renderMessages()}
    </div>
  )
}
