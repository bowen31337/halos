import React, { useEffect, useRef, useState } from 'react'
import { useCollaborationStore } from '../stores/collaborationStore'
import { useConversationStore } from '../stores/conversationStore'
import { useAuthStore } from '../stores/authStore'

interface CollaborationCursorsProps {
  containerRef: React.RefObject<HTMLElement>
}

export const CollaborationCursors: React.FC<CollaborationCursorsProps> = ({ containerRef }) => {
  const { isConnected, collaborators, connect, disconnect, sendCursor } = useCollaborationStore()
  const { currentConversation } = useConversationStore()
  const { user } = useAuthStore()
  const [cursorPositions, setCursorPositions] = useState<Map<string, { x: number; y: number; color: string; name: string }>>(new Map())
  const [showPanel, setShowPanel] = useState(false)
  const lastCursorUpdate = useRef<Map<string, number>>(new Map())

  // Auto-connect when conversation is active
  useEffect(() => {
    if (currentConversation?.id && user?.id) {
      connect(currentConversation.id, user.id, user.name || 'Anonymous')
    }

    return () => {
      disconnect()
    }
  }, [currentConversation?.id, user?.id])

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

  if (!isConnected || cursorPositions.size === 0) {
    return null
  }

  return (
    <div className="collaboration-cursors">
      {/* Cursor indicators */}
      {Array.from(cursorPositions.entries()).map(([userId, pos]) => (
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

      {/* Collaborator indicator panel */}
      <div
        className="collaborator-panel"
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
          transition: 'all 0.2s'
        }}
        onClick={() => setShowPanel(!showPanel)}
        title="Active collaborators"
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div style={{
            width: '8px',
            height: '8px',
            borderRadius: '50%',
            background: '#10b981',
            animation: 'pulse 2s infinite'
          }}></div>
          <span style={{ fontWeight: 600, fontSize: '13px' }}>
            {collaborators.size} {collaborators.size === 1 ? 'user' : 'users'}
          </span>
        </div>

        {showPanel && (
          <div style={{ marginTop: '8px', borderTop: '1px solid #e0e0e0', paddingTop: '8px' }}>
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
