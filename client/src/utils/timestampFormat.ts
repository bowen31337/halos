/**
 * Timestamp formatting utilities with locale support.
 */

export interface TimestampSettings {
  locale?: string
  timeFormat?: '12h' | '24h'
  dateFormat?: 'MM/DD/YYYY' | 'DD/MM/YYYY' | 'YYYY-MM-DD'
  relativeTime?: boolean
}

/**
 * Format a timestamp according to user locale and format preferences.
 */
export function formatTimestamp(
  timestamp: string | Date,
  settings: TimestampSettings = {}
): string {
  const date = typeof timestamp === 'string' ? new Date(timestamp) : timestamp
  const now = new Date()

  const {
    locale = 'en-US',
    timeFormat = '12h',
    dateFormat = 'MM/DD/YYYY',
    relativeTime = true
  } = settings

  // Check if we should show relative time
  if (relativeTime) {
    const diffMs = now.getTime() - date.getTime()
    const diffSeconds = Math.floor(diffMs / 1000)
    const diffMinutes = Math.floor(diffSeconds / 60)
    const diffHours = Math.floor(diffMinutes / 60)
    const diffDays = Math.floor(diffHours / 24)

    if (diffSeconds < 60) return 'just now'
    if (diffMinutes < 60) return `${diffMinutes}m ago`
    if (diffHours < 24) return `${diffHours}h ago`
    if (diffDays < 7) return `${diffDays}d ago`
  }

  // Format date based on user preference
  const dateOptions: Intl.DateTimeFormatOptions = {
    year: 'numeric',
    month: dateFormat === 'YYYY-MM-DD' ? '2-digit' : '2-digit',
    day: '2-digit',
  }

  // Format time based on user preference
  const timeOptions: Intl.DateTimeFormatOptions = {
    hour: '2-digit',
    minute: '2-digit',
    hour12: timeFormat === '12h',
  }

  const dateStr = new Intl.DateTimeFormat(locale, dateOptions).format(date)
  const timeStr = new Intl.DateTimeFormat(locale, timeOptions).format(date)

  // Reorder date based on format preference
  let formattedDate = dateStr
  if (dateFormat === 'YYYY-MM-DD') {
    const parts = dateStr.split('/')
    // For locale formats that return MM/DD/YYYY, convert to YYYY-MM-DD
    if (parts.length === 3) {
      const [m, d, y] = parts
      formattedDate = `${y}-${m}-${d}`
    }
  } else if (dateFormat === 'DD/MM/YYYY') {
    const parts = dateStr.split('/')
    if (parts.length === 3) {
      const [m, d, y] = parts
      formattedDate = `${d}/${m}/${y}`
    }
  }

  return `${formattedDate} ${timeStr}`
}

/**
 * Get relative time string (e.g., "5 minutes ago", "2 hours ago").
 */
export function getRelativeTime(timestamp: string | Date): string {
  const date = typeof timestamp === 'string' ? new Date(timestamp) : timestamp
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()

  const diffSeconds = Math.floor(diffMs / 1000)
  const diffMinutes = Math.floor(diffSeconds / 60)
  const diffHours = Math.floor(diffMinutes / 60)
  const diffDays = Math.floor(diffHours / 24)
  const diffWeeks = Math.floor(diffDays / 7)
  const diffMonths = Math.floor(diffDays / 30)
  const diffYears = Math.floor(diffDays / 365)

  if (diffSeconds < 5) return 'just now'
  if (diffSeconds < 60) return `${diffSeconds}s ago`
  if (diffMinutes < 60) return `${diffMinutes}m ago`
  if (diffHours < 24) return `${diffHours}h ago`
  if (diffDays < 7) return `${diffDays}d ago`
  if (diffWeeks < 52) return `${diffWeeks}w ago`
  if (diffMonths < 12) return `${diffMonths}mo ago`
  return `${diffYears}y ago`
}

/**
 * Format date in a specific format.
 */
export function formatDate(
  timestamp: string | Date,
  format: 'short' | 'medium' | 'long' | 'iso' = 'short',
  locale: string = 'en-US'
): string {
  const date = typeof timestamp === 'string' ? new Date(timestamp) : timestamp

  switch (format) {
    case 'iso':
      return date.toISOString()
    case 'long':
      return new Intl.DateTimeFormat(locale, {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      }).format(date)
    case 'medium':
      return new Intl.DateTimeFormat(locale, {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      }).format(date)
    case 'short':
    default:
      return new Intl.DateTimeFormat(locale, {
        month: '2-digit',
        day: '2-digit',
        year: 'numeric',
      }).format(date)
  }
}

/**
 * Format time only.
 */
export function formatTime(
  timestamp: string | Date,
  timeFormat: '12h' | '24h' = '12h',
  locale: string = 'en-US'
): string {
  const date = typeof timestamp === 'string' ? new Date(timestamp) : timestamp

  return new Intl.DateTimeFormat(locale, {
    hour: '2-digit',
    minute: '2-digit',
    hour12: timeFormat === '12h',
  }).format(date)
}

/**
 * Check if a timestamp is today.
 */
export function isToday(timestamp: string | Date): boolean {
  const date = typeof timestamp === 'string' ? new Date(timestamp) : timestamp
  const today = new Date()

  return (
    date.getDate() === today.getDate() &&
    date.getMonth() === today.getMonth() &&
    date.getFullYear() === today.getFullYear()
  )
}

/**
 * Check if a timestamp is yesterday.
 */
export function isYesterday(timestamp: string | Date): boolean {
  const date = typeof timestamp === 'string' ? new Date(timestamp) : timestamp
  const yesterday = new Date()
  yesterday.setDate(yesterday.getDate() - 1)

  return (
    date.getDate() === yesterday.getDate() &&
    date.getMonth() === yesterday.getMonth() &&
    date.getFullYear() === yesterday.getFullYear()
  )
}

/**
 * Get the date group label for sidebar organization.
 */
export function getDateGroup(timestamp: string | Date): string {
  if (isToday(timestamp)) return 'Today'
  if (isYesterday(timestamp)) return 'Yesterday'
  return 'Previous'
}
