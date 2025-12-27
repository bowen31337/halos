import { useState } from 'react'
import { useUIStore } from '../stores/uiStore'

interface ComparisonModalProps {
  isOpen: boolean
  onClose: () => void
  tempComparisonModels: string[]
  setTempComparisonModels: (models: string[]) => void
  onConfirm: () => void
}

const MODELS = [
  {
    id: 'claude-sonnet-4-5-20250929',
    name: 'Claude Sonnet 4.5',
    description: 'Balanced',
  },
  {
    id: 'claude-haiku-4-5-20251001',
    name: 'Claude Haiku 4.5',
    description: 'Fast',
  },
  {
    id: 'claude-opus-4-1-20250805',
    name: 'Claude Opus 4.1',
    description: 'Most capable',
  },
]

export function ComparisonModal({ isOpen, onClose, tempComparisonModels, setTempComparisonModels, onConfirm }: ComparisonModalProps) {
  const [step, setStep] = useState(1) // 1 = select first model, 2 = select second model

  if (!isOpen) return null

  const handleModelSelect = (modelId: string) => {
    if (step === 1) {
      setTempComparisonModels([modelId, tempComparisonModels[1] || ''])
      setStep(2)
    } else {
      // Ensure we don't select the same model twice
      if (modelId === tempComparisonModels[0]) {
        alert('Please select a different model for comparison')
        return
      }
      setTempComparisonModels([tempComparisonModels[0], modelId])
      onConfirm()
    }
  }

  const getAvailableModels = () => {
    if (step === 1) {
      return MODELS
    }
    // Filter out the first selected model
    return MODELS.filter(m => m.id !== tempComparisonModels[0])
  }

  const currentSelection = step === 1 ? tempComparisonModels[0] : tempComparisonModels[1]

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm" onClick={onClose}>
      <div className="bg-[var(--bg-primary)] border border-[var(--border-primary)] rounded-lg shadow-xl p-6 w-full max-w-md mx-4" onClick={(e) => e.stopPropagation()}>
        <h2 className="text-xl font-bold text-[var(--text-primary)] mb-2">
          {step === 1 ? 'Select First Model' : 'Select Second Model'}
        </h2>
        <p className="text-sm text-[var(--text-secondary)] mb-4">
          {step === 1
            ? 'Choose the first model to compare'
            : `Comparing against: ${MODELS.find(m => m.id === tempComparisonModels[0])?.name}`}
        </p>

        <div className="space-y-2 max-h-[60vh] overflow-y-auto">
          {getAvailableModels().map((model) => (
            <button
              key={model.id}
              onClick={() => handleModelSelect(model.id)}
              className={`w-full text-left px-4 py-3 rounded-lg border transition-colors ${
                currentSelection === model.id
                  ? 'bg-[var(--primary)] text-white border-[var(--primary)]'
                  : 'bg-[var(--surface-elevated)] hover:bg-[var(--bg-secondary)] border-[var(--border-primary)] text-[var(--text-primary)]'
              }`}
            >
              <div className="font-medium">{model.name}</div>
              <div className="text-xs opacity-75">{model.description}</div>
            </button>
          ))}
        </div>

        <div className="flex gap-2 mt-4">
          <button
            onClick={onClose}
            className="flex-1 px-4 py-2 bg-[var(--surface-elevated)] hover:bg-[var(--bg-secondary)] rounded-lg text-[var(--text-primary)] transition-colors"
          >
            Cancel
          </button>
          {step === 2 && (
            <button
              onClick={() => setStep(1)}
              className="px-4 py-2 bg-[var(--surface-elevated)] hover:bg-[var(--bg-secondary)] rounded-lg text-[var(--text-primary)] transition-colors"
            >
              Back
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
