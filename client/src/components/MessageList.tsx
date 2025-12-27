import { useConversationStore } from '../stores/conversationStore'
import { MessageBubble } from './MessageBubble'
import { ThinkingIndicator } from './ThinkingIndicator'

export function MessageList() {
  const { messages, isStreaming, regenerateLastResponse, editAndResend } = useConversationStore()

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

      {isStreaming && <ThinkingIndicator />}
    </div>
  )
}
