/**
 * Timestamp formatting utilities for locale-aware date handling
 */

export interface LocaleOptions {
  locale?: string
  timezone?: string
  relativeThreshold?: number // Hours threshold for showing relative time
}

export interface TimestampFormats {
  relative: string
  short: string
  medium: string
  long: string
  full: string
}

/**
 * Format a date with locale awareness
 */
export function formatTimestamp(
  date: Date | string,
  options: LocaleOptions = {}
): TimestampFormats {
  const {
    locale = 'en-US',
    timezone = Intl.DateTimeFormat().resolvedOptions().timeZone,
    relativeThreshold = 24
  } = options

  const dateObj = typeof date === 'string' ? new Date(date) : date
  const now = new Date()

  // Calculate time difference in hours
  const diffMs = now.getTime() - dateObj.getTime()
  const diffHours = diffMs / (1000 * 60 * 60)

  // If date is in the future, don't show relative time
  const isFuture = diffHours < 0

  // Options for different format levels
  const commonOptions: Intl.DateTimeFormatOptions = {
    timeZone: timezone,
  }

  const relativeFormat = getRelativeTime(dateObj, diffHours, locale)

  const shortFormat = new Intl.DateTimeFormat(locale, {
    ...commonOptions,
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(dateObj)

  const mediumFormat = new Intl.DateTimeFormat(locale, {
    ...commonOptions,
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(dateObj)

  const longFormat = new Intl.DateTimeFormat(locale, {
    ...commonOptions,
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    weekday: 'short',
  }).format(dateObj)

  const fullFormat = new Intl.DateTimeFormat(locale, {
    ...commonOptions,
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    weekday: 'long',
    timeZoneName: 'short',
  }).format(dateObj)

  return {
    relative: isFuture ? 'In the future' : relativeFormat,
    short: shortFormat,
    medium: mediumFormat,
    long: longFormat,
    full: fullFormat,
  }
}

/**
 * Get relative time string (e.g., "5 minutes ago", "2 hours ago", "3 days ago")
 */
function getRelativeTime(date: Date, diffHours: number, locale: string): string {
  // Use absolute value since we already checked for future dates
  const diffAbsHours = Math.abs(diffHours)
  const diffDays = diffAbsHours / 24

  // Less than 1 minute
  if (diffAbsHours < 1/60) {
    return 'Just now'
  }

  // Less than 1 hour
  if (diffAbsHours < 1) {
    const minutes = Math.floor(diffAbsHours * 60)
    return `${minutes} minute${minutes === 1 ? '' : 's'} ago`
  }

  // Less than 24 hours
  if (diffAbsHours < 24) {
    const hours = Math.floor(diffAbsHours)
    return `${hours} hour${hours === 1 ? '' : 's'} ago`
  }

  // Less than 7 days
  if (diffDays < 7) {
    const days = Math.floor(diffDays)
    return `${days} day${days === 1 ? '' : 's'} ago`
  }

  // Less than 30 days
  if (diffDays < 30) {
    const weeks = Math.floor(diffDays / 7)
    return `${weeks} week${weeks === 1 ? '' : 's'} ago`
  }

  // Less than 365 days
  if (diffDays < 365) {
    const months = Math.floor(diffDays / 30)
    return `${months} month${months === 1 ? '' : 's'} ago`
  }

  // More than 1 year
  const years = Math.floor(diffDays / 365)
  return `${years} year${years === 1 ? '' : 's'} ago`
}

/**
 * Get user's preferred locale
 */
export function getUserLocale(): string {
  // Try to get from navigator
  if (typeof navigator !== 'undefined') {
    return navigator.language || 'en-US'
  }
  return 'en-US'
}

/**
 * Get user's preferred timezone
 */
export function getUserTimezone(): string {
  try {
    return Intl.DateTimeFormat().resolvedOptions().timeZone
  } catch {
    return 'UTC'
  }
}

/**
 * Check if two dates are on the same day
 */
export function isSameDay(date1: Date, date2: Date): boolean {
  return (
    date1.getFullYear() === date2.getFullYear() &&
    date1.getMonth() === date2.getMonth() &&
    date1.getDate() === date2.getDate()
  )
}

/**
 * Check if date is today
 */
export function isToday(date: Date): boolean {
  return isSameDay(date, new Date())
}

/**
 * Check if date is yesterday
 */
export function isYesterday(date: Date): boolean {
  const yesterday = new Date()
  yesterday.setDate(yesterday.getDate() - 1)
  return isSameDay(date, yesterday)
}

/**
 * Format date for accessibility (screen readers)
 */
export function formatForAccessibility(date: Date | string, locale?: string): string {
  const localeToUse = locale || getUserLocale()
  const dateObj = typeof date === 'string' ? new Date(date) : date

  return new Intl.DateTimeFormat(localeToUse, {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    hour12: true,
    timeZoneName: 'short',
  }).format(dateObj)
}