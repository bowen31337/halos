import type { Message } from '../stores/conversationStore'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism'
import { useState } from 'react'
import { useArtifactStore } from '../stores/artifactStore'
import { useUIStore } from '../stores/uiStore'
import { useConversationStore } from '../stores/conversationStore'
import { useBranchingStore } from '../stores/branchingStore'
import { OptimizedImage } from './OptimizedImage'

interface MessageBubbleProps {
  message: Message
  onRegenerate?: (messageId: string) => void
  onEdit?: (messageId: string, content: string) => void
}

export function MessageBubble({ message, onRegenerate, onEdit }: MessageBubbleProps) {
  const isUser = message.role === 'user'
  const isTool = message.role === 'tool'
  const isStreaming = message.isStreaming
  const isThinking = message.isThinking
  const hasThinkingContent = !!message.thinkingContent
  const [copiedCode, setCopiedCode] = useState<string | null>(null)
  const [showActions, setShowActions] = useState(false)
  const [isEditing, setIsEditing] = useState(false)
  const [editedContent, setEditedContent] = useState(message.content)
  const [thinkingExpanded, setThinkingExpanded] = useState(false)
  const [isExtracting, setIsExtracting] = useState(false)
  const [isBranching, setIsBranching] = useState(false)

  const { detectArtifacts } = useArtifactStore()
  const { setPanelType, setPanelOpen } = useUIStore()
  const { messages, currentConversationId, setCurrentConversation, loadMessages } = useConversationStore()
  const { createBranch, loadBranchPath } = useBranchingStore()

  const hasCodeBlocks = message.content && /```/.test(message.content)
  const currentIndex = messages.findIndex(m => m.id === message.id)
  const isLastMessage = currentIndex === messages.length - 1

  const copyToClipboard = async (text: string, language: string) => {
    try {
      await navigator.clipboard.writeText(text)
      setCopiedCode(language)
      setTimeout(() => setCopiedCode(null), 2000)
    } catch (err) {
      console.error('Failed to copy:', err)
    }
  }

  const handleEdit = () => {
    if (isUser && onEdit) {
      onEdit(message.id, editedContent)
      setIsEditing(false)
    }
  }

  const handleBranch = async () => {
    if (isBranching) return

    // Branching works from user messages - clicking on a user message creates a branch from that point
    // Or from assistant messages (but not the last one)
    const canBranch = isUser || (!isUser && !isLastMessage)

    if (!canBranch) {
      console.log('Cannot branch from this message')
      return
    }

    try {
      setIsBranching(true)
      const result = await createBranch(message.conversationId, message.id, undefined, '#ff6b6b')

      // Switch to the new branch conversation
      if (result?.conversation?.id) {
        setCurrentConversation(result.conversation.id)
        await loadMessages(result.conversation.id)
        await loadBranchPath(result.conversation.id)
      }
    } catch (err) {
      console.error('Failed to create branch:', err)
    } finally {
      setIsBranching(false)
    }
  }

  const handleExtractArtifacts = async () => {
    setIsExtracting(true)
    try {
      const artifacts = await detectArtifacts(message.content, message.conversationId)
      if (artifacts.length > 0) {
        setPanelType('artifacts')
        setPanelOpen(true)
      }
    } catch (error) {
      console.error('Failed to extract artifacts:', error)
    } finally {
      setIsExtracting(false)
    }
  }

  if (isTool) {
    const [isExpanded, setIsExpanded] = useState(true)
    const toolName = message.toolName || 'unknown'
    const toolInput = message.toolInput || {}
    const toolOutput = message.toolOutput || message.content || ''

    // Format tool input as JSON
    const formattedInput = Object.keys(toolInput).length > 0
      ? JSON.stringify(toolInput, null, 2)
      : '{}'

    return (
      <div className="mb-6 fade-in-mount">
        <div className="bg-gradient-to-br from-[var(--surface-elevated)] to-[var(--bg-secondary)] rounded-lg border border-[var(--border-primary)] overflow-hidden shadow-sm card-hover">
          {/* Tool header with distinct accent */}
          <div
            className="flex items-center justify-between px-4 py-3 cursor-pointer hover:bg-[var(--surface-secondary)] transition-colors-smooth border-b border-[var(--border)]/50"
            onClick={() => setIsExpanded(!isExpanded)}
          >
            <div className="flex items-center gap-3 text-sm font-medium text-[var(--text-primary)]">
              <div className="w-6 h-6 rounded bg-[var(--info)]/20 flex items-center justify-center text-[var(--info)] text-xs font-bold"
                   style={{ fontFamily: 'monospace' }}>
                {toolName.substring(0, 3).toUpperCase()}
              </div>
              <span className="font-semibold tracking-wide">{toolName}</span>
              <span className="text-xs px-2 py-0.5 bg-[var(--info)]/10 text-[var(--info)] rounded-full border border-[var(--info)]/20"
                    style={{ letterSpacing: '0.05em' }}>
                TOOL CALL
              </span>
            </div>
            <div className="flex items-center gap-2">
              <span className={`text-xs px-2 py-0.5 rounded transition-colors-smooth ${isExpanded ? 'bg-[var(--bg-primary)] text-[var(--text-secondary)]' : 'bg-[var(--surface-secondary)] text-[var(--text-secondary)]'}`}>
                {isExpanded ? 'Collapse' : 'Expand'}
              </span>
              <svg
                className={`w-4 h-4 text-[var(--text-secondary)] transition-transform-smooth ${isExpanded ? 'rotate-180' : ''}`}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </div>
          </div>

          {/* Tool content - collapsible with smooth animation */}
          {isExpanded && (
            <div className="px-4 pb-3 space-y-3 animate-fade-in">
              {/* Tool Input */}
              <div>
                <div className="flex items-center gap-2 text-xs font-semibold text-[var(--text-secondary)] mb-1">
                  <span className="w-1.5 h-1.5 bg-[var(--info)] rounded-full"></span>
                  <span>Input Parameters</span>
                </div>
                <pre className="text-xs text-[var(--text-primary)] bg-[var(--bg-primary)]/80 p-3 rounded-lg overflow-x-auto font-mono border border-[var(--border)]/50"
                     style={{ borderRadius: '0.5rem' }}>
                  {formattedInput}
                </pre>
              </div>

              {/* Tool Output */}
              {toolOutput && (
                <div>
                  <div className="flex items-center gap-2 text-xs font-semibold text-[var(--text-secondary)] mb-1">
                    <span className="w-1.5 h-1.5 bg-[var(--success)] rounded-full"></span>
                    <span>Output Result</span>
                  </div>
                  <pre className="text-xs text-[var(--text-primary)] bg-[var(--bg-primary)]/80 p-3 rounded-lg overflow-x-auto font-mono whitespace-pre-wrap border border-[var(--border)]/50"
                       style={{ borderRadius: '0.5rem' }}>
                    {toolOutput}
                  </pre>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    )
  }

  return (
    <div
      className={`mb-6 group ${isUser ? 'flex justify-end' : ''}`}
      onMouseEnter={() => setShowActions(true)}
      onMouseLeave={() => setShowActions(false)}
    >
      <div
        className={`max-w-full ${isUser ? 'bg-[var(--primary)] text-white px-4 py-3 rounded-2xl' : 'bg-[var(--bg-secondary)] px-4 py-3 rounded-2xl border border-[var(--border)]'}`}
      >
        {!isUser && (
          <div className="flex items-center gap-2 mb-2">
            <div className="w-6 h-6 rounded-full bg-[var(--primary)] flex items-center justify-center text-white text-xs">
              C
            </div>
            <span className="text-sm font-medium text-[var(--text-secondary)]">
              Claude
            </span>
            {/* Thinking indicator badge */}
            {isThinking && (
              <span className="text-xs px-2 py-0.5 bg-[var(--surface-elevated)] rounded-full text-[var(--text-secondary)] flex items-center gap-2">
                <span className="loading-dots">
                  <span></span>
                  <span></span>
                  <span></span>
                </span>
                Thinking...
              </span>
            )}
            {/* Token usage badge */}
            {!isThinking && message.inputTokens && message.outputTokens && (
              <span className="text-xs px-2 py-0.5 bg-[var(--surface-elevated)] rounded-full text-[var(--text-secondary)] flex items-center gap-1">
                <span className="text-[var(--primary)]">🔢</span>
                {message.inputTokens} in, {message.outputTokens} out
                {message.cacheReadTokens ? ` (${message.cacheReadTokens} cached)` : ''}
                {message.cacheWriteTokens ? ` (+${message.cacheWriteTokens} cache)` : ''}
              </span>
            )}
            {/* Action buttons for assistant messages */}
            {showActions && !isStreaming && !isEditing && (
              <div className="flex gap-1 ml-2">
                {hasCodeBlocks && (
                  <button
                    onClick={handleExtractArtifacts}
                    disabled={isExtracting}
                    className="p-1 hover:bg-[var(--bg-primary)] rounded transition-colors"
                    title="Extract artifacts"
                  >
                    {isExtracting ? '⏳' : '📦'}
                  </button>
                )}
                {onRegenerate && (
                  <button
                    onClick={() => onRegenerate(message.id)}
                    className="p-1 hover:bg-[var(--bg-primary)] rounded transition-colors"
                    title="Regenerate response"
                  >
                    🔄
                  </button>
                )}
                {/* Branch button - show for assistant messages that are not the last message */}
                {!isLastMessage && (
                  <button
                    onClick={handleBranch}
                    disabled={isBranching}
                    className="p-1 hover:bg-[var(--bg-primary)] rounded transition-colors"
                    title="Create branch from this message"
                  >
                    {isBranching ? '⏳' : '🌳'}
                  </button>
                )}
              </div>
            )}
          </div>
        )}

        {/* Display image attachments with optimization */}
        {message.attachments && message.attachments.length > 0 && (
          <div className="mb-3 flex flex-wrap gap-2">
            {message.attachments.map((attachment, idx) => {
              // Generate thumbnail URL by appending ?thumbnail=1 if the backend supports it
              // Otherwise, the OptimizedImage component will handle lazy loading
              const thumbnailSrc = attachment.includes('?')
                ? `${attachment}&thumbnail=1`
                : `${attachment}?thumbnail=1`

              return (
                <div key={idx} className="group relative">
                  <OptimizedImage
                    src={attachment}
                    thumbnailSrc={thumbnailSrc}
                    alt={`Attachment ${idx + 1}`}
                    className="max-w-md max-h-64 rounded-lg border border-[var(--border-primary)]"
                    placeholderClassName="w-full h-full min-w-[120px] min-h-[80px]"
                  />
                </div>
              )
            })}
          </div>
        )}

        {/* Collapsible thinking content */}
        {!isUser && hasThinkingContent && (
          <div className="mb-3">
            <button
              onClick={() => setThinkingExpanded(!thinkingExpanded)}
              className="text-xs text-[var(--text-secondary)] hover:text-[var(--text-primary)] flex items-center gap-1 transition-colors"
            >
              <svg
                className={`w-3 h-3 transition-transform ${thinkingExpanded ? 'rotate-90' : ''}`}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
              {thinkingExpanded ? 'Hide thinking' : 'Show thinking'} process
            </button>
            {thinkingExpanded && (
              <div className="mt-2 p-3 bg-[var(--surface-elevated)] rounded-lg border border-[var(--border-primary)]">
                <div className="text-xs font-medium text-[var(--text-secondary)] mb-2">Thinking Process:</div>
                <div className="text-xs text-[var(--text-secondary)] whitespace-pre-wrap font-mono leading-relaxed">
                  {message.thinkingContent}
                </div>
              </div>
            )}
          </div>
        )}

        <div className={isUser ? 'text-white' : 'text-[var(--text-primary)] prose prose-sm max-w-none'}>
          {isUser ? (
            isEditing ? (
              <div className="space-y-2">
                <textarea
                  value={editedContent}
                  onChange={(e) => setEditedContent(e.target.value)}
                  className="w-full p-2 rounded bg-white/10 resize-none"
                  rows={3}
                />
                <div className="flex gap-2">
                  <button
                    onClick={handleEdit}
                    className="px-3 py-1 bg-white/20 hover:bg-white/30 rounded text-sm"
                  >
                    Resend
                  </button>
                  <button
                    onClick={() => {
                      setIsEditing(false)
                      setEditedContent(message.content)
                    }}
                    className="px-3 py-1 bg-white/10 hover:bg-white/20 rounded text-sm"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            ) : (
              <p className="whitespace-pre-wrap">{message.content}</p>
            )
          ) : (
            <>
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  code({ node, className, children, ...props }) {
                    const match = /language-(\w+)/.exec(className || '')
                    const language = match ? match[1] : ''
                    const codeString = String(children).replace(/\n$/, '')
                    // Inline code has no language class, block code does
                    const isInline = !language

                    if (!isInline) {
                      return (
                        <div className="relative group my-4">
                          <div className="flex items-center justify-between bg-[var(--surface-elevated)] px-4 py-2 rounded-t-lg border border-[var(--border)] border-b-0">
                            <span className="text-xs font-medium text-[var(--text-secondary)]">
                              {language}
                            </span>
                            <button
                              onClick={() => copyToClipboard(codeString, language)}
                              className="text-xs px-2 py-1 rounded bg-[var(--bg-primary)] hover:bg-[var(--border)] text-[var(--text-secondary)] transition-colors"
                            >
                              {copiedCode === language ? '✓ Copied!' : '📋 Copy'}
                            </button>
                          </div>
                          <SyntaxHighlighter
                            style={oneDark}
                            language={language}
                            PreTag="div"
                            className="!mt-0 !rounded-t-none"
                            customStyle={{
                              background: 'var(--bg-primary)',
                              padding: '1rem',
                            }}
                          >
                            {codeString}
                          </SyntaxHighlighter>
                        </div>
                      )
                    }

                    return (
                      <code className="bg-[var(--surface-elevated)] px-1.5 py-0.5 rounded text-sm font-mono" {...props}>
                        {children}
                      </code>
                    )
                  },
                }}
              >
                {message.content || (isStreaming ? '' : '...')}
              </ReactMarkdown>
              {isStreaming && (
                <span className="typing-indicator"></span>
              )}
            </>
          )}
        </div>

        {/* Edit button for user messages */}
        {isUser && showActions && !isEditing && (
          <div className="mt-2 flex gap-1">
            <button
              onClick={() => setIsEditing(true)}
              className="p-1 hover:bg-white/10 rounded transition-colors"
              title="Edit message"
            >
              ✏️
            </button>
            {/* Branch button for user messages */}
            <button
              onClick={handleBranch}
              disabled={isBranching}
              className="p-1 hover:bg-white/10 rounded transition-colors"
              title="Create branch from this message"
            >
              {isBranching ? '⏳' : '🌳'}
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
