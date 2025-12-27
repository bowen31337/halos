import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { MessageBubble } from '../components/MessageBubble'

interface SharedConversation {
  id: string
  title: string
  model: string
  messages: Array<{
    id: string
    role: 'user' | 'assistant' | 'system' | 'tool'
    content: string
    createdAt: string
    attachments?: string[]
    thinkingContent?: string
  }>
  access_level: string
  allow_comments: boolean
}

export function SharedView() {
  const { shareToken } = useParams<{ shareToken: string }>()
  const [sharedData, setSharedData] = useState<SharedConversation | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (shareToken) {
      loadSharedConversation()
    }
  }, [shareToken])

  const loadSharedConversation = async () => {
    try {
      const response = await fetch(`/api/conversations/share/${shareToken}`)

      if (response.status === 410) {
        setError('This share link has expired.')
        return
      }

      if (response.status === 403) {
        setError('This share link is no longer active.')
        return
      }

      if (!response.ok) {
        throw new Error(`Failed to load: ${response.statusText}`)
      }

      const data = await response.json()
      setSharedData(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-[var(--bg-primary)] flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[var(--primary)] mx-auto mb-4"></div>
          <p className="text-[var(--text-secondary)]">Loading shared conversation...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-[var(--bg-primary)] flex items-center justify-center p-4">
        <div className="bg-[var(--surface-secondary)] border border-[var(--border-primary)] rounded-lg p-6 max-w-md w-full">
          <h2 className="text-xl font-semibold text-[var(--text-primary)] mb-2">Unable to Load Conversation</h2>
          <p className="text-[var(--text-secondary)] mb-4">{error}</p>
          <Link
            to="/"
            className="inline-block bg-[var(--primary)] text-white px-4 py-2 rounded hover:opacity-90 transition-opacity"
          >
            Return to Home
          </Link>
        </div>
      </div>
    )
  }

  if (!sharedData) {
    return null
  }

  return (
    <div className="min-h-screen bg-[var(--bg-primary)]">
      {/* Header */}
      <div className="border-b border-[var(--border-primary)] bg-[var(--surface-secondary)] px-4 py-3">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex flex-col">
              <h1 className="text-lg font-semibold text-[var(--text-primary)]">
                {sharedData.title}
              </h1>
              <div className="flex items-center gap-2 text-xs text-[var(--text-secondary)]">
                <span>{sharedData.model}</span>
                <span>•</span>
                <span className="capitalize">{sharedData.access_level} access</span>
                {sharedData.allow_comments && <span>• Comments enabled</span>}
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Link
              to="/"
              className="px-3 py-1.5 text-sm bg-[var(--surface-elevated)] hover:bg-[var(--bg-primary)] rounded transition-colors"
            >
              Sign In to Chat
            </Link>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="max-w-4xl mx-auto px-4 py-6">
        {sharedData.messages.length === 0 ? (
          <div className="text-center py-12 text-[var(--text-secondary)]">
            <p>No messages in this conversation yet.</p>
          </div>
        ) : (
          <div className="space-y-4">
            {sharedData.messages.map((message) => (
              <MessageBubble
                key={message.id}
                message={{
                  id: message.id,
                  conversationId: sharedData.id,
                  role: message.role,
                  content: message.content,
                  createdAt: message.createdAt,
                  attachments: message.attachments,
                  thinkingContent: message.thinkingContent,
                }}
                isStreaming={false}
                onEdit={() => {}}
                onRegenerate={() => {}}
                onBranch={() => {}}
                readOnly={true}
              />
            ))}
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="border-t border-[var(--border-primary)] bg-[var(--surface-secondary)] px-4 py-3">
        <div className="max-w-4xl mx-auto text-center text-sm text-[var(--text-secondary)]">
          <p>Shared conversation view • Read-only</p>
          <p className="text-xs mt-1">
            This conversation was shared via a public link. To continue chatting, sign in to your account.
          </p>
        </div>
      </div>
    </div>
  )
}
