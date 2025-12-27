interface SuggestedFollowUpsProps {
  suggestions: string[]
  onSuggestionClick: (suggestion: string) => void
}

export function SuggestedFollowUps({ suggestions, onSuggestionClick }: SuggestedFollowUpsProps) {
  if (!suggestions || suggestions.length === 0) {
    return null
  }

  return (
    <div className="mt-4 space-y-2">
      <div className="flex items-center gap-2 text-sm text-[var(--text-secondary)]">
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
        </svg>
        <span>Suggested follow-ups</span>
      </div>
      <div className="flex flex-wrap gap-2">
        {suggestions.map((suggestion, index) => (
          <button
            key={index}
            onClick={() => onSuggestionClick(suggestion)}
            className="px-3 py-2 text-sm text-left bg-[var(--surface-elevated)] hover:bg-[var(--bg-primary)] border border-[var(--border-secondary)] rounded-lg transition-colors text-[var(--text-primary)] max-w-xs"
            title={suggestion}
          >
            <span className="line-clamp-2">{suggestion}</span>
          </button>
        ))}
      </div>
    </div>
  )
}
