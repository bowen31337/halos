import type { Message } from '../stores/conversationStore'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism'
import { useState } from 'react'

interface MessageBubbleProps {
  message: Message
  onRegenerate?: (messageId: string) => void
  onEdit?: (messageId: string, content: string) => void
}

export function MessageBubble({ message, onRegenerate, onEdit }: MessageBubbleProps) {
  const isUser = message.role === 'user'
  const isTool = message.role === 'tool'
  const isStreaming = message.isStreaming
  const [copiedCode, setCopiedCode] = useState<string | null>(null)
  const [showActions, setShowActions] = useState(false)
  const [isEditing, setIsEditing] = useState(false)
  const [editedContent, setEditedContent] = useState(message.content)

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

  if (isTool) {
    return (
      <div className="mb-6">
        <div className="bg-[var(--surface-elevated)] rounded-lg border border-[var(--border-primary)] p-4">
          <div className="flex items-center gap-2 text-sm font-medium text-[var(--text-secondary)] mb-2">
            <span>🔧</span>
            <span>Tool: {message.toolName || 'unknown'}</span>
          </div>
          <pre className="text-sm text-[var(--text-secondary)] overflow-x-auto">
            {message.toolOutput || message.content}
          </pre>
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
        className={`max-w-full ${isUser ? 'bg-[var(--primary)] text-white px-4 py-3 rounded-2xl' : ''}`}
      >
        {!isUser && (
          <div className="flex items-center gap-2 mb-2">
            <div className="w-6 h-6 rounded-full bg-[var(--primary)] flex items-center justify-center text-white text-xs">
              C
            </div>
            <span className="text-sm font-medium text-[var(--text-secondary)]">
              Claude
            </span>
            {/* Action buttons for assistant messages */}
            {showActions && !isStreaming && !isEditing && (
              <div className="flex gap-1 ml-2">
                {onRegenerate && (
                  <button
                    onClick={() => onRegenerate(message.id)}
                    className="p-1 hover:bg-[var(--bg-secondary)] rounded transition-colors"
                    title="Regenerate response"
                  >
                    🔄
                  </button>
                )}
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

                    if (!inline && language) {
                      return (
                        <div className="relative group my-4">
                          <div className="flex items-center justify-between bg-[var(--bg-secondary)] px-4 py-2 rounded-t-lg border border-[var(--border)] border-b-0">
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
                      <code className="bg-[var(--bg-secondary)] px-1.5 py-0.5 rounded text-sm font-mono" {...props}>
                        {children}
                      </code>
                    )
                  },
                }}
              >
                {message.content || (isStreaming ? '' : '...')}
              </ReactMarkdown>
              {isStreaming && (
                <span className="inline-block w-2 h-4 ml-1 bg-[var(--text-secondary)] animate-pulse align-middle"></span>
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
          </div>
        )}
      </div>
    </div>
  )
}
