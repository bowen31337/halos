export function ThinkingIndicator() {
  return (
    <div className="mb-6">
      <div className="flex items-center gap-2 text-[var(--text-secondary)]">
        <div className="loading-dots">
          <span></span>
          <span></span>
          <span></span>
        </div>
        <span className="text-sm">Thinking...</span>
      </div>
    </div>
  )
}
