import { useConversationStore } from '../stores/conversationStore'

const suggestions = [
  {
    title: 'Help me write',
    description: 'An email, essay, or story',
    icon: '✍️',
    prompt: 'Help me write an email'
  },
  {
    title: 'Explain a topic',
    description: 'From quantum physics to history',
    icon: '💡',
    prompt: 'Explain quantum computing in simple terms'
  },
  {
    title: 'Help me code',
    description: 'Debug or write new features',
    icon: '💻',
    prompt: 'Help me debug this Python code'
  },
  {
    title: 'Analyze data',
    description: 'Find patterns and insights',
    icon: '📊',
    prompt: 'Analyze this data and find patterns'
  }
]

export function WelcomeScreen() {
  const { setInputMessage } = useConversationStore()

  const handleSuggestion = (prompt: string) => {
    setInputMessage(prompt)
  }

  return (
    <div className="h-full flex flex-col items-center justify-center p-8">
      <div className="max-w-2xl w-full">
        <h1 className="text-3xl font-semibold text-[var(--text-primary)] mb-2 text-center">
          How can I help you today?
        </h1>
        <p className="text-[var(--text-secondary)] text-center mb-12">
          Start a new conversation or choose from the suggestions below
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {suggestions.map((suggestion) => (
            <button
              key={suggestion.title}
              onClick={() => handleSuggestion(suggestion.prompt)}
              className="flex items-start gap-4 p-4 rounded-lg border border-[var(--border-primary)] hover:border-[var(--border-hover)] hover:bg-[var(--surface-elevated)] transition-colors text-left group"
            >
              <span className="text-2xl">{suggestion.icon}</span>
              <div>
                <h3 className="font-medium text-[var(--text-primary)] group-hover:text-[var(--primary)] transition-colors">
                  {suggestion.title}
                </h3>
                <p className="text-sm text-[var(--text-secondary)]">
                  {suggestion.description}
                </p>
              </div>
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
