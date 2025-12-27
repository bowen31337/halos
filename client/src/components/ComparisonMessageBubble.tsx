import type { Message } from '../stores/conversationStore'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism'
import { useState } from 'react'
import { OptimizedImage } from './OptimizedImage'
import { SuggestedFollowUps } from './SuggestedFollowUps'
import { MODELS } from './Header'

interface ComparisonMessageBubbleProps {
  message: Message
  modelId: string
  isLeft: boolean
  onSuggestionClick?: (suggestion: string) => void
}

// Helper function to format relative time
function formatRelativeTime(dateString: string): string {
  const date = new Date(dateString)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)

  if (diffMins < 1) return 'Just now'
  if (diffMins < 60) return `${diffMins}m ago`
  if (diffHours < 24) return `${diffHours}h ago`
  if (diffDays < 7) return `${diffDays}d ago`
  return date.toLocaleDateString()
}

export function ComparisonMessageBubble({
  message,
  modelId,
  isLeft,
  onSuggestionClick
}: ComparisonMessageBubbleProps) {
  const isUser = message.role === 'user'
  const isTool = message.role === 'tool'
  const isStreaming = message.isStreaming
  const isThinking = message.isThinking
  const hasThinkingContent = !!message.thinkingContent
  const [copiedCode, setCopiedCode] = useState<string | null>(null)
  const [thinkingExpanded, setThinkingExpanded] = useState(false)

  const model = MODELS.find(m => m.id === modelId)

  const hasCodeBlocks = message.content && /```/.test(message.content)

  // Format timestamp
  const timestamp = {
    full: new Date(message.createdAt).toLocaleString(),
    relative: formatRelativeTime(message.createdAt)
  }

  const copyToClipboard = async (text: string, language: string) => {
    try {
      await navigator.clipboard.writeText(text)
      setCopiedCode(language)
      setTimeout(() => setCopiedCode(null), 2000)
    } catch (err) {
      console.error('Failed to copy:', err)
    }
  }

  const getModelColor = (modelId: string) => {
    switch (modelId) {
      case 'claude-sonnet-4-5-20250929': return '#CC785C' // Sonnet orange
      case 'claude-haiku-4-5-20251001': return '#5CC8CC'  // Haiku teal
      case 'claude-opus-4-1-20250805': return '#785CCC'   // Opus purple
      default: return '#CC785C'
    }
  }

  const modelColor = getModelColor(modelId)

  // Calculate split view width classes
  const containerClass = isLeft
    ? 'w-1/2 pr-2 border-r border-[var(--border-primary)]'
    : 'w-1/2 pl-2'

  const headerClass = isLeft
    ? 'border-r border-[var(--border-primary)]'
    : 'border-l border-[var(--border-primary)]'

  return (
    <div className={`${containerClass} px-4 py-6`}>
      {/* Model Header */}
      <div className={`flex items-center justify-between p-3 bg-[var(--surface-elevated)] rounded-t-lg border ${headerClass} border-b-0`}>
        <div className="flex items-center gap-3">
          <div
            className="w-3 h-3 rounded-full"
            style={{ backgroundColor: modelColor }}
          />
          <div>
            <div className="font-semibold text-[var(--text-primary)]">
              {model?.name || 'Unknown Model'}
            </div>
            <div className="text-sm text-[var(--text-secondary)]">
              {model?.description || 'Model'}
            </div>
          </div>
        </div>
        <div className="text-xs text-[var(--text-secondary)]" title={timestamp.full}>
          {timestamp.relative}
        </div>
      </div>

      {/* Message Content */}
      <div className="bg-[var(--bg-primary)] border border-[var(--border-primary)] rounded-b-lg p-6 min-h-20">
        {/* Thinking content */}
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

        {isUser ? (
          <div className="text-white">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-white">You</span>
              <span className="text-xs text-white/80" title={timestamp.full}>
                {timestamp.relative}
              </span>
            </div>
            <p className="whitespace-pre-wrap">{message.content}</p>
          </div>
        ) : (
          <div className="text-[var(--text-primary)] prose prose-sm max-w-none">
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                code({ node, className, children, ...props }) {
                  const match = /language-(\w+)/.exec(className || '')
                  const language = match ? match[1] : ''
                  const codeString = String(children).replace(/\n$/, '')
                  const isInline = !language

                  if (!isInline) {
                    return (
                      <div className="relative group my-4">
                        <div className="flex items-center justify-between bg-[var(--surface-elevated)] px-4 py-2 rounded-t-lg border border-[var(--border-primary)] border-b-0">
                          <span className="text-xs font-medium text-[var(--text-secondary)]">
                            {language}
                          </span>
                          <button
                            onClick={() => copyToClipboard(codeString, language)}
                            className="text-xs px-2 py-1 rounded bg-[var(--bg-primary)] hover:bg-[var(--border-primary)] text-[var(--text-secondary)] transition-colors"
                          >
                            {copiedCode === language ? '✓ Copied!' : '📋 Copy'}
                          </button>
                        </div>
                        <div className="bg-[var(--bg-secondary)] rounded-b-lg p-4 border border-[var(--border-primary)] border-t-0">
                          <SyntaxHighlighter
                            language={language}
                            style={oneDark}
                            customStyle={{
                              margin: 0,
                              fontSize: '12px',
                              lineHeight: '1.4',
                              background: 'transparent',
                              padding: 0,
                            }}
                            wrapLines
                            wrapLongLines
                          >
                            {codeString}
                          </SyntaxHighlighter>
                        </div>
                      </div>
                    )
                  }

                  return (
                    <code className="bg-[var(--bg-secondary)] px-1.5 py-0.5 rounded text-xs" {...props}>
                      {children}
                    </code>
                  )
                },
                img({ src, alt, ...props }) {
                  if (!src) return null

                  // Handle data URLs and base64 images
                  if (src.startsWith('data:image/')) {
                    return (
                      <OptimizedImage
                        src={src}
                        alt={alt || 'Generated image'}
                        className="max-w-full rounded-lg border border-[var(--border-primary)]"
                      />
                    )
                  }

                  return (
                    <img
                      src={src}
                      alt={alt}
                      className="max-w-full rounded-lg border border-[var(--border-primary)]"
                      {...props}
                    />
                  )
                },
                table({ children, ...props }) {
                  return (
                    <div className="overflow-x-auto">
                      <table {...props} className="w-full border border-[var(--border-primary)]">
                        {children}
                      </table>
                    </div>
                  )
                },
                th({ children, ...props }) {
                  return (
                    <th {...props} className="border-b border-[var(--border-primary)] px-3 py-2 text-left font-semibold bg-[var(--surface-elevated)]">
                      {children}
                    </th>
                  )
                },
                td({ children, ...props }) {
                  return (
                    <td {...props} className="border-b border-[var(--border-primary)] px-3 py-2">
                      {children}
                    </td>
                  )
                },
                pre({ children, ...props }) {
                  // Handle code blocks that don't have the language class
                  if (children && children.props?.className?.includes('language-')) {
                    return <>{children}</>
                  }

                  return (
                    <pre {...props} className="bg-[var(--bg-secondary)] p-4 rounded-lg border border-[var(--border-primary)] overflow-x-auto font-mono text-sm">
                      {children}
                    </pre>
                  )
                }
              }}
            >
              {message.content}
            </ReactMarkdown>
            {isStreaming && (
              <span className="typing-indicator"></span>
            )}
          </div>
        )}

        {/* Suggested follow-ups for assistant messages */}
        {!isUser && !isStreaming && message.suggestedFollowUps && message.suggestedFollowUps.length > 0 && onSuggestionClick && (
          <SuggestedFollowUps
            suggestions={message.suggestedFollowUps}
            onSuggestionClick={onSuggestionClick}
          />
        )}
      </div>
    </div>
  )
}