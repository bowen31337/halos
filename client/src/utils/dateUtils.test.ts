import { describe, it, expect, beforeEach } from 'vitest'
import { formatTimestamp, getUserLocale, getUserTimezone } from '../utils/dateUtils'

describe('dateUtils', () => {
  beforeEach(() => {
    // Reset any global state
    jest.clearAllMocks()
  })

  describe('formatTimestamp', () => {
    const testDate = new Date('2025-03-15T14:30:00Z')

    it('should format timestamps with default locale', () => {
      const result = formatTimestamp(testDate)
      expect(result).toHaveProperty('relative')
      expect(result).toHaveProperty('short')
      expect(result).toHaveProperty('medium')
      expect(result).toHaveProperty('long')
      expect(result).toHaveProperty('full')
    })

    it('should format timestamps with specific locale', () => {
      const result = formatTimestamp(testDate, { locale: 'en-US' })
      expect(result).toHaveProperty('relative')
      expect(result).toHaveProperty('short')
      expect(result).toHaveProperty('medium')
      expect(result).toHaveProperty('long')
      expect(result).toHaveProperty('full')
    })

    it('should format timestamps with French locale', () => {
      const result = formatTimestamp(testDate, { locale: 'fr-FR' })
      expect(result).toHaveProperty('relative')
      expect(result).toHaveProperty('short')
      expect(result).toHaveProperty('medium')
      expect(result).toHaveProperty('long')
      expect(result).toHaveProperty('full')
    })

    it('should format timestamps with German locale', () => {
      const result = formatTimestamp(testDate, { locale: 'de-DE' })
      expect(result).toHaveProperty('relative')
      expect(result).toHaveProperty('short')
      expect(result).toHaveProperty('medium')
      expect(result).toHaveProperty('long')
      expect(result).toHaveProperty('full')
    })

    it('should format timestamps with Japanese locale', () => {
      const result = formatTimestamp(testDate, { locale: 'ja-JP' })
      expect(result).toHaveProperty('relative')
      expect(result).toHaveProperty('short')
      expect(result).toHaveProperty('medium')
      expect(result).toHaveProperty('long')
      expect(result).toHaveProperty('full')
    })

    it('should handle future dates correctly', () => {
      const futureDate = new Date()
      futureDate.setHours(futureDate.getHours() + 2) // 2 hours in the future

      const result = formatTimestamp(futureDate)
      expect(result.relative).toBe('In the future')
    })

    it('should show "Just now" for very recent timestamps', () => {
      const recentDate = new Date()
      recentDate.setSeconds(recentDate.getSeconds() - 30) // 30 seconds ago

      const result = formatTimestamp(recentDate)
      expect(result.relative).toBe('Just now')
    })

    it('should show minutes ago for recent timestamps', () => {
      const recentDate = new Date()
      recentDate.setMinutes(recentDate.getMinutes() - 5) // 5 minutes ago

      const result = formatTimestamp(recentDate)
      expect(result.relative).toBe('5 minutes ago')
    })

    it('should show hours ago for recent timestamps', () => {
      const recentDate = new Date()
      recentDate.setHours(recentDate.getHours() - 3) // 3 hours ago

      const result = formatTimestamp(recentDate)
      expect(result.relative).toBe('3 hours ago')
    })

    it('should show days ago for recent timestamps', () => {
      const recentDate = new Date()
      recentDate.setDate(recentDate.getDate() - 2) // 2 days ago

      const result = formatTimestamp(recentDate)
      expect(result.relative).toBe('2 days ago')
    })

    it('should show weeks ago for recent timestamps', () => {
      const recentDate = new Date()
      recentDate.setDate(recentDate.getDate() - 10) // 10 days ago

      const result = formatTimestamp(recentDate)
      expect(result.relative).toBe('1 week ago')
    })

    it('should show months ago for recent timestamps', () => {
      const recentDate = new Date()
      recentDate.setDate(recentDate.getDate() - 45) // 45 days ago

      const result = formatTimestamp(recentDate)
      expect(result.relative).toBe('1 month ago')
    })

    it('should show years ago for old timestamps', () => {
      const oldDate = new Date()
      oldDate.setFullYear(oldDate.getFullYear() - 2) // 2 years ago

      const result = formatTimestamp(oldDate)
      expect(result.relative).toBe('2 years ago')
    })

    it('should handle different timezones', () => {
      const result = formatTimestamp(testDate, { timezone: 'America/New_York' })
      expect(result).toHaveProperty('relative')
      expect(result).toHaveProperty('short')
      expect(result).toHaveProperty('medium')
      expect(result).toHaveProperty('long')
      expect(result).toHaveProperty('full')
    })

    it('should respect relative threshold', () => {
      const recentDate = new Date()
      recentDate.setHours(recentDate.getHours() - 25) // 25 hours ago, past default threshold

      const result = formatTimestamp(recentDate, { relativeThreshold: 24 })
      expect(result.relative).toBe('1 day ago')
    })
  })

  describe('getUserLocale', () => {
    it('should return a valid locale string', () => {
      const locale = getUserLocale()
      expect(typeof locale).toBe('string')
      expect(locale.length).toBeGreaterThan(0)
    })

    it('should handle missing navigator', () => {
      const originalNavigator = global.navigator
      delete (global as any).navigator

      const locale = getUserLocale()
      expect(locale).toBe('en-US')

      global.navigator = originalNavigator
    })
  })

  describe('getUserTimezone', () => {
    it('should return a valid timezone string', () => {
      const timezone = getUserTimezone()
      expect(typeof timezone).toBe('string')
      expect(timezone.length).toBeGreaterThan(0)
    })

    it('should handle missing Intl.DateTimeFormat', () => {
      const originalDateTimeFormat = global.Intl.DateTimeFormat
      delete (global as any).Intl.DateTimeFormat

      const timezone = getUserTimezone()
      expect(timezone).toBe('UTC')

      global.Intl.DateTimeFormat = originalDateTimeFormat
    })
  })

  describe('isSameDay', () => {
    it('should return true for same day', () => {
      const date1 = new Date('2025-03-15T10:00:00Z')
      const date2 = new Date('2025-03-15T15:30:00Z')

      expect(isSameDay(date1, date2)).toBe(true)
    })

    it('should return false for different days', () => {
      const date1 = new Date('2025-03-15T10:00:00Z')
      const date2 = new Date('2025-03-16T10:00:00Z')

      expect(isSameDay(date1, date2)).toBe(false)
    })
  })

  describe('isToday', () => {
    it('should return true for today', () => {
      const today = new Date()
      expect(isToday(today)).toBe(true)
    })

    it('should return false for yesterday', () => {
      const yesterday = new Date()
      yesterday.setDate(yesterday.getDate() - 1)

      expect(isToday(yesterday)).toBe(false)
    })
  })

  describe('isYesterday', () => {
    it('should return true for yesterday', () => {
      const yesterday = new Date()
      yesterday.setDate(yesterday.getDate() - 1)

      expect(isYesterday(yesterday)).toBe(true)
    })

    it('should return false for today', () => {
      const today = new Date()

      expect(isYesterday(today)).toBe(false)
    })
  })

  describe('formatForAccessibility', () => {
    it('should format date for screen readers', () => {
      const result = formatForAccessibility(testDate)
      expect(typeof result).toBe('string')
      expect(result.length).toBeGreaterThan(0)
    })

    it('should use provided locale', () => {
      const result = formatForAccessibility(testDate, 'fr-FR')
      expect(typeof result).toBe('string')
      expect(result.length).toBeGreaterThan(0)
    })

    it('should use default locale when none provided', () => {
      const result = formatForAccessibility(testDate)
      expect(typeof result).toBe('string')
      expect(result.length).toBeGreaterThan(0)
    })
  })
})

// Helper functions for testing (need to be exported for the tests to work)
export function isSameDay(date1: Date, date2: Date): boolean {
  return (
    date1.getFullYear() === date2.getFullYear() &&
    date1.getMonth() === date2.getMonth() &&
    date1.getDate() === date2.getDate()
  )
}

export function isToday(date: Date): boolean {
  return isSameDay(date, new Date())
}

export function isYesterday(date: Date): boolean {
  const yesterday = new Date()
  yesterday.setDate(yesterday.getDate() - 1)
  return isSameDay(date, yesterday)
}