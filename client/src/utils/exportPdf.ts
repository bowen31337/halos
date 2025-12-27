/**
 * PDF Export Utility
 * Handles exporting conversations to PDF format using html2pdf.js
 */

interface Message {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  created_at: string
  attachments?: string[]
}

interface ConversationData {
  title: string
  model: string
  created_at: string
  messages: Message[]
}

declare global {
  interface Window {
    html2pdf: any
  }
}

/**
 * Generate HTML for PDF export
 */
function generatePDFHTML(data: ConversationData): string {
  const { title, model, created_at, messages } = data

  const formatDate = new Date(created_at).toLocaleString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })

  let messagesHTML = messages.map((msg) => {
    const roleLabel = msg.role === 'user' ? 'You' : msg.role === 'assistant' ? 'Claude' : 'System'
    const roleColor = msg.role === 'user' ? '#2563eb' : msg.role === 'assistant' ? '#059669' : '#6b7280'

    // Simple markdown-like formatting for PDF
    let formattedContent = msg.content
      // Code blocks
      .replace(/```(\w+)?\n([\s\S]*?)```/g, '<pre style="background:#f3f4f6;padding:12px;border-radius:4px;font-family:monospace;font-size:12px;overflow-x:auto;"><code>$2</code></pre>')
      // Inline code
      .replace(/`([^`]+)`/g, '<code style="background:#f3f4f6;padding:2px 6px;border-radius:3px;font-family:monospace;font-size:13px;">$1</code>')
      // Bold
      .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
      // Italic
      .replace(/\*([^*]+)\*/g, '<em>$1</em>')
      // Line breaks
      .replace(/\n/g, '<br>')

    return `
      <div style="margin-bottom: 24px;">
        <div style="display: flex; align-items: center; margin-bottom: 8px;">
          <span style="font-weight: 600; color: ${roleColor}; font-size: 14px;">${roleLabel}</span>
          <span style="color: #9ca3af; margin: 0 8px; font-size: 12px;">•</span>
          <span style="color: #6b7280; font-size: 12px;">${new Date(msg.created_at).toLocaleString()}</span>
        </div>
        <div style="padding-left: 16px; border-left: 3px solid ${roleColor};">
          <div style="color: #1f2937; line-height: 1.6; font-size: 13px;">${formattedContent}</div>
          ${msg.attachments && msg.attachments.length > 0 ? `
            <div style="margin-top: 8px;">
              ${msg.attachments.map(url => `<div style="color: #2563eb; font-size: 12px;">📎 Image: ${url}</div>`).join('')}
            </div>
          ` : ''}
        </div>
      </div>
    `
  }).join('\n')

  return `
    <div style="font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 800px; margin: 0 auto; padding: 40px 20px;">
      <div style="border-bottom: 2px solid #e5e7eb; padding-bottom: 20px; margin-bottom: 30px;">
        <h1 style="color: #111827; font-size: 28px; margin: 0 0 12px 0;">${title}</h1>
        <div style="color: #6b7280; font-size: 14px;">
          <div><strong>Model:</strong> ${model}</div>
          <div><strong>Date:</strong> ${formatDate}</div>
        </div>
      </div>

      ${messagesHTML}

      <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #e5e7eb; text-align: center; color: #9ca3af; font-size: 12px;">
        Exported from Claude.ai Clone • ${new Date().toLocaleString()}
      </div>
    </div>
  `
}

/**
 * Export conversation to PDF
 */
export async function exportToPDF(
  data: ConversationData,
  filename?: string
): Promise<void> {
  // Check if html2pdf is loaded
  if (!window.html2pdf) {
    throw new Error('html2pdf.js library not loaded')
  }

  // Generate filename
  const safeTitle = data.title.replace(/[^a-z0-9]/gi, '_').toLowerCase()
  const defaultFilename = `${safeTitle}_export.pdf`
  const finalFilename = filename || defaultFilename

  // Generate HTML content
  const htmlContent = generatePDFHTML(data)

  // Configure PDF options
  const opt = {
    margin: [15, 15, 15, 15], // top, left, bottom, right (in mm)
    filename: finalFilename,
    image: { type: 'jpeg', quality: 0.95 },
    html2canvas: {
      scale: 2, // Higher scale for better quality
      useCORS: true,
      letterRendering: true,
    },
    jsPDF: {
      unit: 'mm',
      format: 'a4',
      orientation: 'portrait',
    },
    pagebreak: { mode: ['avoid-all', 'css', 'legacy'] },
  }

  try {
    // Create a temporary container for the HTML
    const container = document.createElement('div')
    container.style.position = 'absolute'
    container.style.left = '-9999px'
    container.innerHTML = htmlContent
    document.body.appendChild(container)

    // Generate and download PDF
    await window.html2pdf().set(opt).from(container).save()

    // Clean up
    document.body.removeChild(container)
  } catch (error) {
    console.error('PDF export failed:', error)
    throw new Error('Failed to generate PDF')
  }
}

/**
 * Export current conversation from page
 */
export async function exportCurrentConversation(): Promise<void> {
  // This will be implemented to get conversation data from the store
  // For now, it's a placeholder that will be connected to the actual store
  throw new Error('Not implemented - use exportToPDF with conversation data')
}

export default exportToPDF
