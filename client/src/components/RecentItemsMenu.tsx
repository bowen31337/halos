import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useRecentItemsStore } from '../stores/recentItemsStore'
import { useConversationStore } from '../stores/conversationStore'

interface RecentItemsMenuProps {
  isOpen: boolean
  onClose: () => void
  position?: { top: number; right: number }
}

export function RecentItemsMenu({ isOpen, onClose, position }: RecentItemsMenuProps) {
  const { items, clearRecentItems, removeRecentItem } = useRecentItemsStore()
  const { setCurrentConversationId } = useConversationStore()
  const navigate = useNavigate()
  const [filterType, setFilterType] = useState<'all' | 'conversation' | 'file' | 'project'>('all')

  // Filter items by type
  const filteredItems = filterType === 'all'
    ? items
    : items.filter(item => item.type === filterType)

  // Format timestamp
  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp)
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

  // Get icon for item type
  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'conversation':
        return '💬'
      case 'file':
        return '📄'
      case 'project':
        return '📁'
      default:
        return '📌'
    }
  }

  // Handle clicking a recent item
  const handleItemClick = (item: any) => {
    if (item.type === 'conversation') {
      setCurrentConversationId(item.id)
      navigate(`/conversation/${item.id}`)
    } else if (item.type === 'project') {
      navigate(`/project/${item.id}`)
    } else if (item.type === 'file' && item.metadata?.path) {
      // Could open file in panel or navigate
      navigate(`/file/${item.metadata.path}`)
    }
    onClose()
  }

  // Handle remove individual item
  const handleRemoveItem = (e: React.MouseEvent, id: string) => {
    e.stopPropagation()
    removeRecentItem(id)
  }

  // Handle clear all
  const handleClearAll = () => {
    if (confirm('Clear all recent items?')) {
      clearRecentItems()
    }
  }

  if (!isOpen) return null

  const menuStyle: React.CSSProperties = {
    position: 'absolute',
    top: position?.top || '100%',
    right: position?.right || 0,
    marginTop: '8px',
    zIndex: 1000,
  }

  return (
    <div
      className="recent-items-menu"
      style={menuStyle}
    >
      <div className="recent-items-backdrop" onClick={onClose}>
        <div
          className="recent-items-dropdown"
          onClick={(e) => e.stopPropagation()}
          style={{
            background: 'var(--bg-primary)',
            border: '1px solid var(--border-color)',
            borderRadius: '8px',
            boxShadow: '0 4px 20px rgba(0, 0, 0, 0.15)',
            width: '380px',
            maxHeight: '600px',
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden',
          }}
        >
          {/* Header */}
          <div
            className="recent-items-header"
            style={{
              padding: '12px 16px',
              borderBottom: '1px solid var(--border-color)',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
            }}
          >
            <h3
              style={{
                margin: 0,
                fontSize: '15px',
                fontWeight: 600,
                color: 'var(--text-primary)',
              }}
            >
              Recent Items
            </h3>
            {items.length > 0 && (
              <button
                onClick={handleClearAll}
                style={{
                  background: 'transparent',
                  border: 'none',
                  color: 'var(--text-secondary)',
                  fontSize: '13px',
                  cursor: 'pointer',
                  padding: '4px 8px',
                  borderRadius: '4px',
                }}
                onMouseEnter={(e) => e.currentTarget.style.background = 'var(--bg-hover)'}
                onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
              >
                Clear All
              </button>
            )}
          </div>

          {/* Filter Tabs */}
          {items.length > 0 && (
            <div
              className="recent-items-filters"
              style={{
                padding: '8px 16px',
                display: 'flex',
                gap: '8px',
                borderBottom: '1px solid var(--border-color)',
              }}
            >
              {(['all', 'conversation', 'file', 'project'] as const).map((type) => {
                const count = type === 'all'
                  ? items.length
                  : items.filter(i => i.type === type).length

                return (
                  <button
                    key={type}
                    onClick={() => setFilterType(type)}
                    disabled={count === 0}
                    style={{
                      background: filterType === type ? 'var(--accent-color)' : 'transparent',
                      border: filterType === type ? 'none' : '1px solid var(--border-color)',
                      color: filterType === type ? 'white' : 'var(--text-secondary)',
                      fontSize: '12px',
                      padding: '4px 10px',
                      borderRadius: '12px',
                      cursor: count === 0 ? 'not-allowed' : 'pointer',
                      opacity: count === 0 ? 0.4 : 1,
                      textTransform: 'capitalize',
                    }}
                  >
                    {type === 'all' ? 'All' : type} ({count})
                  </button>
                )
              })}
            </div>
          )}

          {/* Items List */}
          <div
            className="recent-items-list"
            style={{
              flex: 1,
              overflowY: 'auto',
              padding: filteredItems.length > 0 ? '8px' : '24px',
            }}
          >
            {filteredItems.length === 0 ? (
              <div
                className="recent-items-empty"
                style={{
                  textAlign: 'center',
                  color: 'var(--text-secondary)',
                }}
              >
                <div style={{ fontSize: '48px', marginBottom: '12px' }}>🕐</div>
                <p style={{ margin: 0, fontSize: '14px' }}>
                  {items.length === 0 ? 'No recent items yet' : `No ${filterType} items yet`}
                </p>
                <p style={{ margin: '8px 0 0', fontSize: '12px', opacity: 0.7 }}>
                  Items you view will appear here
                </p>
              </div>
            ) : (
              <div className="recent-items" style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                {filteredItems.map((item) => (
                  <div
                    key={item.id}
                    className="recent-item"
                    onClick={() => handleItemClick(item)}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '12px',
                      padding: '10px 12px',
                      borderRadius: '6px',
                      cursor: 'pointer',
                      transition: 'background 0.15s ease',
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.background = 'var(--bg-hover)'
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.background = 'transparent'
                    }}
                  >
                    {/* Icon */}
                    <div
                      className="recent-item-icon"
                      style={{
                        fontSize: '20px',
                        flexShrink: 0,
                      }}
                    >
                      {getTypeIcon(item.type)}
                    </div>

                    {/* Content */}
                    <div
                      className="recent-item-content"
                      style={{
                        flex: 1,
                        minWidth: 0,
                      }}
                    >
                      <div
                        className="recent-item-title"
                        style={{
                          fontSize: '14px',
                          fontWeight: 500,
                          color: 'var(--text-primary)',
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          whiteSpace: 'nowrap',
                        }}
                      >
                        {item.title}
                      </div>
                      {item.subtitle && (
                        <div
                          className="recent-item-subtitle"
                          style={{
                            fontSize: '12px',
                            color: 'var(--text-secondary)',
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                            whiteSpace: 'nowrap',
                          }}
                        >
                          {item.subtitle}
                        </div>
                      )}
                      <div
                        className="recent-item-time"
                        style={{
                          fontSize: '11px',
                          color: 'var(--text-tertiary)',
                          marginTop: '2px',
                        }}
                      >
                        {formatTimestamp(item.timestamp)}
                      </div>
                    </div>

                    {/* Remove button */}
                    <button
                      onClick={(e) => handleRemoveItem(e, item.id)}
                      style={{
                        background: 'transparent',
                        border: 'none',
                        color: 'var(--text-tertiary)',
                        cursor: 'pointer',
                        padding: '4px',
                        borderRadius: '4px',
                        opacity: 0,
                        transition: 'opacity 0.15s ease',
                      }}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.opacity = '1'
                        e.currentTarget.style.color = 'var(--text-secondary)'
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.opacity = '0'
                        e.currentTarget.style.color = 'var(--text-tertiary)'
                      }}
                      className="recent-item-remove"
                    >
                      ✕
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Footer */}
          {items.length > 0 && (
            <div
              className="recent-items-footer"
              style={{
                padding: '10px 16px',
                borderTop: '1px solid var(--border-color)',
                fontSize: '12px',
                color: 'var(--text-tertiary)',
                textAlign: 'center',
              }}
            >
              Showing {filteredItems.length} of {items.length} items
            </div>
          )}
        </div>
      </div>

      <style>{`
        .recent-item:hover .recent-item-remove {
          opacity: 0.6 !important;
        }
        .recent-item-remove:hover {
          opacity: 1 !important;
          color: var(--text-primary) !important;
        }
      `}</style>
    </div>
  )
}
