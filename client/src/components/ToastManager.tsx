import { useState, useEffect, useCallback } from 'react'
import { create } from 'zustand'

// Toast types
export type ToastType = 'success' | 'error' | 'warning' | 'info'

export interface Toast {
  id: string
  type: ToastType
  title: string
  message?: string
  duration?: number
  createdAt: number
}

interface ToastStore {
  toasts: Toast[]
  addToast: (toast: Omit<Toast, 'id' | 'createdAt'>) => void
  removeToast: (id: string) => void
  clearToasts: () => void
}

// Toast store using Zustand
export const useToastStore = create<ToastStore>((set) => ({
  toasts: [],
  addToast: (toast) =>
    set((state) => ({
      toasts: [
        ...state.toasts,
        {
          ...toast,
          id: `${Date.now()}-${Math.random()}`,
          createdAt: Date.now(),
        },
      ],
    })),
  removeToast: (id) =>
    set((state) => ({
      toasts: state.toasts.filter((t) => t.id !== id),
    })),
  clearToasts: () => set({ toasts: [] }),
}))

// Toast icon component
const ToastIcon = ({ type }: { type: ToastType }) => {
  const icons = {
    success: (
      <svg className="toast-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
      </svg>
    ),
    error: (
      <svg className="toast-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
      </svg>
    ),
    warning: (
      <svg className="toast-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
      </svg>
    ),
    info: (
      <svg className="toast-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
  }
  return icons[type]
}

// Toast component
const ToastItem = ({ toast, onClose }: { toast: Toast; onClose: (id: string) => void }) => {
  const [isDismissing, setIsDismissing] = useState(false)

  useEffect(() => {
    const duration = toast.duration ?? 3000
    if (duration > 0) {
      const timer = setTimeout(() => {
        setIsDismissing(true)
        setTimeout(() => onClose(toast.id), 200)
      }, duration)
      return () => clearTimeout(timer)
    }
  }, [toast, onClose])

  const handleClose = useCallback(() => {
    setIsDismissing(true)
    setTimeout(() => onClose(toast.id), 200)
  }, [toast.id, onClose])

  return (
    <div
      className={`toast ${toast.type} ${isDismissing ? 'dismissing' : ''}`}
      role="alert"
      aria-live="polite"
    >
      <ToastIcon type={toast.type} />
      <div className="toast-content">
        <div className="toast-title">{toast.title}</div>
        {toast.message && <div className="toast-message">{toast.message}</div>}
      </div>
      <button className="toast-close" onClick={handleClose} aria-label="Close notification">
        <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
      <div className="toast-progress" />
    </div>
  )
}

// Toast container component
export function ToastManager() {
  const { toasts, removeToast } = useToastStore()

  if (toasts.length === 0) return null

  return (
    <div className="toast-container">
      {toasts.map((toast) => (
        <ToastItem key={toast.id} toast={toast} onClose={removeToast} />
      ))}
    </div>
  )
}

// Hook for showing toasts
export function useToast() {
  const addToast = useToastStore((state) => state.addToast)

  const showSuccess = useCallback(
    (title: string, message?: string) => {
      addToast({ type: 'success', title, message, duration: 3000 })
    },
    [addToast]
  )

  const showError = useCallback(
    (title: string, message?: string) => {
      addToast({ type: 'error', title, message, duration: 5000 })
    },
    [addToast]
  )

  const showWarning = useCallback(
    (title: string, message?: string) => {
      addToast({ type: 'warning', title, message, duration: 4000 })
    },
    [addToast]
  )

  const showInfo = useCallback(
    (title: string, message?: string) => {
      addToast({ type: 'info', title, message, duration: 3000 })
    },
    [addToast]
  )

  return { showSuccess, showError, showWarning, showInfo, addToast }
}
