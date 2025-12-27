import { useConversationStore } from '../stores/conversationStore'
import { ComparisonMessageList } from './ComparisonMessageList'
import { useUIStore } from '../stores/uiStore'
import { MODELS } from './Header'

export function ComparisonView() {
  const { messages } = useConversationStore()
  const { comparisonModels } = useUIStore()

  // Get model info for display
  const leftModel = MODELS.find(m => m.id === comparisonModels[0]) || MODELS[0]
  const rightModel = MODELS.find(m => m.id === comparisonModels[1]) || MODELS[1]

  // Filter messages for comparison view
  // In comparison mode, messages are stored with model tags
  // We need to show user messages once, and assistant messages split by model
  const comparisonMessages = messages.filter(m =>
    m.role === 'user' ||
    (m.role === 'assistant' && m.comparisonGroup)
  )

  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* Header showing model comparison */}
      <div className="border-b border-[var(--border-primary)] bg-[var(--surface-secondary)] p-3">
        <div className="flex gap-4 justify-center">
          <div className="flex items-center gap-2 px-3 py-1.5 bg-[var(--surface-elevated)] rounded">
            <div
              className="w-2 h-2 rounded-full"
              style={{ backgroundColor: '#CC785C' }}
            ></div>
            <span className="font-medium text-sm">{leftModel.name}</span>
            <span className="text-xs text-[var(--text-secondary)]">({leftModel.description})</span>
          </div>
          <div className="text-[var(--text-secondary)] text-sm flex items-center font-semibold">vs</div>
          <div className="flex items-center gap-2 px-3 py-1.5 bg-[var(--surface-elevated)] rounded">
            <div
              className="w-2 h-2 rounded-full"
              style={{ backgroundColor: comparisonModels[1] === 'claude-haiku-4-5-20251001' ? '#5CC8CC' : '#785CCC' }}
            ></div>
            <span className="font-medium text-sm">{rightModel.name}</span>
            <span className="text-xs text-[var(--text-secondary)]">({rightModel.description})</span>
          </div>
        </div>
      </div>

      {/* Comparison message list */}
      <div className="flex-1 overflow-y-auto">
        <ComparisonMessageList messages={comparisonMessages} />
      </div>
    </div>
  )
}
