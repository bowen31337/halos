import { useConversationStore } from '../stores/conversationStore'
import { MessageBubble } from './MessageBubble'
import { ThinkingIndicator } from './ThinkingIndicator'

export function MessageList() {
  const { messages, isStreaming, regenerateLastResponse, editAndResend } = useConversationStore()

  // Check if the last message is thinking
  const lastMessage = messages[messages.length - 1]
  const isLastMessageThinking = lastMessage?.role === 'assistant' && lastMessage?.isThinking

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

      {/* Show thinking indicator when streaming or when last message is thinking */}
      {(isStreaming || isLastMessageThinking) && <ThinkingIndicator />}
    </div>
  )
}
