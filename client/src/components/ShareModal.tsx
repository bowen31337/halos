import React, { useState, useEffect } from 'react';
import { X, Copy, Link, Clock, Globe, Lock, MessageSquare, Trash2 } from 'lucide-react';

interface ShareModalProps {
  conversationId: string;
  conversationTitle: string;
  onClose: () => void;
}

interface ShareSettings {
  access_level: 'read' | 'comment' | 'edit';
  allow_comments: boolean;
  expires_in_days: number | null;
}

interface ShareLink {
  id: string;
  share_token: string;  // Full URL for display
  token: string;        // Just the token for API calls
  access_level: string;
  allow_comments: boolean;
  expires_at: string | null;
  view_count: number;
  created_at: string;
}

export const ShareModal: React.FC<ShareModalProps> = ({ conversationId, conversationTitle, onClose }) => {
  const [settings, setSettings] = useState<ShareSettings>({
    access_level: 'read',
    allow_comments: false,
    expires_in_days: null,
  });
  const [shareLink, setShareLink] = useState<ShareLink | null>(null);
  const [existingShares, setExistingShares] = useState<ShareLink[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingShares, setIsLoadingShares] = useState(true);
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load existing shares on mount
  useEffect(() => {
    loadExistingShares();
  }, [conversationId]);

  const loadExistingShares = async () => {
    setIsLoadingShares(true);
    try {
      const response = await fetch(`/api/conversations/${conversationId}/shares`);
      if (response.ok) {
        const data = await response.json();
        // Transform data to include both full URL and token
        const transformed = data.map((item: any) => ({
          ...item,
          share_token: `${window.location.origin}/share/${item.share_token}`,
          token: item.share_token,
        }));
        setExistingShares(transformed);
      }
    } catch (err) {
      console.error('Failed to load shares:', err);
    } finally {
      setIsLoadingShares(false);
    }
  };

  const generateShareLink = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`/api/conversations/${conversationId}/share`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(settings),
      });

      if (!response.ok) {
        throw new Error(`Failed to create share link: ${response.statusText}`);
      }

      const data = await response.json();
      const fullLink = `${window.location.origin}/share/${data.share_token}`;
      const newShare = { ...data, share_token: fullLink, token: data.share_token };

      // Store the new share and refresh the list
      setShareLink(newShare);
      setExistingShares(prev => [newShare, ...prev]);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setIsLoading(false);
    }
  };

  const copyToClipboard = async () => {
    if (!shareLink) return;

    try {
      await navigator.clipboard.writeText(shareLink.share_token);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      // Fallback for older browsers
      const textArea = document.createElement('textarea');
      textArea.value = shareLink.share_token;
      document.body.appendChild(textArea);
      textArea.select();
      document.execCommand('copy');
      document.body.removeChild(textArea);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const revokeLink = async () => {
    if (!shareLink) return;

    try {
      await fetch(`/api/conversations/share/${shareLink.token}`, {
        method: 'DELETE',
      });
      setShareLink(null);
      // Remove from existing shares
      setExistingShares(prev => prev.filter(s => s.token !== shareLink.token));
    } catch (err) {
      setError('Failed to revoke link');
    }
  };

  const revokeExistingShare = async (token: string) => {
    try {
      await fetch(`/api/conversations/share/${token}`, {
        method: 'DELETE',
      });
      // Remove from existing shares
      setExistingShares(prev => prev.filter(s => s.token !== token));
    } catch (err) {
      setError('Failed to revoke link');
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={onClose}>
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl w-full max-w-md p-6" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Share Conversation</h2>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">{conversationTitle}</p>
          </div>
          <button onClick={onClose} className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded">
            <X size={20} />
          </button>
        </div>

        {/* Error Message */}
        {error && (
          <div className="mb-4 p-3 bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300 rounded text-sm">
            {error}
          </div>
        )}

        {/* Settings Form */}
        <div className="space-y-4">
            {/* Access Level */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                <Globe size={16} className="inline mr-2" />
                Access Level
              </label>
              <div className="grid grid-cols-3 gap-2">
                {[
                  { value: 'read', label: 'Read Only', icon: Lock },
                  { value: 'comment', label: 'Comment', icon: MessageSquare },
                  { value: 'edit', label: 'Edit', icon: Globe },
                ].map(({ value, label, icon: Icon }) => (
                  <button
                    key={value}
                    onClick={() => setSettings({ ...settings, access_level: value as any })}
                    className={`p-2 rounded border text-sm flex items-center justify-center gap-1 ${
                      settings.access_level === value
                        ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300'
                        : 'border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700'
                    }`}
                  >
                    <Icon size={14} />
                    {label}
                  </button>
                ))}
              </div>
            </div>

            {/* Allow Comments */}
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                <MessageSquare size={16} className="inline mr-2" />
                Allow Comments
              </label>
              <input
                type="checkbox"
                checked={settings.allow_comments}
                onChange={(e) => setSettings({ ...settings, allow_comments: e.target.checked })}
                className="w-4 h-4 text-blue-600 rounded"
              />
            </div>

            {/* Expiration */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                <Clock size={16} className="inline mr-2" />
                Expiration (days, optional)
              </label>
              <input
                type="number"
                min="1"
                placeholder="Never expires"
                value={settings.expires_in_days ?? ''}
                onChange={(e) => setSettings({
                  ...settings,
                  expires_in_days: e.target.value ? parseInt(e.target.value) : null
                })}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              />
            </div>

            {/* Generate Button */}
            <button
              onClick={generateShareLink}
              disabled={isLoading}
              className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2.5 rounded flex items-center justify-center gap-2 disabled:opacity-50"
            >
              <Link size={18} />
              {isLoading ? 'Generating...' : 'Generate Share Link'}
            </button>

            {/* Existing Shares */}
            {!isLoadingShares && existingShares.length > 0 && (
              <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-600">
                <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Existing Shares ({existingShares.length})</p>
                <div className="space-y-2 max-h-48 overflow-y-auto">
                  {existingShares.map((share) => (
                    <div key={share.id} className="bg-gray-50 dark:bg-gray-700/50 p-2 rounded border border-gray-200 dark:border-gray-600 text-xs">
                      <div className="flex items-center justify-between mb-1">
                        <span className="font-medium capitalize">{share.access_level}</span>
                        <span className="text-gray-500">{share.view_count} views</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <code className="flex-1 truncate bg-white dark:bg-gray-800 px-1 py-0.5 rounded border border-gray-200 dark:border-gray-600">
                          {share.share_token}
                        </code>
                        <button
                          onClick={() => navigator.clipboard.writeText(share.share_token)}
                          className="p-1 hover:bg-gray-200 dark:hover:bg-gray-600 rounded"
                          title="Copy"
                        >
                          <Copy size={12} />
                        </button>
                        <button
                          onClick={() => revokeExistingShare(share.token)}
                          className="p-1 hover:bg-red-100 dark:hover:bg-red-900/30 text-red-600 rounded"
                          title="Revoke"
                        >
                          <Trash2 size={12} />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

        {/* Share Link Display */}
        {shareLink && (
          <div className="space-y-4 mt-4 pt-4 border-t border-gray-200 dark:border-gray-600">
            <div className="bg-gray-50 dark:bg-gray-700/50 p-4 rounded-lg border border-gray-200 dark:border-gray-600">
              <div className="flex items-start gap-2">
                <Link size={18} className="mt-1 text-blue-600" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 dark:text-white mb-1">New Share Link</p>
                  <div className="flex items-center gap-2">
                    <code className="text-xs bg-white dark:bg-gray-800 px-2 py-1 rounded border border-gray-200 dark:border-gray-600 truncate flex-1">
                      {shareLink.share_token}
                    </code>
                    <button
                      onClick={copyToClipboard}
                      className="p-2 hover:bg-gray-200 dark:hover:bg-gray-600 rounded"
                      title="Copy link"
                    >
                      <Copy size={16} />
                    </button>
                  </div>
                </div>
              </div>

              {/* Status Info */}
              <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-600 grid grid-cols-2 gap-2 text-xs">
                <div>
                  <span className="text-gray-500">Access:</span>{' '}
                  <span className="font-medium capitalize">{shareLink.access_level}</span>
                </div>
                <div>
                  <span className="text-gray-500">Views:</span>{' '}
                  <span className="font-medium">{shareLink.view_count}</span>
                </div>
                {shareLink.expires_at && (
                  <div className="col-span-2">
                    <span className="text-gray-500">Expires:</span>{' '}
                    <span className="font-medium">
                      {new Date(shareLink.expires_at).toLocaleDateString()}
                    </span>
                  </div>
                )}
              </div>
            </div>

            {/* Copied Indicator */}
            {copied && (
              <div className="text-center text-sm text-green-600 dark:text-green-400 py-2">
                ✓ Copied to clipboard!
              </div>
            )}

            {/* Actions */}
            <div className="flex gap-2">
              <button
                onClick={generateShareLink}
                className="flex-1 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-900 dark:text-white font-medium py-2 rounded"
              >
                Generate New Link
              </button>
              <button
                onClick={revokeLink}
                className="flex-1 bg-red-600 hover:bg-red-700 text-white font-medium py-2 rounded"
              >
                Revoke Link
              </button>
            </div>

            {/* Share Instructions */}
            <div className="text-xs text-gray-500 dark:text-gray-400 bg-blue-50 dark:bg-blue-900/20 p-3 rounded">
              <p className="font-medium mb-1">How to use:</p>
              <ol className="list-decimal list-inside space-y-1">
                <li>Copy the link above</li>
                <li>Share with anyone you want</li>
                <li>Recipients can view without logging in</li>
              </ol>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
