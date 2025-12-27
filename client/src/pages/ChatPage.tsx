import { useEffect, useRef } from 'react'
import { useParams } from 'react-router-dom'
import { useConversationStore } from '../stores/conversationStore'
import { MessageList } from '../components/MessageList'
import { ChatInput } from '../components/ChatInput'
import { WelcomeScreen } from '../components/WelcomeScreen'

export function ChatPage() {
  const { conversationId } = useParams()
  const { messages, currentConversationId, setCurrentConversation, loadMessages } = useConversationStore()
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Set current conversation from URL
  useEffect(() => {
    if (conversationId) {
      setCurrentConversation(conversationId)
      loadMessages(conversationId)
    }
  }, [conversationId, setCurrentConversation, loadMessages])

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const showWelcome = messages.length === 0 && !currentConversationId

  return (
    <div className="flex flex-col h-full">
      {/* Messages area */}
      <div className="flex-1 overflow-y-auto">
        {showWelcome ? (
          <WelcomeScreen />
        ) : (
          <>
            <MessageList />
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* Input area */}
      <div className="flex-shrink-0 border-t border-[var(--border-primary)]">
        <ChatInput />
      </div>
    </div>
  )
}
