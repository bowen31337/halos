/**
 * Token estimation utilities for live token count display
 *
 * Uses a simple approximation: tokens ≈ characters / 4
 * This is a rough estimate for display purposes only.
 * For more accurate estimates, the backend would need to calculate actual tokens.
 */

/**
 * Estimate the number of tokens for a given text string.
 *
 * This uses a simple character-based approximation:
 * - 1 token ≈ 4 characters for English text
 * - Adds overhead for special characters and formatting
 *
 * @param text - The text to estimate tokens for
 * @returns Estimated token count (integer)
 */
export function estimateTokens(text: string): number {
  if (!text || text.length === 0) return 0

  // Basic approximation: 1 token per 4 characters
  // This is conservative and works well for English text
  const baseEstimate = Math.ceil(text.length / 4)

  // Add overhead for common formatting patterns
  let overhead = 0

  // Markdown formatting overhead
  const markdownPatterns = [
    { regex: /```/g, weight: 2 },      // Code blocks
    { regex: /`/g, weight: 1 },        // Inline code
    { regex: /\*\*/g, weight: 1 },     // Bold
    { regex: /__/g, weight: 1 },       // Bold (underscore)
    { regex: /\*/g, weight: 0.5 },     // Italic
    { regex: /_/g, weight: 0.5 },      // Italic (underscore)
    { regex: /#/g, weight: 1 },        // Headers
    { regex: />/g, weight: 0.5 },      // Blockquotes
    { regex: /\n/g, weight: 0.25 },    // Newlines
    { regex: /\t/g, weight: 0.5 },     // Tabs
  ]

  for (const pattern of markdownPatterns) {
    const matches = text.match(pattern.regex)
    if (matches) {
      overhead += matches.length * pattern.weight
    }
  }

  // JSON/structured data overhead
  if (text.includes('{') || text.includes('[') || text.includes('"')) {
    overhead += Math.ceil(text.length * 0.05) // 5% overhead for JSON-like content
  }

  return Math.ceil(baseEstimate + overhead)
}

/**
 * Format token count for display
 *
 * @param tokens - Token count
 * @returns Formatted string like "123 tokens" or "~123 tokens"
 */
export function formatTokenCount(tokens: number): string {
  if (tokens === 0) return '0 tokens'
  return `${tokens} token${tokens !== 1 ? 's' : ''}`
}

/**
 * Estimate tokens and return formatted display string
 *
 * @param text - Text to estimate
 * @returns Formatted string like "45 chars • ~12 tokens"
 */
export function getLiveTokenDisplay(text: string): string {
  const chars = text.length
  const tokens = estimateTokens(text)

  if (chars === 0) return '0 characters'

  return `${chars} characters • ~${tokens} token${tokens !== 1 ? 's' : ''}`
}

/**
 * Estimate cost based on token usage (for display purposes)
 *
 * @param inputTokens - Input token count
 * @param outputTokens - Output token count
 * @param model - Model name (e.g., 'claude-sonnet')
 * @returns Estimated cost in USD
 */
export function estimateCost(inputTokens: number, outputTokens: number, model: string = 'claude-sonnet'): number {
  // Approximate pricing per 1K tokens (as of 2024)
  // These are rough estimates for display purposes
  const pricing: Record<string, { input: number; output: number }> = {
    'claude-opus': { input: 0.015, output: 0.075 },    // $15/$75 per 1M
    'claude-sonnet': { input: 0.003, output: 0.015 },  // $3/$15 per 1M
    'claude-haiku': { input: 0.00025, output: 0.00125 }, // $0.25/$1.25 per 1M
  }

  const pricingData = pricing[model] || pricing['claude-sonnet']

  const inputCost = (inputTokens / 1000) * pricingData.input
  const outputCost = (outputTokens / 1000) * pricingData.output

  return inputCost + outputCost
}
