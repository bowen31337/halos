/**
 * Tests for token estimation utilities
 */

import { estimateTokens, formatTokenCount, getLiveTokenDisplay, estimateCost } from './tokenUtils'

describe('tokenUtils', () => {
  describe('estimateTokens', () => {
    it('returns 0 for empty string', () => {
      expect(estimateTokens('')).toBe(0)
      expect(estimateTokens(null as any)).toBe(0)
      expect(estimateTokens(undefined as any)).toBe(0)
    })

    it('estimates tokens for simple text', () => {
      // 20 characters ≈ 5 tokens
      const result = estimateTokens('Hello, world!')
      expect(result).toBeGreaterThan(0)
      expect(result).toBeLessThan(10)
    })

    it('estimates tokens for longer text', () => {
      // 100 characters ≈ 25 tokens
      const text = 'This is a longer piece of text that should have more tokens. ' +
                   'It contains multiple sentences and should be estimated properly.'
      const result = estimateTokens(text)
      expect(result).toBeGreaterThan(20)
      expect(result).toBeLessThan(35)
    })

    it('adds overhead for markdown formatting', () => {
      const plain = 'Hello world'
      const withCode = '`Hello world`'
      const withBold = '**Hello world**'

      const plainTokens = estimateTokens(plain)
      const codeTokens = estimateTokens(withCode)
      const boldTokens = estimateTokens(withBold)

      // Code and bold should have higher estimates due to overhead
      expect(codeTokens).toBeGreaterThan(plainTokens)
      expect(boldTokens).toBeGreaterThan(plainTokens)
    })

    it('handles code blocks', () => {
      const code = '```javascript\nconst x = 1;\n```'
      const result = estimateTokens(code)
      expect(result).toBeGreaterThan(5)
    })

    it('handles newlines', () => {
      const text1 = 'line1\nline2\nline3'
      const text2 = 'line1line2line3'

      const result1 = estimateTokens(text1)
      const result2 = estimateTokens(text2)

      // Newlines add overhead
      expect(result1).toBeGreaterThan(result2)
    })

    it('handles JSON-like content', () => {
      const json = '{"key": "value", "number": 123}'
      const plain = 'key value number 123'

      const jsonTokens = estimateTokens(json)
      const plainTokens = estimateTokens(plain)

      // JSON should have higher overhead
      expect(jsonTokens).toBeGreaterThan(plainTokens)
    })
  })

  describe('formatTokenCount', () => {
    it('formats zero correctly', () => {
      expect(formatTokenCount(0)).toBe('0 tokens')
    })

    it('formats singular correctly', () => {
      expect(formatTokenCount(1)).toBe('1 token')
    })

    it('formats plural correctly', () => {
      expect(formatTokenCount(2)).toBe('2 tokens')
      expect(formatTokenCount(100)).toBe('100 tokens')
    })
  })

  describe('getLiveTokenDisplay', () => {
    it('returns zero for empty string', () => {
      expect(getLiveTokenDisplay('')).toBe('0 characters')
    })

    it('includes both character and token count', () => {
      const result = getLiveTokenDisplay('Hello, world!')
      expect(result).toContain('characters')
      expect(result).toContain('tokens')
      expect(result).toContain('~') // Token count is approximate
    })

    it('formats correctly for single token', () => {
      const result = getLiveTokenDisplay('Hi')
      expect(result).toContain('1 token')
    })

    it('formats correctly for multiple tokens', () => {
      const result = getLiveTokenDisplay('Hello, world! This is a test.')
      expect(result).toContain('tokens')
    })
  })

  describe('estimateCost', () => {
    it('returns 0 for zero tokens', () => {
      expect(estimateCost(0, 0)).toBe(0)
    })

    it('calculates cost for input tokens', () => {
      const cost = estimateCost(1000, 0, 'claude-sonnet')
      // Sonnet: $3 per 1M input tokens = $0.003 per 1K
      // 1000 tokens = $0.003
      expect(cost).toBeCloseTo(0.003, 4)
    })

    it('calculates cost for output tokens', () => {
      const cost = estimateCost(0, 1000, 'claude-sonnet')
      // Sonnet: $15 per 1M output tokens = $0.015 per 1K
      // 1000 tokens = $0.015
      expect(cost).toBeCloseTo(0.015, 4)
    })

    it('calculates combined cost', () => {
      const cost = estimateCost(1000, 1000, 'claude-sonnet')
      // 1000 input + 1000 output = $0.003 + $0.015 = $0.018
      expect(cost).toBeCloseTo(0.018, 4)
    })

    it('uses different pricing for different models', () => {
      const sonnetCost = estimateCost(1000, 1000, 'claude-sonnet')
      const opusCost = estimateCost(1000, 1000, 'claude-opus')

      // Opus is more expensive than Sonnet
      expect(opusCost).toBeGreaterThan(sonnetCost)
    })

    it('defaults to sonnet pricing for unknown models', () => {
      const cost = estimateCost(1000, 1000, 'unknown-model')
      expect(cost).toBeCloseTo(0.018, 4)
    })
  })
})
