import { useEffect, useRef } from 'react'
import { useParams } from 'react-router-dom'
import { useConversationStore } from '../stores/conversationStore'
import { useUIStore } from '../stores/uiStore'
import { useArtifactStore } from '../stores/artifactStore'
import { MessageList } from '../components/MessageList'
import { ChatInput } from '../components/ChatInput'
import { WelcomeScreen } from '../components/WelcomeScreen'
import { ArtifactPanel } from '../components/ArtifactPanel'
import { TodoPanel } from '../components/TodoPanel'
import { FilesPanel } from '../components/FilesPanel'
import { DiffPanel } from '../components/DiffPanel'

export function ChatPage() {
  const { conversationId } = useParams()
  const { messages, currentConversationId, setCurrentConversation, loadMessages } = useConversationStore()
  const { panelOpen, panelType } = useUIStore()
  const { loadArtifactsForConversation, clearArtifacts } = useArtifactStore()
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Set current conversation from URL
  useEffect(() => {
    if (conversationId) {
      setCurrentConversation(conversationId)
      loadMessages(conversationId)
      loadArtifactsForConversation(conversationId)
    } else {
      clearArtifacts()
    }
  }, [conversationId, setCurrentConversation, loadMessages, loadArtifactsForConversation, clearArtifacts])

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const showWelcome = messages.length === 0 && !currentConversationId

  // Determine panel width based on type
  const getPanelWidth = () => {
    if (panelType === 'diffs') return 'mr-[600px]'
    return 'mr-[450px]'
  }

  return (
    <div className="flex flex-col h-full relative">
      {/* Messages area */}
      <div className={`flex-1 overflow-y-auto transition-all duration-300 ${panelOpen ? getPanelWidth() : ''}`}>
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
      <div className={`flex-shrink-0 border-t border-[var(--border-primary)] transition-all duration-300 ${panelOpen ? getPanelWidth() : ''}`}>
        <ChatInput />
      </div>

      {/* Panels */}
      {panelType === 'artifacts' && <ArtifactPanel />}
      {panelType === 'todos' && <TodoPanel />}
      {panelType === 'files' && <FilesPanel />}
      {panelType === 'diffs' && <DiffPanel />}
    </div>
  )
}
