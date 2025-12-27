import { useState, useRef, useEffect } from 'react'
import { useConversationStore } from '../stores/conversationStore'
import { useUIStore } from '../stores/uiStore'
import { useProjectStore } from '../stores/projectStore'
import { useArtifactStore } from '../stores/artifactStore'
import { useChatStore } from '../stores/chatStore'
import { api } from '../services/api'
import { v4 as uuidv4 } from 'uuid'
import { HITLApprovalDialog } from './HITLApprovalDialog'

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
    setPanelOpen,
    setPanelType
  } = useUIStore()

  const { detectArtifacts } = useArtifactStore()

  // Use local state for immediate UI feedback, sync with store
  const [inputValue, setInputValue] = useState(storeInputMessage)
  const [images, setImages] = useState<ImageAttachment[]>([])
  const [isDragOver, setIsDragOver] = useState(false)
  const [hitlApproval, setHitlApproval] = useState<HITLPendingApproval | null>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const abortControllerRef = useRef<AbortController | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

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

  const handleSend = async () => {
    // If streaming, this is a stop request
    if (isStreaming) {
      abortControllerRef.current?.abort()
      setStreaming(false)
      setLoading(false)
      return
    }

    if ((!inputValue.trim() && images.length === 0) || isLoading) return

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
      // Create a new conversation
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
    setInputValue('')
    setImages([]) // Clear images after sending
    setLoading(true)
    setStreaming(true)

    // Create assistant message placeholder for streaming
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

    // Create abort controller for cancellation
    const abortController = new AbortController()
    abortControllerRef.current = abortController

    try {
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
      let finalMessage = messageToSend
      if (effectiveInstructions.trim()) {
        finalMessage = `[System Instructions: ${effectiveInstructions}]\n\n${messageToSend}`
      }

      // Call the backend SSE API with conversation ID
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
          model: useUIStore.getState().selectedModel,
          permission_mode: permissionMode,
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
      let fullAssistantContent = ''
      let fullThinkingContent = ''
      let currentToolCall: { toolName: string; toolInput: Record<string, unknown> } | null = null

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || '' // Keep incomplete line in buffer

        // SSE events can span multiple lines: event: X \n data: Y \n\n
        // We need to buffer event and data lines together
        let currentEvent: string | null = null
        let currentData: string | null = null

        for (const line of lines) {
          const trimmed = line.trim()

          if (trimmed.startsWith('event:')) {
            currentEvent = trimmed.slice(6).trim()
          } else if (trimmed.startsWith('data:')) {
            currentData = trimmed.slice(5).trim()
          } else if (trimmed === '') {
            // Empty line indicates end of event, process what we have
            if (currentEvent && currentData) {
              try {
                const eventData = JSON.parse(currentData)

                switch (currentEvent) {
                  case 'message':
                    if (eventData.content) {
                      appendToLastMessage(eventData.content)
                      fullAssistantContent += eventData.content
                    }
                    break
                  case 'thinking':
                    // Handle thinking events
                    if (eventData.status === 'thinking') {
                      // Show thinking indicator
                      const { messages } = useConversationStore.getState()
                      const currentIndex = messages.findIndex(m => m.id === assistantMessageId)
                      if (currentIndex >= 0) {
                        const updatedMessages = [...messages]
                        updatedMessages[currentIndex] = {
                          ...updatedMessages[currentIndex],
                          isThinking: true
                        }
                        useConversationStore.setState({ messages: updatedMessages })
                      }
                    }
                    if (eventData.content) {
                      fullThinkingContent += eventData.content
                      // Update thinking content in real-time with isThinking flag
                      const { messages } = useConversationStore.getState()
                      const currentIndex = messages.findIndex(m => m.id === assistantMessageId)
                      if (currentIndex >= 0) {
                        const updatedMessages = [...messages]
                        updatedMessages[currentIndex] = {
                          ...updatedMessages[currentIndex],
                          thinkingContent: fullThinkingContent,
                          isThinking: true
                        }
                        useConversationStore.setState({ messages: updatedMessages })
                      }
                    }
                    break
                  case 'tool_start':
                    // Store tool call info for when it completes
                    currentToolCall = {
                      toolName: eventData.tool,
                      toolInput: eventData.input,
                    }
                    break
                  case 'tool_end':
                    // Create a tool message when tool completes
                    if (currentToolCall) {
                      const { addMessage } = useConversationStore.getState()
                      addMessage({
                        id: `tool-${Date.now()}`,
                        conversationId: convId,
                        role: 'tool',
                        content: '',
                        createdAt: new Date().toISOString(),
                        toolName: currentToolCall.toolName,
                        toolInput: currentToolCall.toolInput,
                        toolOutput: eventData.output,
                      })
                      currentToolCall = null
                    }
                    break
                  case 'todos':
                    // Handle todos update from agent
                    if (eventData.todos) {
                      const { setTodos, todos } = useChatStore.getState()
                      const previousTodos = todos
                      setTodos(eventData.todos)
                      // Auto-open todo panel if this is the first time todos are set
                      if (previousTodos.length === 0 && eventData.todos.length > 0) {
                        const { setPanelType, setPanelOpen } = useUIStore.getState()
                        setPanelType('todos')
                        setPanelOpen(true)
                      }
                    }
                    break
                  case 'files':
                    // Handle files update from agent
                    if (eventData.files) {
                      const { setFiles, files } = useChatStore.getState()
                      const previousFiles = files
                      setFiles(eventData.files)
                      // Auto-open files panel if this is the first time files are set
                      if (previousFiles.length === 0 && eventData.files.length > 0) {
                        const { setPanelType, setPanelOpen } = useUIStore.getState()
                        setPanelType('files')
                        setPanelOpen(true)
                      }
                    }
                    break
                  case 'interrupt':
                    // Handle HITL interrupt - show approval dialog
                    if (eventData.tool && eventData.input) {
                      setHitlApproval({
                        threadId: convId,
                        tool: eventData.tool,
                        input: eventData.input,
                        reason: eventData.reason || 'Tool execution requires approval',
                      })
                      // Mark streaming as stopped since we're waiting for approval
                      setStreaming(false)
                    }
                    break
                  case 'done':
                    console.log('Stream completed')
                    // Store thinking content if present
                    if (eventData.thinking_content) {
                      fullThinkingContent = eventData.thinking_content
                    }
                    // Handle artifacts created by backend
                    if (eventData.artifacts && eventData.artifacts.length > 0) {
                      // Add artifacts to the store
                      const { addArtifact } = useArtifactStore.getState()
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
                      // Open the artifact panel
                      const { setPanelType } = useUIStore.getState()
                      setPanelType('artifacts')
                    }
                    // Handle todos from done event (fallback if no todos event was emitted)
                    if (eventData.todos) {
                      const { setTodos } = useChatStore.getState()
                      setTodos(eventData.todos)
                    }
                    // Handle files from done event (fallback if no files event was emitted)
                    if (eventData.files) {
                      const { setFiles } = useChatStore.getState()
                      setFiles(eventData.files)
                    }
                    break
                  case 'error':
                    console.error('Stream error:', eventData.error)
                    break
                  case 'start':
                    // Start event - could be used for initialization
                    break
                }
              } catch (e) {
                console.warn('Failed to parse SSE data:', e)
              }

              // Reset for next event
              currentEvent = null
              currentData = null
            } else if (currentData) {
              // Handle data-only lines (fallback for non-standard format)
              try {
                const eventData = JSON.parse(currentData)
                if (eventData.content) {
                  appendToLastMessage(eventData.content)
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

      // Mark message as no longer streaming
      const { messages } = useConversationStore.getState()
      const currentIndex = messages.findIndex(m => m.id === assistantMessageId)
      if (currentIndex >= 0) {
        const updatedMessages = [...messages]
        updatedMessages[currentIndex] = {
          ...updatedMessages[currentIndex],
          isStreaming: false,
          isThinking: false,
          thinkingContent: fullThinkingContent || undefined
        }
        useConversationStore.setState({ messages: updatedMessages })
      }

      // Persist assistant message to backend
      try {
        await api.createMessage(convId, {
          content: fullAssistantContent,
          role: 'assistant',
          thinkingContent: fullThinkingContent || undefined
        })
      } catch (e) {
        console.warn('Failed to persist assistant message:', e)
      }

      // Detect artifacts in the assistant response
      try {
        const detectedArtifacts = await detectArtifacts(fullAssistantContent, convId)
        if (detectedArtifacts.length > 0) {
          // Auto-open the artifacts panel
          setPanelType('artifacts')
          setPanelOpen(true)
          console.log(`Detected ${detectedArtifacts.length} artifact(s)`)
        }
      } catch (e) {
        console.warn('Failed to detect artifacts:', e)
      }

    } catch (error: unknown) {
      if (error instanceof Error && error.name === 'AbortError') {
        console.log('Request cancelled by user')
      } else {
        console.error('Error sending message:', error)
        // Add error message
        const errorMsg = `Error: ${error instanceof Error ? error.message : String(error)}. The backend may not be running or API key not configured.`
        addMessage({
          id: uuidv4(),
          conversationId: convId,
          role: 'assistant',
          content: errorMsg,
          createdAt: new Date().toISOString(),
        })
        // Persist error message
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
    // Resume the conversation by re-sending the original message
    if (inputValue.trim()) {
      await handleSend()
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
  }

  const handleHITLEdited = async (editedInput: any) => {
    // The backend handles the edit, now resume
    setHitlApproval(null)
    if (inputValue.trim()) {
      await handleSend()
    }
  }

  return (
    <div
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

      <div className="flex items-end gap-3">
        {/* Attachment button */}
        <button
          onClick={handleFileSelect}
          disabled={isLoading || isStreaming}
          className="p-3 text-[var(--text-secondary)] hover:text-[var(--primary)] transition-colors disabled:opacity-50"
          type="button"
          title="Attach image"
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
            placeholder="Type your message... (Paste images directly)"
            disabled={isLoading || isStreaming}
            className={`w-full resize-none border border-[var(--border-primary)] rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-[var(--primary)] bg-[var(--bg-primary)] text-[var(--text-primary)] disabled:opacity-50 min-h-[60px] max-h-[200px] ${isDragOver ? 'ring-2 ring-[var(--primary)]' : ''}`}
            rows={1}
          />
        </div>
        <button
          onClick={handleSend}
          disabled={(!inputValue.trim() && images.length === 0) || isLoading}
          className="px-6 py-3 bg-[var(--primary)] hover:bg-[var(--primary-hover)] text-white rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isStreaming ? 'Stop' : 'Send'}
        </button>
      </div>
      <div className="flex justify-between mt-2 text-xs text-[var(--text-secondary)]">
        <span>{inputValue.length} characters {images.length > 0 && `• ${images.length} image${images.length > 1 ? 's' : ''} attached`}</span>
        <span>Enter to send, Shift+Enter for newline</span>
      </div>

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
