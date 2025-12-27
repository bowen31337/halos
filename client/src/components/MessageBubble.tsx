import { Message } from '../stores/conversationStore'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { oneDark, oneLight } from 'react-syntax-highlighter/dist/esm/styles/prism'
import { useState } from 'react'

interface MessageBubbleProps {
  message: Message
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user'
  const isTool = message.role === 'tool'
  const isStreaming = message.isStreaming
  const [copiedCode, setCopiedCode] = useState<string | null>(null)

  const copyToClipboard = async (text: string, language: string) => {
    try {
      await navigator.clipboard.writeText(text)
      setCopiedCode(language)
      setTimeout(() => setCopiedCode(null), 2000)
    } catch (err) {
      console.error('Failed to copy:', err)
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
    <div className={`mb-6 ${isUser ? 'flex justify-end' : ''}`}>
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
          </div>
        )}

        <div className={isUser ? 'text-white' : 'text-[var(--text-primary)] prose prose-sm max-w-none'}>
          {isUser ? (
            <p className="whitespace-pre-wrap">{message.content}</p>
          ) : (
            <>
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  code({ node, inline, className, children, ...props }) {
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
      </div>
    </div>
  )
}
