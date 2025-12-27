import { useState, useEffect } from 'react'
import { useCommentStore, Comment } from '../stores/commentStore'
import { format } from 'date-fns'

interface CommentSectionProps {
  shareToken: string
  messageId: string
  allowComments: boolean
}

export function CommentSection({ shareToken, messageId, allowComments }: CommentSectionProps) {
  const {
    comments,
    isLoading,
    error,
    replyToComment,
    setReplyToComment,
    createComment,
    deleteComment,
    loadComments
  } = useCommentStore()

  const [newComment, setNewComment] = useState('')
  const [anonymousName, setAnonymousName] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [showInput, setShowInput] = useState(false)

  // Filter comments for this specific message
  const messageComments = comments.filter(c => c.message_id === messageId && !c.parent_comment_id)

  useEffect(() => {
    if (allowComments) {
      loadComments(shareToken, messageId)
    }
  }, [shareToken, messageId, allowComments])

  const handleSubmit = async () => {
    if (!newComment.trim()) return

    setIsSubmitting(true)
    try {
      await createComment(shareToken, {
        message_id: messageId,
        content: newComment.trim(),
        parent_comment_id: replyToComment?.id,
        anonymous_name: anonymousName || undefined
      })
      setNewComment('')
      setReplyToComment(null)
      setShowInput(false)
    } catch (err) {
      console.error('Failed to create comment:', err)
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleDelete = async (commentId: string) => {
    if (!confirm('Delete this comment?')) return
    try {
      await deleteComment(shareToken, commentId)
    } catch (err) {
      console.error('Failed to delete comment:', err)
    }
  }

  if (!allowComments) {
    return null
  }

  if (isLoading && comments.length === 0) {
    return <div className="text-sm text-gray-500 py-2">Loading comments...</div>
  }

  return (
    <div className="mt-2 space-y-2">
      {/* Comment Count */}
      {messageComments.length > 0 && (
        <div className="text-xs text-gray-600 font-medium">
          {messageComments.length} comment{messageComments.length > 1 ? 's' : ''}
        </div>
      )}

      {/* Existing Comments */}
      {messageComments.map((comment) => (
        <CommentItem
          key={comment.id}
          comment={comment}
          onReply={() => {
            setReplyToComment(comment)
            setShowInput(true)
          }}
          onDelete={() => handleDelete(comment.id)}
        />
      ))}

      {/* Reply Indicator */}
      {replyToComment && (
        <div className="text-xs bg-blue-50 text-blue-700 px-2 py-1 rounded flex items-center justify-between">
          <span>Replying to: {replyToComment.content.substring(0, 50)}...</span>
          <button
            onClick={() => setReplyToComment(null)}
            className="ml-2 font-bold hover:text-blue-900"
          >
            ✕
          </button>
        </div>
      )}

      {/* Input Area */}
      {showInput ? (
        <div className="space-y-2 border-t pt-2">
          <input
            type="text"
            placeholder="Your name (optional)"
            value={anonymousName}
            onChange={(e) => setAnonymousName(e.target.value)}
            className="w-full px-2 py-1 text-sm border rounded"
          />
          <textarea
            placeholder={replyToComment ? "Write a reply..." : "Add a comment..."}
            value={newComment}
            onChange={(e) => setNewComment(e.target.value)}
            className="w-full px-2 py-1 text-sm border rounded resize-none"
            rows={2}
            autoFocus
          />
          <div className="flex gap-2">
            <button
              onClick={handleSubmit}
              disabled={isSubmitting || !newComment.trim()}
              className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
            >
              {isSubmitting ? 'Posting...' : replyToComment ? 'Reply' : 'Post'}
            </button>
            <button
              onClick={() => {
                setShowInput(false)
                setReplyToComment(null)
              }}
              className="px-3 py-1 text-sm bg-gray-200 rounded hover:bg-gray-300"
            >
              Cancel
            </button>
          </div>
        </div>
      ) : (
        <button
          onClick={() => setShowInput(true)}
          className="text-xs text-blue-600 hover:text-blue-800 font-medium"
        >
          + Add comment
        </button>
      )}

      {error && (
        <div className="text-xs text-red-600 bg-red-50 px-2 py-1 rounded">
          {error}
        </div>
      )}
    </div>
  )
}

interface CommentItemProps {
  comment: Comment
  onReply: () => void
  onDelete: () => void
}

function CommentItem({ comment, onReply, onDelete }: CommentItemProps) {
  const [expanded, setExpanded] = useState(true)
  const replies = comment.replies || []

  return (
    <div className="pl-2 border-l-2 border-gray-200">
      <div className="bg-gray-50 rounded p-2 text-sm">
        <div className="flex items-center justify-between mb-1">
          <div className="flex items-center gap-2">
            <span className="font-semibold text-gray-700">
              {comment.anonymous_name || 'Anonymous'}
            </span>
            <span className="text-xs text-gray-500">
              {format(new Date(comment.created_at), 'MMM d, h:mm a')}
            </span>
            {comment.updated_at && (
              <span className="text-xs text-gray-400">(edited)</span>
            )}
          </div>
          <div className="flex gap-2">
            <button
              onClick={onReply}
              className="text-xs text-blue-600 hover:text-blue-800"
            >
              Reply
            </button>
            <button
              onClick={onDelete}
              className="text-xs text-red-600 hover:text-red-800"
            >
              Delete
            </button>
          </div>
        </div>
        <div className="text-gray-800 break-words">{comment.content}</div>
      </div>

      {/* Replies */}
      {replies.length > 0 && (
        <div className="mt-1">
          <button
            onClick={() => setExpanded(!expanded)}
            className="text-xs text-gray-500 hover:text-gray-700"
          >
            {expanded ? '─ Hide replies' : `─ Show ${replies.length} repl${replies.length > 1 ? 'ies' : 'y'}`}
          </button>
          {expanded && (
            <div className="ml-2 mt-1 space-y-1">
              {replies.map((reply) => (
                <CommentItem
                  key={reply.id}
                  comment={reply}
                  onReply={onReply}
                  onDelete={onDelete}
                />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
