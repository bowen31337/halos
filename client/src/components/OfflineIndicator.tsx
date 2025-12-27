import React from 'react'
import { useNetworkStore } from '../stores/networkStore'

/**
 * OfflineIndicator Component
 *
 * Displays a banner when the application is offline
 * Shows number of queued actions waiting to sync
 */
export const OfflineIndicator: React.FC = () => {
  const { isOffline, actionQueue } = useNetworkStore()

  if (!isOffline) {
    return null
  }

  const queuedCount = actionQueue.length

  return (
    <div
      className="offline-indicator"
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        backgroundColor: '#f59e0b',
        color: '#1a1a1a',
        padding: '12px 16px',
        textAlign: 'center',
        fontWeight: 500,
        zIndex: 9999,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: '8px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
      }}
    >
      <svg
        width="20"
        height="20"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
      >
        <path d="M1 1l22 22" />
        <path d="M16.72 11.06A10.94 10.94 0 0 1 19 12.55M5 12.55a10.94 10.94 0 0 1 5.17-2.39M10.71 5.05A16 16 0 0 1 22.58 9M1.42 9a15.91 15.91 0 0 1 4.7-2.88M8.53 16.11a6 6 0 0 1 6.95 0M12 20h.01" />
      </svg>
      <span>
        You are offline. {queuedCount > 0 && `${queuedCount} action${queuedCount > 1 ? 's are' : ' is'} queued to sync.`}
      </span>
      <style>{`
        .offline-indicator {
          animation: slideDown 0.3s ease-out;
        }
        @keyframes slideDown {
          from {
            transform: translateY(-100%);
            opacity: 0;
          }
          to {
            transform: translateY(0);
            opacity: 1;
          }
        }
      `}</style>
    </div>
  )
}
