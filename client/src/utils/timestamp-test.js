/**
 * Simple verification script for timestamp formatting
 * Run this in the browser console to verify locale-aware timestamp formatting
 */

// Mock the dateUtils functions for browser testing
function formatTimestamp(date, options = {}) {
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
  const commonOptions = {
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

function getRelativeTime(date, diffHours, locale) {
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

// Test function
function testTimestampFormatting() {
  console.log('🧪 Testing Timestamp Formatting with Different Locales')
  console.log('='.repeat(60))

  const testDate = new Date('2025-03-15T14:30:00Z')
  const recentDate = new Date()
  recentDate.setMinutes(recentDate.getMinutes() - 5)

  const locales = ['en-US', 'en-GB', 'fr-FR', 'de-DE', 'es-ES', 'ja-JP']

  locales.forEach(locale => {
    console.log(`\n🌍 Testing ${locale}:`)
    console.log('-'.repeat(40))

    const result = formatTimestamp(testDate, { locale })
    console.log('📅 Test Date (2025-03-15):')
    console.log(`   Relative: ${result.relative}`)
    console.log(`   Short: ${result.short}`)
    console.log(`   Medium: ${result.medium}`)
    console.log(`   Long: ${result.long}`)
    console.log(`   Full: ${result.full}`)

    const recentResult = formatTimestamp(recentDate, { locale })
    console.log('⏰ Recent Date (5 minutes ago):')
    console.log(`   Relative: ${recentResult.relative}`)
    console.log(`   Short: ${recentResult.short}`)
  })

  console.log('\n✅ Timestamp formatting test completed!')
  console.log('Check the console output above for locale-specific formatting.')
}

// Run the test when this script is loaded
testTimestampFormatting()