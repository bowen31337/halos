import React, { useEffect, useRef, useState } from 'react'
import { useCollaborationStore } from '../stores/collaborationStore'
import { useConversationStore } from '../stores/conversationStore'

interface CollaborationCursorsProps {
  containerRef: React.RefObject<HTMLElement>
}

export const CollaborationCursors: React.FC<CollaborationCursorsProps> = ({ containerRef }) => {
  const {
    isConnected,
    isConnecting,
    collaborators,
    connect,
    disconnect,
    sendCursor,
    currentUserId,
    currentUserName,
    setUserName
  } = useCollaborationStore()
  const { currentConversation } = useConversationStore()
  const [cursorPositions, setCursorPositions] = useState<Map<string, { x: number; y: number; color: string; name: string }>>(new Map())
  const [showPanel, setShowPanel] = useState(false)
  const [showNameInput, setShowNameInput] = useState(false)
  const [tempName, setTempName] = useState(currentUserName)
  const lastCursorUpdate = useRef<Map<string, number>>(new Map())

  // Auto-connect when conversation is active
  useEffect(() => {
    if (currentConversation?.id && currentUserId) {
      connect(currentConversation.id, currentUserId, currentUserName)
    }

    return () => {
      disconnect()
    }
  }, [currentConversation?.id])

  // Track cursor position and send updates (throttled)
  useEffect(() => {
    const container = containerRef.current
    if (!container || !isConnected) return

    const handleMouseMove = (e: MouseEvent) => {
      const now = Date.now()
      const lastUpdate = lastCursorUpdate.current.get('self') || 0

      // Throttle to 50ms
      if (now - lastUpdate < 50) return

      const rect = container.getBoundingClientRect()
      const x = e.clientX - rect.left
      const y = e.clientY - rect.top

      sendCursor({ x, y })
      lastCursorUpdate.current.set('self', now)
    }

    container.addEventListener('mousemove', handleMouseMove)
    return () => container.removeEventListener('mousemove', handleMouseMove)
  }, [isConnected, containerRef, sendCursor])

  // Update cursor positions from collaborators
  useEffect(() => {
    const newPositions = new Map<string, { x: number; y: number; color: string; name: string }>()

    collaborators.forEach((collaborator, userId) => {
      if (collaborator.cursor) {
        newPositions.set(userId, {
          x: collaborator.cursor.x,
          y: collaborator.cursor.y,
          color: collaborator.color,
          name: collaborator.name
        })
      }
    })

    setCursorPositions(newPositions)
  }, [collaborators])

  const handleNameSave = () => {
    if (tempName.trim()) {
      setUserName(tempName.trim())
      setShowNameInput(false)
      // Reconnect with new name
      if (currentConversation?.id) {
        disconnect()
        setTimeout(() => {
          connect(currentConversation.id, currentUserId, tempName.trim())
        }, 100)
      }
    }
  }

  if (!currentConversation?.id) {
    return null
  }

  return (
    <div className="collaboration-cursors">
      {/* Connection status indicator */}
      <div
        className="connection-indicator"
        style={{
          position: 'fixed',
          top: '70px',
          right: '20px',
          background: 'rgba(255, 255, 255, 0.95)',
          backdropFilter: 'blur(10px)',
          border: '1px solid #e0e0e0',
          borderRadius: '8px',
          padding: '8px 12px',
          boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
          zIndex: 9999,
          cursor: 'pointer',
          transition: 'all 0.2s',
          minWidth: '120px'
        }}
        onClick={() => setShowPanel(!showPanel)}
        title={isConnected ? 'Collaboration active' : isConnecting ? 'Connecting...' : 'Click to connect'}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div style={{
              width: '8px',
              height: '8px',
              borderRadius: '50%',
              background: isConnected ? '#10b981' : isConnecting ? '#f59e0b' : '#ef4444',
              animation: (isConnected || isConnecting) ? 'pulse 2s infinite' : 'none'
            }}></div>
            <span style={{ fontWeight: 600, fontSize: '13px' }}>
              {isConnected ? `${collaborators.size} ${collaborators.size === 1 ? 'user' : 'users'}` : isConnecting ? 'Connecting...' : 'Offline'}
            </span>
          </div>
          {isConnected && (
            <span style={{ fontSize: '11px', color: '#666' }}>
              {currentUserName}
            </span>
          )}
        </div>

        {showPanel && isConnected && (
          <div style={{ marginTop: '8px', borderTop: '1px solid #e0e0e0', paddingTop: '8px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
              <span style={{ fontWeight: 600, fontSize: '12px' }}>Active Users</span>
              <button
                onClick={(e) => { e.stopPropagation(); setShowNameInput(!showNameInput) }}
                style={{
                  background: 'none',
                  border: 'none',
                  color: '#3b82f6',
                  cursor: 'pointer',
                  fontSize: '11px',
                  padding: '2px 4px'
                }}
              >
                Change name
              </button>
            </div>

            {showNameInput && (
              <div style={{ marginBottom: '8px' }}>
                <input
                  type="text"
                  value={tempName}
                  onChange={(e) => setTempName(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') handleNameSave()
                    if (e.key === 'Escape') setShowNameInput(false)
                  }}
                  placeholder="Your name"
                  style={{
                    width: '100%',
                    padding: '4px 6px',
                    border: '1px solid #ccc',
                    borderRadius: '4px',
                    fontSize: '12px'
                  }}
                  autoFocus
                />
              </div>
            )}

            {Array.from(collaborators.values()).map((c) => (
              <div key={c.userId} style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '4px 0',
                fontSize: '12px'
              }}>
                <div style={{
                  width: '10px',
                  height: '10px',
                  borderRadius: '50%',
                  background: c.color
                }}></div>
                <span>{c.name}</span>
                {c.cursor && (
                  <span style={{ color: '#666', fontSize: '10px' }}>• typing...</span>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Cursor indicators */}
      {isConnected && Array.from(cursorPositions.entries()).map(([userId, pos]) => (
        <div
          key={userId}
          className="collaborator-cursor"
          style={{
            position: 'absolute',
            left: `${pos.x}px`,
            top: `${pos.y}px`,
            pointerEvents: 'none',
            zIndex: 10000
          }}
        >
          {/* Cursor arrow */}
          <svg
            width="20"
            height="20"
            viewBox="0 0 20 20"
            style={{ transform: 'translate(-2px, -2px)' }}
          >
            <path
              d="M0 0 L0 16 L4 12 L7 18 L9 17 L6 10 L12 10 Z"
              fill={pos.color}
              stroke="white"
              strokeWidth="1"
            />
          </svg>

          {/* Name label */}
          <div
            style={{
              position: 'absolute',
              left: '16px',
              top: '16px',
              background: pos.color,
              color: 'white',
              padding: '2px 6px',
              borderRadius: '4px',
              fontSize: '11px',
              whiteSpace: 'nowrap',
              fontWeight: 'bold',
              boxShadow: '0 2px 4px rgba(0,0,0,0.2)'
            }}
          >
            {pos.name}
          </div>
        </div>
      ))}

      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.5; }
        }
      `}</style>
    </div>
  )
}

export default CollaborationCursors
