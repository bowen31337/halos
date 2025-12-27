import { useEffect, useRef, useState } from 'react'
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
import { SubAgentIndicator } from '../components/SubAgentIndicator'
import { MemoryPanel } from '../components/MemoryPanel'
import { PromptCacheIndicator } from '../components/PromptCacheIndicator'
import { TokenUsageDisplay } from '../components/TokenUsageDisplay'
import { UsageDashboard } from '../components/UsageDashboard'
import { ComparisonView } from '../components/ComparisonView'

export function ChatPage() {
  const { conversationId } = useParams()
  const { messages, currentConversationId, setCurrentConversation, loadMessages } = useConversationStore()
  const { panelOpen, panelType, setPanelOpen, comparisonMode } = useUIStore()
  const { loadArtifactsForConversation, clearArtifacts } = useArtifactStore()
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const [isTablet, setIsTablet] = useState(false)
  const [isMobile, setIsMobile] = useState(false)

  // Track screen size for responsive behavior
  useEffect(() => {
    const checkScreenSize = () => {
      const width = window.innerWidth
      setIsMobile(width < 768)
      setIsTablet(width >= 768 && width < 1024)
    }

    checkScreenSize()
    window.addEventListener('resize', checkScreenSize)
    return () => window.removeEventListener('resize', checkScreenSize)
  }, [])

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

  // Auto-scroll to bottom (only for small message lists)
  // Virtualized list handles its own scrolling
  useEffect(() => {
    if (messages.length < 15) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }
  }, [messages])

  const showWelcome = messages.length === 0

  // Determine panel width based on type and screen size
  const getPanelWidth = () => {
    if (panelType === 'diffs') return 'mr-[600px]'
    if (panelType === 'memory') return 'mr-[500px]'
    return 'mr-[450px]'
  }

  // On desktop, panels should adjust main content width
  const shouldAdjustWidth = panelOpen && !isTablet && !isMobile

  return (
    <div className="flex flex-col h-full relative overflow-hidden">
      {/* Messages area - virtualized list handles its own scrolling */}
      <div className={`flex-1 overflow-hidden transition-all duration-300 ${shouldAdjustWidth ? getPanelWidth() : ''}`}>
        {showWelcome ? (
          <div className="h-full overflow-y-auto">
            <WelcomeScreen />
          </div>
        ) : comparisonMode ? (
          <ComparisonMessageList messages={messages} />
        ) : (
          <MessageList />
        )}
      </div>

      {/* SubAgent Indicator - handles its own visibility */}
      <SubAgentIndicator />

      {/* Prompt Cache Indicator */}
      <PromptCacheIndicator />

      {/* Token Usage Display */}
      <TokenUsageDisplay />

      {/* Usage Dashboard */}
      <UsageDashboard />

      {/* Input area */}
      <div className={`flex-shrink-0 border-t border-[var(--border-primary)] transition-all duration-300 ${shouldAdjustWidth ? getPanelWidth() : ''}`}>
        <ChatInput />
      </div>

      {/* Panels - overlay on tablet/mobile, side panel on desktop */}
      {panelType === 'artifacts' && (
        <div className={`${isTablet || isMobile ? 'fixed inset-0 z-30' : ''}`}>
          {(isTablet || isMobile) && <div className="absolute inset-0 bg-black/50" onClick={() => setPanelOpen(false)} />}
          <ArtifactPanel />
        </div>
      )}
      {panelType === 'todos' && (
        <div className={`${isTablet || isMobile ? 'fixed inset-0 z-30' : ''}`}>
          {(isTablet || isMobile) && <div className="absolute inset-0 bg-black/50" onClick={() => setPanelOpen(false)} />}
          <TodoPanel />
        </div>
      )}
      {panelType === 'files' && (
        <div className={`${isTablet || isMobile ? 'fixed inset-0 z-30' : ''}`}>
          {(isTablet || isMobile) && <div className="absolute inset-0 bg-black/50" onClick={() => setPanelOpen(false)} />}
          <FilesPanel />
        </div>
      )}
      {panelType === 'diffs' && (
        <div className={`${isTablet || isMobile ? 'fixed inset-0 z-30' : ''}`}>
          {(isTablet || isMobile) && <div className="absolute inset-0 bg-black/50" onClick={() => setPanelOpen(false)} />}
          <DiffPanel />
        </div>
      )}
      {panelType === 'memory' && (
        <div className={`${isTablet || isMobile ? 'fixed inset-0 z-30' : ''}`}>
          {(isTablet || isMobile) && <div className="absolute inset-0 bg-black/50" onClick={() => setPanelOpen(false)} />}
          <MemoryPanel />
        </div>
      )}
    </div>
  )
}
