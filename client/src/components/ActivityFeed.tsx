import React, { useEffect, useState } from 'react'
import { api } from '../services/api'

interface Activity {
  id: string
  user_id: string
  user_name: string
  action_type: string
  resource_type?: string
  resource_id?: string
  resource_name?: string
  details?: any
  created_at: string
}

interface ActivityFeedProps {
  onClose: () => void
}

export const ActivityFeed: React.FC<ActivityFeedProps> = ({ onClose }) => {
  const [activities, setActivities] = useState<Activity[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState({
    action_type: '',
    resource_type: '',
    time_range: '7d'
  })
  const [activityTypes, setActivityTypes] = useState<string[]>([])
  const [resourceTypes, setResourceTypes] = useState<string[]>([])

  useEffect(() => {
    fetchActivities()
    fetchActivityTypes()
  }, [filter])

  const fetchActivities = async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams()
      if (filter.action_type) params.append('action_type', filter.action_type)
      if (filter.resource_type) params.append('resource_type', filter.resource_type)
      if (filter.time_range) params.append('time_range', filter.time_range)
      params.append('limit', '50')

      const response = await fetch(`/api/activity?${params.toString()}`)
      if (response.ok) {
        const data = await response.json()
        setActivities(data.activities || [])
      }
    } catch (error) {
      console.error('Failed to fetch activities:', error)
    } finally {
      setLoading(false)
    }
  }

  const fetchActivityTypes = async () => {
    try {
      const response = await fetch('/api/activity/types')
      if (response.ok) {
        const data = await response.json()
        setActivityTypes(data.action_types?.map((t: any) => t.type) || [])
        setResourceTypes(data.resource_types?.map((t: any) => t.type) || [])
      }
    } catch (error) {
      console.error('Failed to fetch activity types:', error)
    }
  }

  const formatAction = (action: string) => {
    const words = action.split('_')
    return words.map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')
  }

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp)
    const now = new Date()
    const diff = now.getTime() - date.getTime()
    const minutes = Math.floor(diff / 60000)
    const hours = Math.floor(minutes / 60)
    const days = Math.floor(hours / 24)

    if (days > 0) return `${days}d ago`
    if (hours > 0) return `${hours}h ago`
    if (minutes > 0) return `${minutes}m ago`
    return 'Just now'
  }

  const getActionColor = (action: string) => {
    if (action.includes('create')) return '#10b981'
    if (action.includes('delete')) return '#ef4444'
    if (action.includes('update') || action.includes('edit')) return '#3b82f6'
    if (action.includes('share')) return '#8b5cf6'
    return '#6b7280'
  }

  return (
    <div className="activity-feed-overlay" style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      background: 'rgba(0, 0, 0, 0.5)',
      zIndex: 10000,
      display: 'flex',
      justifyContent: 'flex-end'
    }} onClick={onClose}>
      <div
        className="activity-feed-panel"
        style={{
          width: '400px',
          maxWidth: '90vw',
          height: '100vh',
          background: 'white',
          boxShadow: '-4px 0 12px rgba(0,0,0,0.1)',
          overflowY: 'auto',
          display: 'flex',
          flexDirection: 'column'
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div style={{
          padding: '20px',
          borderBottom: '1px solid #e0e0e0',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <h2 style={{ margin: 0, fontSize: '20px', fontWeight: 600 }}>Activity Feed</h2>
          <button
            onClick={onClose}
            style={{
              background: 'none',
              border: 'none',
              fontSize: '24px',
              cursor: 'pointer',
              padding: '0 8px'
            }}
          >
            ×
          </button>
        </div>

        {/* Filters */}
        <div style={{
          padding: '16px',
          borderBottom: '1px solid #e0e0e0',
          background: '#f9fafb'
        }}>
          <div style={{ display: 'flex', gap: '8px', marginBottom: '8px' }}>
            <select
              value={filter.time_range}
              onChange={(e) => setFilter({ ...filter, time_range: e.target.value })}
              style={{ flex: 1, padding: '6px', borderRadius: '4px', border: '1px solid #ccc' }}
            >
              <option value="1d">Last 24h</option>
              <option value="7d">Last 7 days</option>
              <option value="30d">Last 30 days</option>
              <option value="all">All time</option>
            </select>
          </div>

          <div style={{ display: 'flex', gap: '8px' }}>
            <select
              value={filter.action_type}
              onChange={(e) => setFilter({ ...filter, action_type: e.target.value })}
              style={{ flex: 1, padding: '6px', borderRadius: '4px', border: '1px solid #ccc' }}
            >
              <option value="">All Actions</option>
              {activityTypes.map(type => (
                <option key={type} value={type}>{formatAction(type)}</option>
              ))}
            </select>

            <select
              value={filter.resource_type}
              onChange={(e) => setFilter({ ...filter, resource_type: e.target.value })}
              style={{ flex: 1, padding: '6px', borderRadius: '4px', border: '1px solid #ccc' }}
            >
              <option value="">All Resources</option>
              {resourceTypes.map(type => (
                <option key={type} value={type}>{formatAction(type)}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Activity List */}
        <div style={{ flex: 1, overflowY: 'auto' }}>
          {loading ? (
            <div style={{ padding: '40px', textAlign: 'center', color: '#666' }}>
              Loading...
            </div>
          ) : activities.length === 0 ? (
            <div style={{ padding: '40px', textAlign: 'center', color: '#666' }}>
              No activities found
            </div>
          ) : (
            <div>
              {activities.map((activity) => (
                <div
                  key={activity.id}
                  style={{
                    padding: '16px',
                    borderBottom: '1px solid #f0f0f0',
                    cursor: 'pointer',
                    transition: 'background 0.2s'
                  }}
                  onMouseEnter={(e) => e.currentTarget.style.background = '#f9fafb'}
                  onMouseLeave={(e) => e.currentTarget.style.background = 'white'}
                  onClick={() => {
                    if (activity.resource_id && activity.resource_type === 'conversation') {
                      // Navigate to conversation
                      window.location.hash = `#/conversation/${activity.resource_id}`
                    }
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                    <span style={{ fontWeight: 600, fontSize: '13px' }}>
                      {activity.user_name || 'Unknown'}
                    </span>
                    <span style={{ fontSize: '11px', color: '#999' }}>
                      {formatTime(activity.created_at)}
                    </span>
                  </div>

                  <div style={{ fontSize: '13px', marginBottom: '4px' }}>
                    <span style={{
                      color: getActionColor(activity.action_type),
                      fontWeight: 500
                    }}>
                      {formatAction(activity.action_type)}
                    </span>
                    {activity.resource_name && (
                      <span> "{activity.resource_name}"</span>
                    )}
                  </div>

                  {activity.resource_type && (
                    <div style={{ fontSize: '11px', color: '#666' }}>
                      {formatAction(activity.resource_type)}
                      {activity.resource_id && ` • ${activity.resource_id.slice(0, 8)}...`}
                    </div>
                  )}

                  {activity.details && Object.keys(activity.details).length > 0 && (
                    <div style={{ fontSize: '11px', color: '#666', marginTop: '4px', fontStyle: 'italic' }}>
                      {JSON.stringify(activity.details)}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div style={{
          padding: '12px',
          borderTop: '1px solid #e0e0e0',
          fontSize: '12px',
          color: '#666',
          textAlign: 'center'
        }}>
          {activities.length} activities
        </div>
      </div>
    </div>
  )
}

export default ActivityFeed
