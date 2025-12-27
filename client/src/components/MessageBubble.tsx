import { Message } from '../stores/conversationStore'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

interface MessageBubbleProps {
  message: Message
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user'
  const isTool = message.role === 'tool'
  const isStreaming = message.isStreaming

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
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
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
