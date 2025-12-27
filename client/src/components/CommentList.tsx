import { useState, useEffect } from 'react';
import { MessageSquare, Trash2, Reply, Send } from 'lucide-react';

interface Comment {
  id: string;
  message_id: string;
  conversation_id: string;
  user_id: string | null;
  anonymous_name: string | null;
  content: string;
  parent_comment_id: string | null;
  created_at: string;
  updated_at: string | null;
  replies: Comment[];
}

interface CommentListProps {
  shareToken: string;
  messageId: string;
  allowComments: boolean;
}

export function CommentList({ shareToken, messageId, allowComments }: CommentListProps) {
  const [comments, setComments] = useState<Comment[]>([]);
  const [newComment, setNewComment] = useState('');
  const [replyingTo, setReplyingTo] = useState<string | null>(null);
  const [replyContent, setReplyContent] = useState('');
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    loadComments();
  }, [shareToken, messageId]);

  const loadComments = async () => {
    try {
      const response = await fetch(`/api/comments/shared/${shareToken}/comments?message_id=${messageId}`);
      if (response.ok) {
        const data = await response.json();
        setComments(data);
      }
    } catch (err) {
      console.error('Failed to load comments:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleAddComment = async () => {
    if (!newComment.trim()) return;

    setSubmitting(true);
    try {
      const response = await fetch(`/api/comments/shared/${shareToken}/comments`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message_id: messageId,
          content: newComment,
        }),
      });

      if (response.ok) {
        setNewComment('');
        loadComments();
      }
    } catch (err) {
      console.error('Failed to add comment:', err);
    } finally {
      setSubmitting(false);
    }
  };

  const handleReply = async (parentId: string) => {
    if (!replyContent.trim()) return;

    setSubmitting(true);
    try {
      const response = await fetch(`/api/comments/shared/${shareToken}/comments`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message_id: messageId,
          content: replyContent,
          parent_comment_id: parentId,
        }),
      });

      if (response.ok) {
        setReplyContent('');
        setReplyingTo(null);
        loadComments();
      }
    } catch (err) {
      console.error('Failed to reply:', err);
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (commentId: string) => {
    if (!confirm('Delete this comment?')) return;

    try {
      const response = await fetch(`/api/comments/shared/${shareToken}/comments/${commentId}`, {
        method: 'DELETE',
      });

      if (response.ok) {
        loadComments();
      }
    } catch (err) {
      console.error('Failed to delete comment:', err);
    }
  };

  if (!allowComments) {
    return null;
  }

  if (loading) {
    return <div className="text-sm text-gray-500 py-2">Loading comments...</div>;
  }

  return (
    <div className="mt-2 border-t border-[var(--border)] pt-2">
      {/* Existing Comments */}
      {comments.length > 0 && (
        <div className="space-y-3 mb-3">
          {comments.map((comment) => (
            <CommentThread
              key={comment.id}
              comment={comment}
              onReply={setReplyingTo}
              onDelete={handleDelete}
              replyingTo={replyingTo}
              replyContent={replyContent}
              setReplyContent={setReplyContent}
              onSendReply={handleReply}
              submitting={submitting}
            />
          ))}
        </div>
      )}

      {/* Add Comment Input */}
      {!replyingTo && (
        <div className="flex gap-2">
          <input
            type="text"
            value={newComment}
            onChange={(e) => setNewComment(e.target.value)}
            placeholder="Add a comment..."
            className="flex-1 px-3 py-2 text-sm bg-[var(--bg-primary)] border border-[var(--border)] rounded focus:outline-none focus:border-[var(--primary)]"
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleAddComment();
              }
            }}
          />
          <button
            onClick={handleAddComment}
            disabled={submitting || !newComment.trim()}
            className="px-3 py-2 bg-[var(--primary)] text-white rounded hover:opacity-90 disabled:opacity-50"
          >
            <Send size={16} />
          </button>
        </div>
      )}
    </div>
  );
}

interface CommentThreadProps {
  comment: Comment;
  onReply: (id: string) => void;
  onDelete: (id: string) => void;
  replyingTo: string | null;
  replyContent: string;
  setReplyContent: (content: string) => void;
  onSendReply: (id: string) => void;
  submitting: boolean;
}

function CommentThread({
  comment,
  onReply,
  onDelete,
  replyingTo,
  replyContent,
  setReplyContent,
  onSendReply,
  submitting,
}: CommentThreadProps) {
  const timeAgo = new Date(comment.created_at).toLocaleString();

  return (
    <div className="space-y-2">
      <div className="bg-[var(--surface-secondary)] rounded-lg p-3 border border-[var(--border)]">
        <div className="flex items-start justify-between mb-1">
          <div className="flex items-center gap-2">
            <span className="font-medium text-sm text-[var(--text-primary)]">
              {comment.anonymous_name || 'User'}
            </span>
            <span className="text-xs text-[var(--text-secondary)]">{timeAgo}</span>
          </div>
          <div className="flex gap-1">
            <button
              onClick={() => onReply(comment.id)}
              className="p-1 hover:bg-[var(--bg-primary)] rounded text-[var(--text-secondary)]"
              title="Reply"
            >
              <Reply size={14} />
            </button>
            <button
              onClick={() => onDelete(comment.id)}
              className="p-1 hover:bg-red-100 dark:hover:bg-red-900/30 text-red-600 rounded"
              title="Delete"
            >
              <Trash2 size={14} />
            </button>
          </div>
        </div>
        <div className="text-sm text-[var(--text-primary)] whitespace-pre-wrap">
          {comment.content}
        </div>
      </div>

      {/* Reply Input */}
      {replyingTo === comment.id && (
        <div className="ml-6 flex gap-2">
          <input
            type="text"
            value={replyContent}
            onChange={(e) => setReplyContent(e.target.value)}
            placeholder="Write a reply..."
            className="flex-1 px-3 py-2 text-sm bg-[var(--bg-primary)] border border-[var(--border)] rounded focus:outline-none focus:border-[var(--primary)]"
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                onSendReply(comment.id);
              }
            }}
            autoFocus
          />
          <button
            onClick={() => onSendReply(comment.id)}
            disabled={submitting || !replyContent.trim()}
            className="px-3 py-2 bg-[var(--primary)] text-white rounded hover:opacity-90 disabled:opacity-50"
          >
            <Send size={14} />
          </button>
        </div>
      )}

      {/* Replies */}
      {comment.replies && comment.replies.length > 0 && (
        <div className="ml-6 space-y-2">
          {comment.replies.map((reply) => (
            <CommentThread
              key={reply.id}
              comment={reply}
              onReply={onReply}
              onDelete={onDelete}
              replyingTo={replyingTo}
              replyContent={replyContent}
              setReplyContent={setReplyContent}
              onSendReply={onSendReply}
              submitting={submitting}
            />
          ))}
        </div>
      )}
    </div>
  );
}
