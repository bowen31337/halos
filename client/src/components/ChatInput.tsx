import { useState, useRef, useEffect } from 'react'
import { useConversationStore } from '../stores/conversationStore'
import { useUIStore } from '../stores/uiStore'
import { useProjectStore } from '../stores/projectStore'
import { useArtifactStore } from '../stores/artifactStore'
import { useChatStore } from '../stores/chatStore'
import { useNetworkStore, QueuedAction } from '../stores/networkStore'
import { api } from '../services/api'
import { v4 as uuidv4 } from 'uuid'
import { HITLApprovalDialog } from './HITLApprovalDialog'
import { getLiveTokenDisplay } from '../utils/tokenUtils'

interface ImageAttachment {
  id: string
  url: string
  file: File
  preview: string
}

interface HITLPendingApproval {
  threadId: string
  tool: string
  input: any
  reason: string
}

export function ChatInput() {
  const {
    isStreaming,
    isLoading,
    addMessage,
    appendToLastMessage,
    setStreaming,
    setLoading,
    currentConversationId,
    createConversation,
    inputMessage: storeInputMessage,
    setInputMessage
  } = useConversationStore()

  const {
    extendedThinkingEnabled,
    customInstructions,
    temperature,
    maxTokens,
    permissionMode,
    memoryEnabled,
    comparisonMode,
    comparisonModels,
    setPanelOpen,
    setPanelType
  } = useUIStore()

  const { detectArtifacts } = useArtifactStore()
  const { isOffline, queueAction, actionQueue } = useNetworkStore()

  // Use local state for immediate UI feedback, sync with store
  const [inputValue, setInputValue] = useState(storeInputMessage)
  const [images, setImages] = useState<ImageAttachment[]>([])
  const [isDragOver, setIsDragOver] = useState(false)
  const [hitlApproval, setHitlApproval] = useState<HITLPendingApproval | null>(null)
  const [isRecording, setIsRecording] = useState(false)
  const [recognition, setRecognition] = useState<SpeechRecognition | SpeechRecognition | null>(null)
  const [recordingText, setRecordingText] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const abortControllerRef = useRef<AbortController | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  // Store the message that triggered an interrupt so we can resume after approval
  const interruptedMessageRef = useRef<string>('')
  // Voice input state
  const [isListening, setIsListening] = useState(false)
  const [isSpeechRecognitionSupported, setIsSpeechRecognitionSupported] = useState(false)
  const recognitionRef = useRef<any>(null)

  // Sync with store when it changes (e.g., from WelcomeScreen)
  useEffect(() => {
    if (storeInputMessage && storeInputMessage !== inputValue) {
      setInputValue(storeInputMessage)
      // Clear the store message after syncing
      setInputMessage('')
    }
  }, [storeInputMessage, inputValue, setInputMessage])

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 200) + 'px'
    }
  }, [inputValue])

  // Initialize speech recognition
  useEffect(() => {
    // Check for browser support
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    if (SpeechRecognition) {
      setIsSpeechRecognitionSupported(true)
      const recognitionInstance = new SpeechRecognition()
      recognitionInstance.continuous = true
      recognitionInstance.interimResults = true
      recognitionInstance.lang = 'en-US'

      recognitionInstance.onresult = (event) => {
        let finalTranscript = ''
        let interimTranscript = ''

        for (let i = event.resultIndex; i < event.results.length; i++) {
          const result = event.results[i]
          const transcript = result[0].transcript

          if (result.isFinal) {
            finalTranscript += transcript
          } else {
            interimTranscript += transcript
          }
        }

        // Update recording text with both final and interim results
        const currentText = finalTranscript || interimTranscript
        setRecordingText(currentText)
        setInputValue(currentText)

        // Also update the store
        setInputMessage(currentText)
      }

      recognitionInstance.onend = () => {
        setIsRecording(false)
        setRecordingText('')
      }

      recognitionInstance.onerror = (event) => {
        console.error('Speech recognition error:', event.error)
        setIsRecording(false)
        setRecordingText('')
        alert(`Speech recognition error: ${event.error}`)
      }

      recognitionRef.current = recognitionInstance
    }
  }, [setInputMessage])

  // Handle recording state changes
  useEffect(() => {
    if (recognitionRef.current && isListening) {
      recognitionRef.current.start()
    } else if (recognitionRef.current && !isListening) {
      recognitionRef.current.stop()
    }
  }, [isListening])

  // Listen for prompt content from PromptModal
  useEffect(() => {
    const handleUsePrompt = (event: CustomEvent) => {
      const content = event.detail.content
      setInputValue(content)
      // Also update the store
      setInputMessage(content)
      // Focus the textarea
      setTimeout(() => textareaRef.current?.focus(), 100)
    }

    window.addEventListener('usePrompt', handleUsePrompt as EventListener)
    return () => {
      window.removeEventListener('usePrompt', handleUsePrompt as EventListener)
    }
  }, [setInputMessage])

  // Helper function to stream from a single model
  const streamFromModel = async (
    model: string,
    message: string,
    convId: string,
    abortController: AbortController,
    messageId: string,
    comparisonGroup?: string
  ) => {
    const { appendToMessage, appendToThinking, updateMessage, addMessage } = useConversationStore.getState()
    const { addArtifact } = useArtifactStore.getState()
    const { setPanelType, setPanelOpen } = useUIStore.getState()
    const { setTodos, setFiles } = useChatStore.getState()

    // Get project-specific custom instructions
    const { conversations } = useConversationStore.getState()
    const { projects } = useProjectStore.getState()
    const currentConversation = conversations.find(c => c.id === convId)
    const projectInstructions = currentConversation?.projectId
      ? projects.find(p => p.id === currentConversation.projectId)?.custom_instructions
      : null

    // Use project instructions if available, otherwise use global custom instructions
    const effectiveInstructions = projectInstructions || customInstructions

    // Prepare message with custom instructions if set
    let finalMessage = message
    if (effectiveInstructions.trim()) {
      finalMessage = `[System Instructions: ${effectiveInstructions}]\n\n${message}`
    }

    let fullAssistantContent = ''
    let fullThinkingContent = ''
    let currentToolCall: { toolName: string; toolInput: Record<string, unknown> } | null = null

    try {
      // Call the backend SSE API
      const response = await fetch('/api/agent/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: finalMessage,
          conversationId: convId,
          thread_id: convId,
          extended_thinking: extendedThinkingEnabled,
          temperature: temperature,
          max_tokens: maxTokens,
          custom_instructions: effectiveInstructions,
          model: model,
          permission_mode: permissionMode,
          memory_enabled: memoryEnabled,
        }),
        signal: abortController.signal,
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const reader = response.body?.getReader()
      if (!reader) {
        throw new Error('No response body')
      }

      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        let currentEvent: string | null = null
        let currentData: string | null = null

        for (const line of lines) {
          const trimmed = line.trim()

          if (trimmed.startsWith('event:')) {
            currentEvent = trimmed.slice(6).trim()
          } else if (trimmed.startsWith('data:')) {
            currentData = trimmed.slice(5).trim()
          } else if (trimmed === '') {
            if (currentEvent && currentData) {
              try {
                const eventData = JSON.parse(currentData)

                switch (currentEvent) {
                  case 'message':
                    if (eventData.content) {
                      appendToMessage(messageId, eventData.content)
                      fullAssistantContent += eventData.content
                    }
                    break
                  case 'thinking':
                    if (eventData.content) {
                      fullThinkingContent += eventData.content
                      appendToThinking(messageId, eventData.content)
                    }
                    break
                  case 'tool_start':
                    currentToolCall = {
                      toolName: eventData.tool,
                      toolInput: eventData.input,
                    }
                    break
                  case 'tool_end':
                    if (currentToolCall) {
                      addMessage({
                        id: `tool-${Date.now()}`,
                        conversationId: convId,
                        role: 'tool',
                        content: '',
                        createdAt: new Date().toISOString(),
                        toolName: currentToolCall.toolName,
                        toolInput: currentToolCall.toolInput,
                        toolOutput: eventData.output,
                        comparisonGroup,
                      })
                      currentToolCall = null
                    }
                    break
                  case 'todos':
                    if (eventData.todos) {
                      const { todos: previousTodos } = useChatStore.getState()
                      if (previousTodos.length === 0 && eventData.todos.length > 0) {
                        setPanelType('todos')
                        setPanelOpen(true)
                      }
                      setTodos(eventData.todos)
                    }
                    break
                  case 'files':
                    if (eventData.files) {
                      setFiles(eventData.files)
                    }
                    break
                  case 'done':
                    updateMessage(messageId, {
                      content: fullAssistantContent,
                      isStreaming: false,
                      thinkingContent: fullThinkingContent || undefined,
                      inputTokens: eventData.input_tokens,
                      outputTokens: eventData.output_tokens,
                      cacheReadTokens: eventData.cache_read_tokens,
                      cacheWriteTokens: eventData.cache_write_tokens,
                      suggestedFollowUps: eventData.suggested_follow_ups,
                      model: model,
                    })

                    if (eventData.artifacts && eventData.artifacts.length > 0) {
                      eventData.artifacts.forEach((artifact: any) => {
                        addArtifact({
                          id: artifact.id,
                          title: artifact.title,
                          content: artifact.content,
                          language: artifact.language,
                          version: artifact.version,
                          createdAt: artifact.created_at || new Date().toISOString(),
                          conversationId: convId,
                          artifact_type: artifact.artifact_type,
                        })
                      })
                      setPanelType('artifacts')
                      setPanelOpen(true)
                    }
                    break
                  case 'error':
                    console.error(`Stream error (${model}):`, eventData.error)
                    break
                }
              } catch (e) {
                console.warn('Failed to parse SSE data:', e)
              }
              currentEvent = null
              currentData = null
            } else if (currentData) {
              try {
                const eventData = JSON.parse(currentData)
                if (eventData.content) {
                  appendToMessage(messageId, eventData.content)
                  fullAssistantContent += eventData.content
                }
              } catch (e) {
                console.warn('Failed to parse SSE data:', e)
              }
              currentData = null
            }
          }
        }
      }

      // Mark message as complete
      updateMessage(messageId, {
        isStreaming: false,
        isThinking: false,
        model: model,
      })

      // Persist assistant message to backend
      try {
        await api.createMessage(convId, {
          content: fullAssistantContent,
          role: 'assistant',
          thinkingContent: fullThinkingContent || undefined,
          model: model,
        })
      } catch (e) {
        console.warn('Failed to persist assistant message:', e)
      }

      // Detect artifacts
      try {
        const detectedArtifacts = await detectArtifacts(fullAssistantContent, convId)
        if (detectedArtifacts.length > 0) {
          setPanelType('artifacts')
          setPanelOpen(true)
        }
      } catch (e) {
        console.warn('Failed to detect artifacts:', e)
      }

    } catch (error: unknown) {
      if (error instanceof Error && error.name === 'AbortError') {
        console.log(`Request cancelled for ${model}`)
      } else {
        console.error(`Error streaming from ${model}:`, error)
        updateMessage(messageId, {
          content: `Error: ${error instanceof Error ? error.message : String(error)}`,
          isStreaming: false,
          model: model,
        })
      }
    }
  }

  const handleSend = async () => {
    // If streaming, this is a stop request
    if (isStreaming) {
      abortControllerRef.current?.abort()
      setStreaming(false)
      setLoading(false)
      return
    }

    if ((!inputValue.trim() && images.length === 0) || isLoading) return

    // OFFLINE MODE: Queue actions instead of sending
    if (isOffline) {
      const userMessageId = uuidv4()
      const convId = currentConversationId || 'offline-placeholder'

      const userMessage = {
        id: userMessageId,
        conversationId: convId,
        role: 'user' as const,
        content: inputValue,
        createdAt: new Date().toISOString(),
      }

      addMessage(userMessage)

      queueAction({
        type: 'send_message',
        payload: {
          conversationId: convId,
          content: inputValue,
          images: images.map(img => img.file.name),
          timestamp: new Date().toISOString()
        }
      })

      addMessage({
        id: uuidv4(),
        conversationId: convId,
        role: 'system' as const,
        content: 'Message queued. Will be sent when connection is restored.',
        createdAt: new Date().toISOString(),
      })

      setInputValue('')
      setImages([])
      return
    }

    // Upload images first
    const uploadedImages: string[] = []
    for (const image of images) {
      try {
        const formData = new FormData()
        formData.append('file', image.file)
        const response = await fetch('/api/messages/upload-image', {
          method: 'POST',
          body: formData,
        })
        if (response.ok) {
          const data = await response.json()
          uploadedImages.push(data.url)
        }
      } catch (e) {
        console.error('Failed to upload image:', e)
      }
    }

    // Ensure we have a conversation ID
    let convId = currentConversationId
    if (!convId) {
      const newConv = await createConversation('New Conversation')
      convId = newConv.id
    }

    const userMessageId = uuidv4()
    const userMessage = {
      id: userMessageId,
      conversationId: convId,
      role: 'user' as const,
      content: inputValue,
      attachments: uploadedImages.length > 0 ? uploadedImages : undefined,
      createdAt: new Date().toISOString(),
    }

    addMessage(userMessage)
    const messageToSend = inputValue
    interruptedMessageRef.current = messageToSend
    setInputValue('')
    setImages([])
    setLoading(true)
    setStreaming(true)

    // Create abort controller for cancellation
    const abortController = new AbortController()
    abortControllerRef.current = abortController

    try {
      // Persist user message to backend
      try {
        await api.createMessage(convId, {
          content: messageToSend,
          role: 'user',
          attachments: uploadedImages.length > 0 ? uploadedImages : undefined
        })
      } catch (e) {
        console.warn('Failed to persist user message:', e)
      }

      if (comparisonMode && comparisonModels.length === 2) {
        // COMPARISON MODE: Stream from multiple models
        const comparisonGroup = `comparison-${Date.now()}`

        // Create placeholder messages for both models
        const messageIds: string[] = []
        for (const model of comparisonModels) {
          const assistantMessageId = uuidv4()
          messageIds.push(assistantMessageId)
          const assistantMessage = {
            id: assistantMessageId,
            conversationId: convId,
            role: 'assistant' as const,
            content: '',
            createdAt: new Date().toISOString(),
            isStreaming: true,
            model: model,
            comparisonGroup: comparisonGroup,
          }
          addMessage(assistantMessage)
        }

        // Stream from both models in parallel
        const streamPromises = comparisonModels.map((model, index) =>
          streamFromModel(
            model,
            messageToSend,
            convId,
            abortController,
            messageIds[index],
            comparisonGroup
          )
        )

        await Promise.all(streamPromises)

      } else {
        // SINGLE MODEL MODE: Original behavior
        const assistantMessageId = uuidv4()
        const assistantMessage = {
          id: assistantMessageId,
          conversationId: convId,
          role: 'assistant' as const,
          content: '',
          createdAt: new Date().toISOString(),
          isStreaming: true,
        }
        addMessage(assistantMessage)

        await streamFromModel(
          useUIStore.getState().selectedModel,
          messageToSend,
          convId,
          abortController,
          assistantMessageId
        )
      }

    } catch (error: unknown) {
      if (error instanceof Error && error.name === 'AbortError') {
        console.log('Request cancelled by user')
      } else {
        console.error('Error sending message:', error)
        const errorMsg = `Error: ${error instanceof Error ? error.message : String(error)}. The backend may not be running or API key not configured.`
        addMessage({
          id: uuidv4(),
          conversationId: convId,
          role: 'assistant',
          content: errorMsg,
          createdAt: new Date().toISOString(),
        })
        try {
          await api.createMessage(convId, { content: errorMsg, role: 'assistant' })
        } catch (e) {
          console.warn('Failed to persist error message:', e)
        }
      }
    } finally {
      setLoading(false)
      setStreaming(false)
      abortControllerRef.current = null
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleVoiceInput = () => {
    if (!isSpeechRecognitionSupported) {
      alert('Speech recognition is not supported in this browser.')
      return
    }

    if (!isListening) {
      // Start recording
      setIsListening(true)
      setIsRecording(true)
      setRecordingText('')
    } else {
      // Stop recording
      setIsListening(false)
      setIsRecording(false)
      setRecordingText('')
    }
  }

  const handleFileSelect = () => {
    fileInputRef.current?.click()
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (!files) return

    Array.from(files).forEach(file => {
      if (!file.type.startsWith('image/')) return

      const reader = new FileReader()
      reader.onload = (e) => {
        const preview = e.target?.result as string
        const newImage: ImageAttachment = {
          id: uuidv4(),
          url: '',
          file,
          preview,
        }
        setImages(prev => [...prev, newImage])
      }
      reader.readAsDataURL(file)
    })

    // Reset input value to allow selecting the same file again
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  const handlePaste = (e: React.ClipboardEvent) => {
    const items = e.clipboardData.items
    for (let i = 0; i < items.length; i++) {
      const item = items[i]
      if (item.type.startsWith('image/')) {
        e.preventDefault()
        const file = item.getAsFile()
        if (!file) continue

        const reader = new FileReader()
        reader.onload = (e) => {
          const preview = e.target?.result as string
          const newImage: ImageAttachment = {
            id: uuidv4(),
            url: '',
            file,
            preview,
          }
          setImages(prev => [...prev, newImage])
        }
        reader.readAsDataURL(file)
      }
    }
  }

  const removeImage = (id: string) => {
    setImages(prev => prev.filter(img => img.id !== id))
  }

  // Drag and drop handlers
  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.dataTransfer.items && e.dataTransfer.items.length > 0) {
      // Check if any item is a file
      const hasFiles = Array.from(e.dataTransfer.items).some(item => item.kind === 'file')
      if (hasFiles) {
        setIsDragOver(true)
      }
    }
  }

  const handleDragLeave = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragOver(false)
  }

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragOver(false)

    const files = e.dataTransfer.files
    if (!files || files.length === 0) return

    Array.from(files).forEach(file => {
      if (!file.type.startsWith('image/')) return

      const reader = new FileReader()
      reader.onload = (e) => {
        const preview = e.target?.result as string
        const newImage: ImageAttachment = {
          id: uuidv4(),
          url: '',
          file,
          preview,
        }
        setImages(prev => [...prev, newImage])
      }
      reader.readAsDataURL(file)
    })
  }

  // HITL Approval Dialog Handlers
  const handleHITLApproved = async () => {
    setHitlApproval(null)
    // Restore the interrupted message and resume
    const messageToResume = interruptedMessageRef.current
    if (messageToResume.trim()) {
      setInputValue(messageToResume)
      // Wait a tick for state to update, then send
      setTimeout(() => handleSend(), 0)
    }
  }

  const handleHITLRejected = () => {
    setHitlApproval(null)
    // Add a message indicating rejection
    const { addMessage } = useConversationStore.getState()
    addMessage({
      id: uuidv4(),
      conversationId: hitlApproval?.threadId || '',
      role: 'system',
      content: 'Tool execution was rejected by user.',
      createdAt: new Date().toISOString(),
    })
    // Clear the interrupted message ref
    interruptedMessageRef.current = ''
  }

  const handleHITLEdited = async (editedInput: any) => {
    // The backend handles the edit, now resume with the original message
    // (The edit was already sent to backend via api.handleInterrupt)
    setHitlApproval(null)
    const messageToResume = interruptedMessageRef.current
    if (messageToResume.trim()) {
      setInputValue(messageToResume)
      // Wait a tick for state to update, then send
      setTimeout(() => handleSend(), 0)
    }
  }

  return (
    <div
      data-tour="chat-input"
      className={`max-w-3xl mx-auto p-4 ${isDragOver ? 'bg-[var(--bg-secondary)]' : ''}`}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      {/* Drop zone indicator */}
      {isDragOver && (
        <div className="mb-3 p-4 border-2 border-dashed border-[var(--primary)] rounded-lg bg-[var(--bg-secondary)] text-[var(--primary)] text-center font-medium">
          Drop images here to attach
        </div>
      )}
      {/* Image previews */}
      {images.length > 0 && (
        <div className="mb-3 flex flex-wrap gap-2">
          {images.map((image) => (
            <div key={image.id} className="relative group">
              <img
                src={image.preview}
                alt="Attachment"
                className="h-20 w-20 object-cover rounded-lg border border-[var(--border-primary)]"
              />
              <button
                onClick={() => removeImage(image.id)}
                className="absolute -top-2 -right-2 bg-red-500 text-white rounded-full p-1 opacity-0 group-hover:opacity-100 transition-opacity"
                type="button"
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Offline mode indicator in input area */}
      {isOffline && (
        <div className="mb-3 p-3 bg-[var(--warning)]/10 border border-[var(--warning)] rounded-lg text-[var(--text-primary)] text-sm">
          <div className="font-medium mb-1">⚠️ Offline Mode</div>
          <div className="opacity-80">
            Messages will be queued and sent when connection is restored.
            {actionQueue.length > 0 && ` ${actionQueue.length} message${actionQueue.length > 1 ? 's' : ''} queued.`}
          </div>
        </div>
      )}

      <div className="flex items-end gap-3">
        {/* Voice input button */}
        <button
          onClick={handleVoiceInput}
          disabled={isLoading || isStreaming || isOffline}
          className={`p-3 rounded-lg transition-colors disabled:opacity-50 ${
            isRecording
              ? 'bg-red-500 text-white hover:bg-red-600'
              : 'text-[var(--text-secondary)] hover:text-[var(--primary)]'
          }`}
          type="button"
          title={isRecording ? "Stop recording" : isOffline ? "Voice input unavailable offline" : "Voice input (click to record)"}
        >
          {isRecording ? (
            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 animate-pulse" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <circle cx="12" cy="12" r="4" fill="currentColor" />
            </svg>
          ) : (
            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
            </svg>
          )}
        </button>

        {/* Attachment button */}
        <button
          onClick={handleFileSelect}
          disabled={isLoading || isStreaming || isOffline}
          className="p-3 text-[var(--text-secondary)] hover:text-[var(--primary)] transition-colors disabled:opacity-50"
          type="button"
          title={isOffline ? "Attachments unavailable offline" : "Attach image"}
        >
          <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
          </svg>
        </button>

        {/* Hidden file input */}
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          multiple
          onChange={handleFileChange}
          className="hidden"
        />

        <div className="flex-1 relative">
          <textarea
            ref={textareaRef}
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            onPaste={handlePaste}
            placeholder={isOffline ? "Type message to queue... (images not supported offline)" : "Type your message... (Paste images directly)"}
            disabled={isLoading || isStreaming}
            className={`w-full resize-none border border-[var(--border-primary)] rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-[var(--primary)] bg-[var(--bg-primary)] text-[var(--text-primary)] disabled:opacity-50 min-h-[60px] max-h-[200px] ${isDragOver ? 'ring-2 ring-[var(--primary)]' : ''}`}
            rows={1}
          />
        </div>
        <button
          onClick={handleSend}
          disabled={(!inputValue.trim() && images.length === 0) || isLoading}
          className={`px-6 py-3 bg-[var(--primary)] hover:bg-[var(--primary-hover)] text-white rounded-lg font-medium transition-smooth disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 ${isLoading ? 'loading' : ''}`}
          title={isOffline ? "Message will be queued" : "Send message"}
        >
          {isLoading ? (
            <>
              <span className="loading-spinner primary small"></span>
              <span>Sending...</span>
            </>
          ) : isStreaming ? 'Stop' : (isOffline ? 'Queue' : 'Send')}
        </button>
      </div>
      <div className="flex justify-between mt-2 text-xs text-[var(--text-secondary)]">
        <span>
          {getLiveTokenDisplay(inputValue)}
          {images.length > 0 && ` • ${images.length} image${images.length > 1 ? 's' : ''} attached`}
          {isOffline && images.length > 0 && ' (images will be lost)'}
        </span>
        <span>Enter to send, Shift+Enter for newline</span>
      </div>

      {/* Recording status indicator */}
      {isRecording && (
        <div className="mt-2 flex items-center gap-2 text-sm text-[var(--error)]">
          <div className="loading-dots">
            <span></span>
            <span></span>
            <span></span>
          </div>
          <span>Recording...</span>
          <span className="text-xs text-[var(--text-secondary)]">Click microphone to stop</span>
        </div>
      )}

      {/* HITL Approval Dialog */}
      {hitlApproval && (
        <HITLApprovalDialog
          threadId={hitlApproval.threadId}
          tool={hitlApproval.tool}
          input={hitlApproval.input}
          reason={hitlApproval.reason}
          onApproved={handleHITLApproved}
          onRejected={handleHITLRejected}
          onEdited={handleHITLEdited}
        />
      )}
    </div>
  )
}
