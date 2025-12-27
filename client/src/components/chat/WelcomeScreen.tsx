
import { useConversationStore } from '../../stores/conversationStore'

const suggestions = [
  { title: 'Help me write a Python script', prompt: 'Help me write a Python script to automate file organization' },
  { title: 'Explain a concept', prompt: 'Explain quantum computing in simple terms' },
  { title: 'Code review', prompt: 'Review this code for bugs and best practices' },
  { title: 'Brainstorm ideas', prompt: 'Help me brainstorm marketing ideas for a coffee shop' },
]

export function WelcomeScreen() {
  const { } = useConversationStore()

  const handleSuggestion = (prompt: string) => {
    setInputMessage(prompt)
  }

  return (
    <div className="flex flex-col items-center justify-center h-full px-4">
      <div className="max-w-2xl w-full">
        <h1 className="text-3xl font-semibold mb-8 text-center">
          How can I help you today?
        </h1>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {suggestions.map((suggestion, index) => (
            <button
              key={index}
              onClick={() => handleSuggestion(suggestion.prompt)}
              className="text-left p-4 rounded-lg border border-[var(--border)] hover:bg-[var(--surface-elevated)] transition-colors"
            >
              <div className="font-medium text-sm">{suggestion.title}</div>
            </button>
          ))}
        </div>

        <div className="mt-8 text-center text-sm text-[var(--text-secondary)]">
          <p>Claude can make mistakes. Please verify important information.</p>
        </div>
      </div>
    </div>
  )
}
